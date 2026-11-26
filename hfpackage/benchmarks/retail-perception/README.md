# Retail Perception Benchmark — Synthetic-to-Real Experiments (v0)

Protocol: `experimental-protocol.md` · Reports: `bench_a_report.md` · Audit: `w1_audit.json` · Counterfactual: `w1_counterfactual.json`

| Iteration | Setup | Syn val mAP50 | Real mAP50 |
|---|---|---|---|
| v0.1 | synthetic-only, fixed lighting | 0.938 (on regenerated corpus) | 0.0028 |
| v0.2 | + strong domain randomization | 0.858 | 0.0032 |
| v0.3 | + 6-real-image naive fine-tune | — | 0.0015 |

**Conclusion**: zero-shot synthetic-to-real transfer NOT established at v0. Failure analysis
and W1 audit (78% wrong-class / 18% no-detection; class-agnostic recall@0.1 = 81.9% but
@0.3 = 4%) in the report. Counterfactual: detections depend on high-frequency print detail.
Remediation (real-data calibration route A) requires annotation budget; status tracked in
the repository docs.
