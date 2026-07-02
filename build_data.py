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

d = pd.DataFrame({
    "type": df["Ship type"],
    "co2": pd.to_numeric(df["Total CO₂ emissions [m tonnes]"], errors="coerce"),
    "co2b": pd.to_numeric(df[col("CO₂ emissions which occurred", True)], errors="coerce"),
    "ch4": pd.to_numeric(df["Total CH₄ emissions [m tonnes]"], errors="coerce"),
    "ch4b": pd.to_numeric(df[col("CH₄ emissions which occurred", True)], errors="coerce"),
    "n2o": pd.to_numeric(df["Total N₂O emissions [m tonnes]"], errors="coerce"),
    "n2ob": pd.to_numeric(df[col("N₂O emissions which occurred", True)], errors="coerce"),
    "co2eq": pd.to_numeric(df["Total CO₂eq emissions [m tonnes]"], errors="coerce"),
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
}

(HERE / "data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                encoding="utf-8")
print(f"data.json written | vessels {payload['totals']['vessels']} | "
      f"CH4 {payload['totals']['ch4_t']:,} t | uplift {payload['totals']['uplift_pct']}%")
