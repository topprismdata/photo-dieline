# Pack10K — Retail Digital Twin Assets, Validated on Consumer Hardware

*Bringing rigorous 3D asset quality assurance to Apple Silicon and the retail industry.*

**Building on open research.** We gratefully acknowledge NVIDIA's USDCraft-10K and the
broader Omniverse ecosystem for providing open research foundations, reference assets,
and validation practices. This dataset would not exist without that openness.
- NVIDIA USDCraft: https://nvlabs.github.io/USDCraft/
- Dataset: https://huggingface.co/datasets/nvidia/USDCraft-10K (Apache-2.0)
- Paper: https://arxiv.org/abs/2610.11322

**Research integrity notice.** An earlier benchmark result (99.84%) has been **withdrawn**
following a pixel-level audit of our evaluation pipeline: fine-grained studio background
noise contributed to measured edge density (an 8.4 percentage-point shift in E1 win rate),
while compression and resolution differences affected the reference thumbnails. All current
results use the revised (clean-backdrop) protocol. The original experiments and correction
history remain available in the repository (commit 509f71c).

## 01 — Why Pack10K

Rigorous asset production and quality assurance, accessible without data-center hardware.
Our demonstrated workflow runs end-to-end on Apple Silicon (Blender Metal rendering,
PyTorch MPS where applicable); the evaluated execution path requires no CUDA runtime.
Windows / Linux CPU-only / other GPU backends: **not yet validated**. Some label copy was
drafted with external LLM assistance; all metrics are computed locally.

## 02 — Retail asset families

48 retail-oriented families: shelving, shopping carts, baskets, refrigeration, trash &
logistics fixtures, packaging — every asset ships with usdc + model.json + packaging.json +
conformance.json + print.png + a 1024² printed render (see `families/`, `renders/`).

## 03 — Reproducible benchmark (NV960: 480 USDCraft reference assets → 960 thumbnails × 48 classes)

Pairwise comparison under two independently defined protocols (full formulas & tie rules:
`docs/nv960/protocols.md`; per-pair evidence ledger with file hashes:
`docs/nv960/evidence_ledger.json`):

| Protocol | Result | Scope statement |
|---|---|---|
| Seven-metric pixel composite | **82.0%** of pairs net-positive | In this study's predefined seven-metric composite protocol |
| Strict four-axis contract | **90.94%** (873W/87L) | Independent four-axis contract experiment, fully disclosed |

The two protocols answer different questions: the strict four-axis contract asks
"who wins this specific four-clause asset contract" (binary per pair); the seven-metric
composite asks "across the full pixel-statistics spectrum, in what fraction of pairs does
the net advantage lie" — independent experiments, not strict/loose versions of one scale.
Full formulas: `docs/nv960/protocols.md`.

Metric-level (qualified phrasing): 98.1% of pairs score higher on S1 sharpness; 88.4% higher
on E1 edge density; 70.2% higher on E2 direction entropy. Higher metric values are not
claims of superior realism or asset quality. Statistical unit: 960 pairs derive from 480
reference assets (2 thumbnails each) — not 960 independent assets.

The 87 losing pairs are retained in full (see per-class tables); their stratification
(single-asset vs. composed-scene complexity) is planned future work — no attribution claim
is made before that classification exists.

## 04 — Independent validation toolkit

Independent V-gate structural audit (V1–V7) + pixel audit ladder (the tool that found and
retracted our own metric confound). Applied to a 480-asset USDCraft sample, **20.8% passed
all gates under OUR protocol** — this reflects compatibility with Pack10K's validation
requirements and must not be read as a failure rate under NVIDIA's original SimReady
validation protocol. Tools and asset-level findings are released for reproducible,
complementary quality assessment.

## 05 — Acknowledgements & limitations

- With thanks to NVIDIA for USDCraft-10K (Apache-2.0). Thumbnails appear in contact sheets
  as low-resolution side-by-side research references; full attribution in
  `docs/nv960/contact_sheets attribution file` and `docs/nv960/licenses.json`.
- Hardware: Apple M1 Max 64 GB, macOS; environment manifest `docs/nv960/environment.json`.
- Known limitations: single-asset families underperform composed-scene thumbnails on edge
  density; B1 metric lacks masks (uninformative for wide classes); Windows/CPU untested.
- Pack10K is a complementary contribution to the open 3D ecosystem — **not** a replacement
  for NVIDIA's simulation-ready asset infrastructure.

## Repository

Full pipeline (verdict / pixel audit / renderer / fixture families / labels / sharpen):
https://github.com/topprismdata/photo-dieline (`scripts/nv960_*.py`, `docs/nv960/`)
