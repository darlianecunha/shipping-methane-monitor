# Beyond CO₂ — Verified Methane & N₂O Emissions from EU Shipping (MRV 2024–2025)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21144287.svg)](https://doi.org/10.5281/zenodo.21144287)


Two-year observatory of the **greenhouse-gas fields in the EU MRV public dataset**.
Since reporting year 2024, every vessel above 5,000 GT calling at EU ports reports **verified
CH₄ and N₂O emissions** alongside CO₂ (Regulation (EU) 2023/957); 2025 is the second year, and
the first under the extended MRV scope. This project aggregates both years and publishes the
results as a static, dependency-free website.

**Live demo:** [shipping-methane-monitor.vercel.app](https://shipping-methane-monitor.vercel.app/)

## Headline finding (v2): same ships, one year apart

Like-for-like, on the **11,453 vessels** that filed full reports in both years:

| Verified emissions | 2024 → 2025 | Change |
|---|---|---|
| CO₂ | 131.3 → 124.7 Mt | **−5.1%** |
| CH₄ | 58,093 → 70,427 t | **+21.2%** |
| N₂O | 7,390 → 6,990 t | −5.4% |
| CH₄, LNG carriers only (293) | 34,793 → 41,145 t | +18.3% |

**Decarbonisation is trading CO₂ for methane.** Separately, the 2025 scope extension added
5,211 newly covered vessels (mostly smaller general cargo and offshore ships) with a further
14,353 t of reported CH₄ outside this comparison.

## Reporting year 2025 (latest, full emission reports)

| Indicator | Value |
|---|---|
| Vessels with full emission reports | 16,664 |
| Verified CH₄ | 84,779 t/yr |
| Share of fleet CH₄ from LNG carriers | 59.5% |
| Vessels in the slip analysis | 393 LNG carriers (median 17.3 kg CH₄/t fuel) |

## Observatory modules

| Module | Finding |
|---|---|
| **Same ships, one year apart** | The year-on-year table above, computed only on vessels present in both years |
| **Who owns the methane** | The top 10 DoC holders concentrate ~half of all verified CH₄. Alongside LNG-carrier operators (Seapeak, Dynagas, MOL, Knutsen, Maran Gas), LNG-fuelled passenger fleets (Costa Crociere, Baleària) rank among the top emitters |
| **Methane-slip fingerprint** | CH₄ intensity of LNG carriers clusters exactly on the EU default slip factors (0.2% / 1.7% / 3.1% of fuel mass). The ICCT FUMES campaign measured a real-world average of **6.4%** for LNG Otto 4-stroke engines — twice the highest default and literally off the chart. Verified ≠ measured: reported totals are a lower bound |
| **The 2026 ETS methane bill** | ETS-scoped CH₄ (30,532 t) and N₂O (4,817 t) equal 2.13 Mt CO₂eq: **€170.5 M/year** at €80 per allowance. Basis: the 2024 file, the latest in which EMSA populates these fields (the surrender obligation starts with 2026 emissions). Only 15.5% falls on LNG carriers: the bill lands across the whole fleet |

Reference values: EU default slip factors from the FuelEU Maritime / MRV implementing rules;
real-world slip from ICCT, *Fugitive and Unburned Methane Emissions from Ships (FUMES)*, 2024
(LPDF 4-stroke plume average 6.42%, median 6.05%).

## Files

| File | Purpose |
|---|---|
| `index.html` | Single-page site (Chart.js from CDN, no build step) |
| `data.json` | Aggregated indicators consumed by the page |
| `build_data.py` | Regenerates `data.json` from the two EMSA source files |

## Reproducing

1. Download the *Publication of information* files (2024 and 2025 reporting periods) from
   [EMSA / THETIS-MRV](https://mrv.emsa.europa.eu/) (free, no registration), or via the public
   API: `/api/public-emission-report/downloadable-files` lists the current versions and
   `/api/public-emission-report/reporting-period-document/binary/{year}/{version}` downloads them.
2. Run:

```bash
python3 build_data.py path/to/mrv_2024.xlsx path/to/mrv_2025.xlsx
```

3. Serve locally or deploy:

```bash
python3 -m http.server        # local preview at http://localhost:8000
vercel --prod                 # or import the repo at vercel.com (framework: Other)
```

For GitHub Pages: Settings → Pages → deploy from branch, root folder.

## Method notes

- Only **full emission reports** ("Full ERs" sheets) are included; the year-on-year module
  compares only vessels present in both years, isolating the scope extension of 2025.
- CO₂eq uses GWP₁₀₀ from IPCC AR5 (CH₄ = 28, N₂O = 265), the values applied by the EU MRV/ETS
  framework. These were also confirmed empirically from the dataset itself.
- *Verified* means checked by accredited verifiers against approved monitoring plans; emission
  factors are fuel-based defaults, so actual methane slip may exceed reported values for some
  engine types. This makes the CH₄ figures a conservative lower bound.
- Ship types with fewer than 20 full reports are excluded from the by-type table.
- ETS-scoped CH₄/N₂O columns are zero in the 2025 file (the ETS surrender obligation for these
  gases starts with 2026 emissions); the ETS module therefore uses the 2024 file and says so.

## Author

**Darliane Ribeiro Cunha, PhD**.
Research: maritime decarbonisation, port sustainability analytics, SDG implementation.

Related projects: [SDG Port Hub](https://sdgporthub.com) ·
[CO₂ Liquid Bulk Calculator](https://co2-liquid-bulk-calculator.vercel.app)

## Licence & citation

Data: © European Maritime Safety Agency (EMSA), public information.
Analysis and site: CC-BY 4.0. If you use this work, please cite:

> Cunha, D. R. (2026). *Beyond CO₂: verified methane and nitrous-oxide emissions from ships
> calling at EU ports — two years of evidence from the EU MRV greenhouse-gas fields (2024–2025).*
