# Open Retail Simulation Assets

**A Brand-Neutral OpenUSD Asset Library for Retail Digital Twins, Simulation, and Physical AI Research.**

An open, parametric collection of retail-oriented 3D assets, designed to support research and
development in:

- Retail digital twins and virtual environments
- Synthetic data generation
- Retail scene composition and layout research
- Physical simulation and robotic manipulation research
- OpenUSD-based asset pipelines

Building on open research: NVIDIA USDCraft-10K and the Omniverse SimReady ecosystem
(https://nvlabs.github.io/USDCraft/ · https://huggingface.co/datasets/nvidia/simready-assets).

## What Makes This Dataset Different?

Unlike general-purpose 3D asset collections, this project focuses on **retail-specific asset
families** — beverage containers (beer bottles, cans, baijiu and western spirits bottles,
PET bottles), packaging (gable-top cartons, RSC boxes, gift cartons), and retail fixtures
(carts, baskets, displays, dispensers, flow racks).

The project emphasizes:

- **Retail-specific coverage**: structured asset families reflecting real-world retail
  packaging and equipment categories (dual-axis ontology: product category × packaging
  structure)
- **Parametric generation**: reproducible geometry and configurable asset variations
- **Structured semantics**: machine-readable categories, components, and asset metadata
  with six-level attribute provenance (measured / official_spec / derived / estimated /
  sampled / unknown)
- **Simulation-oriented delivery**: OpenUSD-based assets with documented physical
  properties and validation status — every shipped asset passes NVIDIA's own USDCraft
  validation toolchain (`_validate_usd_asset`, PhysX backend) 15/15
- **Reproducible evidence**: transparent validation protocols, test results, and asset
  provenance — including published negative results

## Scope and Limitations

This dataset is designed primarily as a reusable asset foundation for simulation, digital
twins, synthetic data generation, and physical AI research.

**Synthetic-to-real visual recognition is not currently established.** In our initial
experiments, YOLOv8n models trained on synthetic retail scenes achieved high in-domain
validation performance (mAP50 = 0.86–0.94) but did not generalize to the evaluated real
retail photographs (mAP50 < 0.005). Domain randomization and a preliminary real-image
fine-tuning experiment did not resolve this gap. Full protocols, per-iteration results,
and failure analysis are published in `benchmarks/retail-perception/`.

Therefore:

- We do **not** claim zero-shot transfer to real retail product recognition.
- We do **not** claim that brand-neutral synthetic assets can replace real branded SKU
  datasets.
- We do **not** claim improved real-world object detection performance without
  independent benchmark evidence.
- Simulation and runtime compatibility are stated only for individually validated
  capabilities.

Per-asset validation status and evidence (`metadata.json` in each beverage_liquor asset
directory) should be consulted before using assets in a specific simulation or research task.

## Asset families (v0.6, shipped in this dataset)

| Domain | Family | Classes | Validation |
|---|---|---|---|
| Liquor & beverage | beverage_liquor | 11 (beer bottles 330/500, can 500, baijiu ×2 profiles, wine, whisky, vodka, PET 500/1500, gift box) | G-F1..F7 pass · usdc · spec 11/11 · **NVIDIA validator 15/15** |
| Rigid legacy | beverage_can_330 / bottle_wine / food_container_1l / rsc | 4 | usdc (included in the 15 NVIDIA-validated) |

Also in the repository (not shipped as USD in this dataset version): parametric paper-packaging
families (gable/clv/cone, TDE engine, ~25 variants with a 5010-sample training corpus) and
retail fixtures (nv960, 20 usdc) — see the project repository for pipelines and validation.

Brand-neutral rule: no trademarks, no real brand names, no text or graphics on asset
geometry. Attribute provenance and per-asset validation status are recorded in
`metadata.json`.

## Benchmarks

`benchmarks/retail-perception/` publishes our synthetic-to-real perception experiments
**including negative results**: experimental protocol, three iteration reports
(v0.1 synthetic-only, v0.2 domain randomization, v0.3 real fine-tuning pilot), failure
analysis, evaluation audit, counterfactual diagnostics, and evidence manifests.

## License

Code: MIT. Assets: CC-BY-4.0. Real evaluation photographs: web-sourced for research
evaluation only (provenance recorded; not redistributed in this repository).

Please refer to the accompanying attribution, provenance, and asset-specific documentation.
