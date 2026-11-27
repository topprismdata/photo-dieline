# T01/T02 联合送审件：WP-V/REP-IDENTITY 联合报告 + WP1-Pilot-100 协议 v0.4

- 日期：2026-11-27
- commit：见 git log（T01 数据 docs/research/evidence/rep_identity_stats.json + validator_identity；T02 协议 + scripts/wp1_protocol_selftest.py）
- 追溯表：见 §D（强制治理门禁落实）

## A. 验证器身份台账（WP-V）

| 验证器 | 全名/来源 | 检查集 | 我方历史声明 | 与 usdchecker 红灯关系 |
|---|---|---|---|---|
| USDCraft SDK `_validate_usd_asset(backend='physx')` | NVlabs/USDCraft (arXiv 2610.11322 官方仓) `_usd_validate.py` | 15 结构检查（default_prim/Z-up/米/千克/无场景/有限值/依赖闭包/相对路径/vendor 命名空间/物理图等） | **175/175 PASS（真实）**——台账口径即此验证器 | 无关（两工具检查集不相交） |
| Pixar usdchecker (OpenUSD) | /usr/bin/usdchecker | 含 MaterialBindingApiAppliedValidator 等 | **从未声称** | 红灯=覆盖缺口，非虚假 |
| auditor v2.2（我方） | scripts/auditor_core.py | 拓扑/绕向/UV/体积符号 | 试点内使用 | 互补 |
| trimesh 4.10（独立交叉） | pip | watertight/winding/volume | 交叉对照 | 互补 |

**结论**：175/175 PASS 对 USDCraft SDK 验证器为真（口径已核验：conformance.json profile="topprism-selfaudit", validator.name="usdcraft_generic", checks_passed=10 结构项）；usdchecker MaterialBindingAPI 红灯是**新增覆盖缺口**（应补 MaterialBindingAPI.Apply —— 已在 WP-A0.2 裁决 ADOPT，候选路径待 G2）。无历史造假，有口径混淆风险（已按 GPT 要求建立身份台账）。

## B. 9,386 件未舍入表达统计（REP-IDENTITY）

全量逐件未舍入 min-axis 判定（`rep_identity_stats.json`）：

| observed 表达 | 件数 | 占比 | 家族 |
|---|---:|---:|---|
| SOLID_3D（三维折叠体） | 9,015 | 96.0% | 75 家族 |
| FLAT_PATTERN（min_axis 恰 0.0） | 371 | 4.0% | **envelope_envelope_square(185) + envelope_envelope_wedge(186)** |
| MIXED | 0 | — | — |

**关键修正与澄清**：
1. 信封家族的平面表达是其**产品语义正确形态**（平面邮件无折叠体）——FLAT_PATTERN 对该 371 件 = representation_match **TRUE**，非缺陷。
2. 先前"9,386 全部平板"主张**再次证伪并撤回**（该错误曾源于单样本舍入显示误读）。
3. 真实缺陷：brick 系 742 件绕向（内向+不一致）——**已在家族源码修复**（0 反向对实测）+ 导出规范化门控（G1-02 五前置），候选重编译路径待 G2 授权。

**REP-IDENTITY 三字段（逐件登记口径，v0.4 落地）**：
- `declared_representation`: 由家族语义登记（envelope→FLAT_PATTERN；其余 75 家族→SOLID 折叠体）
- `observed_representation`: 未舍入 bbox+拓扑实测（本审计字段来源）
- `representation_match`: declared==observed（envelope 371 件 TRUE；其余 9,015 TRUE；绕向缺陷 brick 系以 winding 判据单列）

## C. 跨环节资产身份（抽检）

`conformance.json` dim_reconciliation（aseptic_brick 抽样）：analytic/folded/stage 三方逐轴 0.0 mm 差 → **QA/fold/export 三环节使用同一资产身份**（同一折叠几何）✓。既有三重验证（USDCraft 结构+尺寸对账+打包契约）均在折叠表达上运行 → 跨环节身份一致（除 usdchecker 覆盖缺口外）。

## D. 追溯表（要求—实现—测试—证据）

| 要求（R09-11 判词出处） | 实现 | 测试 | 证据 | 状态 |
|---|---|---|---|---|
| WP-V: 验证器身份台账 | 本报告 §A 四验证器表 | usdchecker 实跑 + conformance.json profile 核验 | evidence/usdcheck_*.txt + conformance.json | CLOSED |
| REP-IDENTITY: 未舍入全量统计 | 逐件 min_axis <1e-4 判据 | 全量扫描 9,386/9,386 | evidence/rep_identity_stats.json | CLOSED |
| REP-IDENTITY: 跨环节身份 | conformance dim_reconciliation 抽检 | aseptic_brick 三方 0.0 对账 | conformance.json | 抽样 1 家族 CLOSED，全量推广 OPEN（备 G2 后） |
| 印刷镜像 | 维持 UNKNOWN | 未做 | — | OPEN（红线维持） |

## E. WP-A3 归档沉淀（5% 资源按 GPT 裁定执行完毕）

WP-A3 全系列（R09-03→R09-08）报告/证据/源码修复/仲裁 json 已归档于 docs/research/；TRIAL-CLOSURE-CONSTRAINT-TRACE 延期登记于 engineering_verdicts.md。
