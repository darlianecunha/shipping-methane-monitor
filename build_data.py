#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_data.py  (v2 - two reporting years)
Aggregates verified CH4, N2O and CO2eq emissions from the EU MRV public
datasets (EMSA / THETIS-MRV), reporting years 2024 and 2025, into data.json.

Sources expected at ../dados-europa/mrv_annual/mrv_{2024,2025}.xlsx
(or pass two paths: build_data.py <2024.xlsx> <2025.xlsx>).
Download: THETIS-MRV public API,
/api/public-emission-report/reporting-period-document/binary/{year}/{version}

A slim per-year cache (.cache_{year}.parquet) makes re-runs fast.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
DEFAULT_DIR = HERE.parent / "dados-europa" / "mrv_annual"
GWP_CH4, GWP_N2O = 28, 265        # IPCC AR5, as used by the EU MRV/ETS
ETS_PRICE = 80                    # EUR per EUA, reference value
YEARS = (2024, 2025)

PASSENGER = {"Passenger ship", "Passenger ship (Cruise Passenger ship)",
             "Ro-pax ship", "Cruise ship"}


def load(year: int, path: Path) -> pd.DataFrame:
    cache = HERE / f".cache_{year}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    df = pd.read_excel(path, sheet_name=f"{year} Full ERs", skiprows=2)
    df.columns = [str(c) for c in df.columns]

    def col(prefix, berth=False):
        return [x for x in df.columns
                if x.startswith(prefix) and (("at berth" in x) == berth)][0]

    slim = pd.DataFrame({
        "imo": pd.to_numeric(df["IMO Number"], errors="coerce").astype("Int64"),
        "type": df["Ship type"],
        "company": df["Name.1"],
        "fuel": pd.to_numeric(df["Total fuel consumption [m tonnes]"], errors="coerce"),
        "co2": pd.to_numeric(df["Total CO₂ emissions [m tonnes]"], errors="coerce"),
        "co2b": pd.to_numeric(df[col("CO₂ emissions which occurred", True)], errors="coerce"),
        "ch4": pd.to_numeric(df["Total CH₄ emissions [m tonnes]"], errors="coerce"),
        "ch4b": pd.to_numeric(df[col("CH₄ emissions which occurred", True)], errors="coerce"),
        "n2o": pd.to_numeric(df["Total N₂O emissions [m tonnes]"], errors="coerce"),
        "n2ob": pd.to_numeric(df[col("N₂O emissions which occurred", True)], errors="coerce"),
        "co2eq": pd.to_numeric(df["Total CO₂eq emissions [m tonnes]"], errors="coerce"),
        "ets_ch4": pd.to_numeric(df[col("CH₄ emissions to be reported under Directive")], errors="coerce"),
        "ets_n2o": pd.to_numeric(df[col("N₂O emissions to be reported under Directive")], errors="coerce"),
    }).dropna(subset=["imo"]).drop_duplicates(subset=["imo"], keep="first")
    slim.to_parquet(cache, index=False)
    return slim


def aggregate(d: pd.DataFrame) -> dict:
    ch4_total = float(d["ch4"].sum())
    n2o_total = float(d["n2o"].sum())
    lng = d[d["type"] == "LNG carrier"]

    by_type = []
    for t, g in d.groupby("type"):
        if len(g) < 20 or not isinstance(t, str):
            continue
        co2, co2eq = g["co2"].sum(), g["co2eq"].sum()
        by_type.append({
            "type": t, "n": int(len(g)),
            "ch4_t": round(float(g["ch4"].sum()), 1),
            "n2o_t": round(float(g["n2o"].sum()), 1),
            "ch4_berth_t": round(float(g["ch4b"].sum()), 1),
            "co2_mt": round(float(co2) / 1e6, 3),
            "co2eq_mt": round(float(co2eq) / 1e6, 3),
            "uplift_pct": round(float(co2eq / co2 - 1) * 100, 2) if co2 else None,
        })
    by_type.sort(key=lambda x: -x["ch4_t"])

    companies = []
    for name, g in d.dropna(subset=["company"]).groupby("company"):
        ch4 = float(g["ch4"].sum())
        if ch4 <= 0:
            continue
        main = g.groupby("type")["ch4"].sum().idxmax()
        companies.append({
            "name": str(name).strip(), "vessels": int(len(g)),
            "ch4_t": round(ch4, 1),
            "share_pct": round(ch4 / ch4_total * 100, 1),
            "main_type": main,
            "segment": ("lng" if main == "LNG carrier"
                        else "passenger" if main in PASSENGER else "other"),
        })
    companies.sort(key=lambda x: -x["ch4_t"])

    li = lng[(lng["fuel"] > 0) & lng["ch4"].notna()].copy()
    li["kg_per_t"] = li["ch4"] / li["fuel"] * 1000
    BIN_W, BIN_MAX = 2, 32
    counts = [0] * (BIN_MAX // BIN_W)
    for v in li["kg_per_t"].clip(upper=BIN_MAX - 0.001):
        counts[int(v // BIN_W)] += 1

    ets_ch4_t = float(d["ets_ch4"].sum())
    ets_n2o_t = float(d["ets_n2o"].sum())
    ets_co2eq_mt = (ets_ch4_t * GWP_CH4 + ets_n2o_t * GWP_N2O) / 1e6

    return {
        "totals": {
            "vessels": int(len(d)),
            "vessels_reporting_ch4": int((d["ch4"] > 0).sum()),
            "ch4_t": round(ch4_total, 1), "n2o_t": round(n2o_total, 1),
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
        "companies": {"top": companies[:15], "n_companies": len(companies),
                      "top10_share_pct": round(sum(c["ch4_t"] for c in companies[:10])
                                               / ch4_total * 100, 1)},
        "slip": {
            "vessels": int(len(li)), "bin_width": BIN_W, "bin_max": BIN_MAX,
            "counts": counts,
            "median": round(float(li["kg_per_t"].median()), 1),
            "p25": round(float(li["kg_per_t"].quantile(.25)), 2),
            "p75": round(float(li["kg_per_t"].quantile(.75)), 1),
            "share_low_pct": round(float((li["kg_per_t"] < 5).mean()) * 100, 1),
            "share_high_pct": round(float((li["kg_per_t"] >= 25).mean()) * 100, 1),
            "refs": [{"kg": 2, "label": "0.2% EU default · high-pressure diesel 2-stroke"},
                     {"kg": 17, "label": "1.7% EU default · LNG Otto 2-stroke"},
                     {"kg": 31, "label": "3.1% EU default · LNG Otto 4-stroke"}],
            "fumes_kg": 64,
        },
        "ets2026": {
            "price_eur": ETS_PRICE,
            "ch4_t": round(ets_ch4_t), "n2o_t": round(ets_n2o_t),
            "co2eq_mt": round(ets_co2eq_mt, 2),
            "cost_meur": round(ets_co2eq_mt * ETS_PRICE, 1),
            "lng_share_pct": round(float(lng["ets_ch4"].sum()) * GWP_CH4
                                   / (ets_co2eq_mt * 1e6) * 100, 1),
        },
    }


def yoy(d24: pd.DataFrame, d25: pd.DataFrame) -> dict:
    a = d24.set_index("imo")
    b = d25.set_index("imo")
    both = a.index.intersection(b.index)
    out = {"matched_vessels": int(len(both)), "gases": {}}
    for gas in ("co2", "ch4", "n2o"):
        va, vb = float(a.loc[both, gas].sum()), float(b.loc[both, gas].sum())
        out["gases"][gas] = {"y2024": round(va), "y2025": round(vb),
                             "pct": round((vb / va - 1) * 100, 1)}
    lngm = both.intersection(a[a["type"] == "LNG carrier"].index)
    out["lng_ch4"] = {"vessels": int(len(lngm)),
                      "y2024": round(float(a.loc[lngm, "ch4"].sum())),
                      "y2025": round(float(b.loc[lngm, "ch4"].sum()))}
    out["lng_ch4"]["pct"] = round((out["lng_ch4"]["y2025"] / out["lng_ch4"]["y2024"] - 1) * 100, 1)
    new = b.loc[b.index.difference(a.index)]
    out["new_entrants"] = {"vessels": int(len(new)),
                           "ch4_t": round(float(new["ch4"].sum())),
                           "note": "2025 extended MRV scope (general cargo 400-5,000 GT and offshore ships)"}
    return out


def main():
    if len(sys.argv) == 3:
        paths = {2024: Path(sys.argv[1]), 2025: Path(sys.argv[2])}
    else:
        paths = {y: DEFAULT_DIR / f"mrv_{y}.xlsx" for y in YEARS}
    d = {y: load(y, paths[y]) for y in YEARS}
    payload = {
        "meta": {
            "source": "EU MRV 2024 & 2025 (EMSA / THETIS-MRV), full emission reports",
            "source_files": {str(y): paths[y].name for y in YEARS},
            "gwp": {"ch4": GWP_CH4, "n2o": GWP_N2O, "basis": "IPCC AR5"},
            "generated": pd.Timestamp.today().strftime("%Y-%m-%d"),
            "latest_year": 2025,
        },
        "yoy": yoy(d[2024], d[2025]),
    }
    agg25, agg24 = aggregate(d[2025]), aggregate(d[2024])
    payload.update(agg25)                       # app modules show the latest year
    payload["y2024_totals"] = agg24["totals"]
    # the ETS-scoped CH4/N2O columns are only populated in the 2024 file
    # (informative reporting); from 2025 they are zero until the 2026
    # surrender obligation starts. Use the most recent year with data.
    if agg25["ets2026"]["co2eq_mt"] > 0:
        payload["ets2026"]["basis_year"] = 2025
    else:
        payload["ets2026"] = agg24["ets2026"]
        payload["ets2026"]["basis_year"] = 2024
    (HERE / "data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
    t, g = payload["totals"], payload["yoy"]["gases"]
    print(f"data.json | 2025: {t['vessels']:,} navios, CH4 {t['ch4_t']:,.0f} t | "
          f"YoY like-for-like: CO2 {g['co2']['pct']}%, CH4 {g['ch4']['pct']}%")


if __name__ == "__main__":
    main()
