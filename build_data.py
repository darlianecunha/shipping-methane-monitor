#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_data.py
Aggregates verified CH4, N2O and CO2eq emissions from the EU MRV 2024
public dataset (EMSA / THETIS-MRV) into data.json for the static site.

Source file expected at ../Brazil_Vessel_Call_Intelligence/europe/*MRV*.xlsx
(or pass a path as the first argument).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
if len(sys.argv) > 1:
    MRV_XLSX = Path(sys.argv[1])
else:
    MRV_XLSX = next((HERE.parent / "Brazil_Vessel_Call_Intelligence" / "europe").glob("*MRV*"))

GWP_CH4, GWP_N2O = 28, 265   # IPCC AR5, as used by the EU MRV/ETS (verified empirically)

df = pd.read_excel(MRV_XLSX, sheet_name="2024 Full ERs", skiprows=2)
df.columns = [str(c) for c in df.columns]

def col(prefix, berth=False):
    return [x for x in df.columns
            if x.startswith(prefix) and (("at berth" in x) == berth)][0]

def ets_col(gas):
    return [x for x in df.columns
            if x.startswith(f"{gas} emissions to be reported under Directive 2003/87/EC")][0]

d = pd.DataFrame({
    "type": df["Ship type"],
    "company": df["Name.1"],   # DoC holder (second Name column in the file)
    "fuel": pd.to_numeric(df["Total fuel consumption [m tonnes]"], errors="coerce"),
    "co2": pd.to_numeric(df["Total CO₂ emissions [m tonnes]"], errors="coerce"),
    "co2b": pd.to_numeric(df[col("CO₂ emissions which occurred", True)], errors="coerce"),
    "ch4": pd.to_numeric(df["Total CH₄ emissions [m tonnes]"], errors="coerce"),
    "ch4b": pd.to_numeric(df[col("CH₄ emissions which occurred", True)], errors="coerce"),
    "n2o": pd.to_numeric(df["Total N₂O emissions [m tonnes]"], errors="coerce"),
    "n2ob": pd.to_numeric(df[col("N₂O emissions which occurred", True)], errors="coerce"),
    "co2eq": pd.to_numeric(df["Total CO₂eq emissions [m tonnes]"], errors="coerce"),
    "ets_ch4": pd.to_numeric(df[ets_col("CH₄")], errors="coerce"),
    "ets_n2o": pd.to_numeric(df[ets_col("N₂O")], errors="coerce"),
})

by_type = []
for t, g in d.groupby("type"):
    if len(g) < 20 or not isinstance(t, str):
        continue
    co2, co2eq = g["co2"].sum(), g["co2eq"].sum()
    by_type.append({
        "type": t,
        "n": int(len(g)),
        "ch4_t": round(float(g["ch4"].sum()), 1),
        "n2o_t": round(float(g["n2o"].sum()), 1),
        "ch4_berth_t": round(float(g["ch4b"].sum()), 1),
        "co2_mt": round(float(co2) / 1e6, 3),
        "co2eq_mt": round(float(co2eq) / 1e6, 3),
        "uplift_pct": round(float(co2eq / co2 - 1) * 100, 2) if co2 else None,
    })
by_type.sort(key=lambda x: -x["ch4_t"])

ch4_total = float(d["ch4"].sum())
n2o_total = float(d["n2o"].sum())
lng = d[d["type"] == "LNG carrier"]

# ---- Module 1: who owns the methane (DoC holder ranking) ----------------
PASSENGER = {"Passenger ship", "Passenger ship (Cruise Passenger ship)",
             "Ro-pax ship", "Cruise ship"}
companies = []
for name, g in d.dropna(subset=["company"]).groupby("company"):
    ch4 = float(g["ch4"].sum())
    if ch4 <= 0:
        continue
    main = g.groupby("type")["ch4"].sum().idxmax()
    companies.append({
        "name": str(name).strip(),
        "vessels": int(len(g)),
        "ch4_t": round(ch4, 1),
        "share_pct": round(ch4 / ch4_total * 100, 1),
        "main_type": main,
        "segment": ("lng" if main == "LNG carrier"
                    else "passenger" if main in PASSENGER else "other"),
    })
companies.sort(key=lambda x: -x["ch4_t"])
top15 = companies[:15]
top10_share = round(sum(c["ch4_t"] for c in companies[:10]) / ch4_total * 100, 1)

# ---- Module 2: methane-slip fingerprint (LNG carriers) ------------------
li = lng[(lng["fuel"] > 0) & lng["ch4"].notna()].copy()
li["kg_per_t"] = li["ch4"] / li["fuel"] * 1000   # kg CH4 per tonne of fuel
BIN_W, BIN_MAX = 2, 32
counts = [0] * (BIN_MAX // BIN_W)
for v in li["kg_per_t"].clip(upper=BIN_MAX - 0.001):
    counts[int(v // BIN_W)] += 1
slip = {
    "vessels": int(len(li)),
    "bin_width": BIN_W,
    "bin_max": BIN_MAX,
    "counts": counts,
    "median": round(float(li["kg_per_t"].median()), 1),
    "p25": round(float(li["kg_per_t"].quantile(.25)), 2),
    "p75": round(float(li["kg_per_t"].quantile(.75)), 1),
    "share_low_pct": round(float((li["kg_per_t"] < 5).mean()) * 100, 1),
    "share_high_pct": round(float((li["kg_per_t"] >= 25).mean()) * 100, 1),
    # reference values in kg CH4 / t fuel (slip % x 10)
    "refs": [
        {"kg": 2,  "label": "0.2% EU default · high-pressure diesel 2-stroke"},
        {"kg": 17, "label": "1.7% EU default · LNG Otto 2-stroke"},
        {"kg": 31, "label": "3.1% EU default · LNG Otto 4-stroke"},
    ],
    "fumes_kg": 64,   # ICCT FUMES real-world average, LPDF 4-stroke: 6.4%
}

# ---- Module 3: the 2026 ETS methane bill --------------------------------
ETS_PRICE = 80   # EUR per EUA, reference value (same as shipping-carbon-costs)
ets_ch4_t = float(d["ets_ch4"].sum())
ets_n2o_t = float(d["ets_n2o"].sum())
ets_co2eq_mt = (ets_ch4_t * GWP_CH4 + ets_n2o_t * GWP_N2O) / 1e6
ets2026 = {
    "price_eur": ETS_PRICE,
    "ch4_t": round(ets_ch4_t),
    "n2o_t": round(ets_n2o_t),
    "co2eq_mt": round(ets_co2eq_mt, 2),
    "cost_meur": round(ets_co2eq_mt * ETS_PRICE, 1),
    "lng_share_pct": round(float(lng["ets_ch4"].sum()) * GWP_CH4
                           / (ets_co2eq_mt * 1e6) * 100, 1),
}

payload = {
    "meta": {
        "source": "EU MRV 2024 (EMSA / THETIS-MRV), Full emission reports",
        "source_version": MRV_XLSX.name,
        "gwp": {"ch4": GWP_CH4, "n2o": GWP_N2O, "basis": "IPCC AR5"},
        "generated": pd.Timestamp.today().strftime("%Y-%m-%d"),
    },
    "totals": {
        "vessels": int(len(d)),
        "vessels_reporting_ch4": int((d["ch4"] > 0).sum()),
        "ch4_t": round(ch4_total, 1),
        "n2o_t": round(n2o_total, 1),
        "co2_mt": round(float(d["co2"].sum()) / 1e6, 2),
        "co2eq_mt": round(float(d["co2eq"].sum()) / 1e6, 2),
        "uplift_pct": round(float(d["co2eq"].sum() / d["co2"].sum() - 1) * 100, 2),
        "ch4_co2eq_mt": round(ch4_total * GWP_CH4 / 1e6, 2),
        "n2o_co2eq_mt": round(n2o_total * GWP_N2O / 1e6, 2),
    },
    "lng": {
        "vessels": int(len(lng)),
        "ch4_t": round(float(lng["ch4"].sum()), 1),
        "share_of_fleet_ch4_pct": round(float(lng["ch4"].sum()) / ch4_total * 100, 1),
        "uplift_pct": round(float(lng["co2eq"].sum() / lng["co2"].sum() - 1) * 100, 1),
    },
    "at_berth": {
        "ch4_t": round(float(d["ch4b"].sum()), 1),
        "n2o_t": round(float(d["n2ob"].sum()), 1),
        "co2_mt": round(float(d["co2b"].sum()) / 1e6, 2),
        "vessels_with_ch4": int((d["ch4b"] > 0).sum()),
    },
    "by_type": by_type,
    "companies": {"top": top15, "n_companies": len(companies),
                  "top10_share_pct": top10_share},
    "slip": slip,
    "ets2026": ets2026,
}

(HERE / "data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                encoding="utf-8")
print(f"data.json written | vessels {payload['totals']['vessels']} | "
      f"CH4 {payload['totals']['ch4_t']:,} t | uplift {payload['totals']['uplift_pct']}%")
