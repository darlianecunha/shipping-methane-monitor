# Beyond CO₂ — Verified Methane & N₂O Emissions from EU Shipping (MRV 2024)

First fleet-scale analysis of the **new greenhouse-gas fields in the EU MRV public dataset**.
Since reporting year 2024, every vessel above 5,000 GT calling at EU ports reports **verified
CH₄ and N₂O emissions** alongside CO₂ (Regulation (EU) 2023/957). This project aggregates those
fields for the first time and publishes the results as a static, dependency-free website.

**Live demo:** deploy this folder to Vercel or GitHub Pages (instructions below).

## Headline findings (reporting year 2024, full emission reports)

| Indicator | Value |
|---|---|
| Vessels with full emission reports | 14,115 |
| Verified CH₄ | 65,129 t/yr |
| Verified N₂O | 8,275 t/yr |
| Fleet CO₂ → CO₂eq uplift | +2.73% |
| Share of fleet CH₄ from LNG carriers | **62.6%** (355 vessels, 2.5% of the fleet) |
| LNG carrier CO₂eq uplift | **+14.9%** over CO₂-only accounting |
| CH₄ at berth in EU ports | 2,765 t/yr |

Two results stand out. First, methane is hyper-concentrated: LNG carriers are 2.5% of the fleet
but emit 62.6% of all verified methane, and their climate footprint is ~15% larger than CO₂-only
accounting suggests — the verified signature of **methane slip**. Second, fleet-wide the
overlooked gas is actually **N₂O**: 2.19 Mt CO₂eq versus 1.82 Mt CO₂eq from methane.

## Files

| File | Purpose |
|---|---|
| `index.html` | Single-page site (Chart.js from CDN, no build step) |
| `data.json` | Aggregated indicators consumed by the page |
| `build_data.py` | Regenerates `data.json` from the EMSA source file |

## Reproducing

1. Download the *Publication of information* file (2024 reporting period) from
   [EMSA / THETIS-MRV](https://mrv.emsa.europa.eu/) (free, no registration).
2. Run:

```bash
python3 build_data.py path/to/EU-MRV-2024.xlsx
```

3. Serve locally or deploy:

```bash
python3 -m http.server        # local preview at http://localhost:8000
vercel --prod                 # or import the repo at vercel.com (framework: Other)
```

For GitHub Pages: Settings → Pages → deploy from branch, root folder.

## Method notes

- Only **full emission reports** ("2024 Full ERs" sheet) are included.
- CO₂eq uses GWP₁₀₀ from IPCC AR5 (CH₄ = 28, N₂O = 265), the values applied by the EU MRV/ETS
  framework. These were also confirmed empirically from the dataset itself.
- *Verified* means checked by accredited verifiers against approved monitoring plans; emission
  factors are fuel-based defaults, so actual methane slip may exceed reported values for some
  engine types. This makes the CH₄ figures a conservative lower bound.
- Ship types with fewer than 20 full reports are excluded from the by-type table.

## Author

**Darliane Ribeiro Cunha, PhD** — Professor, Federal University of Maranhão (UFMA).
Research: maritime decarbonisation, port sustainability analytics, SDG implementation.

Related projects: [SDG Port Hub](https://sdgporthub.com) ·
[CO₂ Liquid Bulk Calculator](https://co2-liquid-bulk-calculator.vercel.app)

## Licence & citation

Data: © European Maritime Safety Agency (EMSA), public information.
Analysis and site: CC-BY 4.0. If you use this work, please cite:

> Cunha, D. R. (2026). *Beyond CO₂: verified methane and nitrous-oxide emissions from ships
> calling at EU ports — first evidence from the EU MRV 2024 greenhouse-gas fields.*
