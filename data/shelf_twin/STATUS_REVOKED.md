# 本目录报告状态: 已撤回 (2026-11-24)

`esr_acceptance.json`（COMPLIANT）、`conformance_score.json`（140/140）、`gate_semantic_coverage.json`、`render_gate.json`、`pixel_alignment.json`、`bench_simready_physics.json` **均不代表当前代码的状态**。

| 问题 | 事实 |
|---|---|
| 报告早于资产 | 报告落盘于 2026-11-21 11:00; SKU USD 在提交 `0a03d31`（11-22 00:35）被重导出, 18 个资产全部丢失 `phys:dimensionsMM` / `wikidata_class` / 材质标签, `box_tp_00` 实为 1m 立方 |
| 门没有否决力 | 语义门接受任意 `semantics:labels:*`（只剩 qcode 仍 18/18 PASS）; 物理门不读 USD、用 manifest 数字现搭仿真; `render_gate.json` 的 `pass: true` 是手写的, 指向 32 个版本前的渲染; 像素门给白噪声图判 ALIGNED |
| 资产与场景无关 | `scripts/build_hxl_shelf.py` 不引用这些 USD; 被验收的资产不在被渲染的场景里 |

证据与根因: `docs/reviews/recheck_2026-11-24/findings.md` F4-04…F4-09, 审计原文 `docs/reviews/recheck_2026-11-24/audits/twin_audit.md`。

处置: 货架孪生 / ESR 线迁出本仓（上游制造几何、下游零售孪生）, 迁出后重修导出并改跑 SimReady Foundation 官方校验器。在此之前, 任何引用本目录数字的表述都不成立。
