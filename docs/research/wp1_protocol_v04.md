# WP1-Pilot-100 盲测协议 v0.4（完整替换版 · 冻结候选）

- 版本：v0.4（按 R09-11 裁决"完整替换，不追加修补"）
- 终态枚举：与 GPT 签发的八终态**逐字一致**（OUT_OF_SCOPE / INPUT_INSUFFICIENT / FAMILY_NOT_COVERED / FAMILY_ADAPTATION_REQUIRED / CONTRACT_UNKNOWN / GATE_FAIL / VALIDATION_PENDING / SUCCESS）
- 机器门禁：`scripts/wp1_protocol_selftest.py`（W01-W10 十例，与协议公式同源模块）
- 状态：**PROPOSED**——十例机器测试随本件送审，签发后 FROZEN

## 1. 八终态（唯一有效枚举；NOT_APPLICABLE 仅限单项门禁级，不得作为 SKU 终态）

| 终态 | 含义 |
|---|---|
| OUT_OF_SCOPE | 预冻结适用域之外 |
| INPUT_INSUFFICIENT | 域内输入不足（关键规格字段缺失/异常）|
| FAMILY_NOT_COVERED | 输入充分但 77 家族未覆盖该结构 |
| FAMILY_ADAPTATION_REQUIRED | 家族命中但需修改家族模板 |
| CONTRACT_UNKNOWN | 必要交付契约未知 |
| GATE_FAIL | 生成或必要门禁失败 |
| VALIDATION_PENDING | 无明确失败，但必要验证（官方验证器/物理实测）未完成 |
| SUCCESS | 全部必要验收完成且通过 |

## 2. 五指标（冻结公式；与 selftest 同源实现）

记 N=样本总数；n_scope=OUT_OF_SCOPE 外的样本数（域内）；n_input=域内且 INPUT_INSUFFICIENT 之外；n_covered=n_input − FAMILY_NOT_COVERED；n_adapt=FAMILY_ADAPTATION_REQUIRED 数。

| 指标 | 公式 | 分母零语义 |
|---|---|---|
| M0 域内率 | n_scope / N | N=0 或 n_scope=0（全域外=抽样失效）→ UNDEFINED |
| M1 输入可用率 | n_input / n_scope | n_scope=0 → UNDEFINED |
| M2 结构覆盖率 | n_covered / n_input | n_input=0 → UNDEFINED |
| M3 编译交付率 | SUCCESS / (n_covered − n_adapt) | 分母=0 → UNDEFINED |
| M4 验证完备率 | max(0, SUCCESS − VALIDATION_PENDING 数) / (n_covered − n_adapt)（负完备率钳 0） | 分母=0 → UNDEFINED |
| C_delivered 交付单位成本 | Σ成本(全部样本) / SUCCESS 数 | SUCCESS=0 → UNDEFINED（不可计算）|

- W06 语义：GATE_FAIL 与 VALIDATION_PENDING 互斥终态，FAIL 不被 PENDING 吸收。
- 置信区间：精确二项 95%（n<150）。

## 3. 一致性门禁（逐件门禁级；NOT_APPLICABLE 允许）

| 门禁 | 阈值（冻结）| NA 语义 |
|---|---|---|
| DIM-01 | 生成 bbox vs 声明尺寸逐轴 ≤ max(1mm, 1%)（R09-10 已批准为 Pilot 阈值）| 无 |
| QUAL-01 | 仅当商品有真实实测质量数据时进入 | 无实测 → NOT_APPLICABLE |
| ART-01 | 有铰接 → 铰接门禁；无铰接 → NOT_APPLICABLE | — |
| PRINT-01 | 翻转面角落于印刷墨水区 → PRINT_MIRROR_RISK | 无 |

## 4. 合法输入冻结与盲测隔离

冻结日哈希登记：编译器 commit、77 家族版本、生成配置、门禁版本、本协议版本。
**持样方**：独立第三方受控存储保存样本；评审侧（GPT）持清单哈希与审计证据；执行侧仅获协议允许的输入字段（匿名规格）。样本清单在编译器冻结**前**生成。

## 5. 分层随机抽样（完整登记）

1. 分层 = 品类 × 包装形态（非空组合）。
2. 配额 = 层占真实商品总体比例 × 100，最少 2 件/非空层。
3. 层内简单随机 `random.sample`，全局 seed 冻结日登记。
4. 排除：关键规格（≥3 轴）缺失/类型异常且持样方确认不可修复 → 候选 OUT_OF_SCOPE。
5. 泄漏检查：家族设计从未接触持样方商品库的书面声明 + 家族来源清单供抽查。

## 6. VALIDATION_PENDING 语义

官方验证器/物理实测未完成 → VALIDATION_PENDING；本地自研门禁结果单独记录，**不得替代官方验证计入 M4**。

## 7. 成本

C_i = r_h·t_h,i + r_m·t_m,i + C_ext,i；费率冻结日登记；失败样本成本计入 Σ；C_delivered = ΣC_i / SUCCESS 数（SUCCESS=0 → UNDEFINED）。

## 8. 报告四件套

coverage_table / terminal_state_distribution / cost_ledger / evidence（逐件门禁原文）。全部比率附 95% 精确二项 CI。

## 9. 冻结签署行

GPT 签核（十例机器测试通过 + 本 v0.4 审查）+ 用户批准 → 状态 FROZEN。


## 10. 机器门禁与历史验证器身份台账（v0.4.1 增补）

- 协议机器门禁 = `scripts/wp1_protocol_selftest.py`（W01-W10 十例，实测 10/10 PASS）。协议文本与 selftest 公式**同源**：任何公式修改必须先改 selftest 再改文档（版本关联）。
- 历史 175 件验证器身份台账（WP-V 遗留追溯闭环，见 evidence/validator_identity_tracing.json）：
  - 工具实物：`~/usdcraft_study/code/sdk/_core/_usd_validate.py`（NVIDIA SDK，sha256 前 16 位 725e97d4afa6877f）
  - 运行记录：`docs/nvidia_package_emit_results.json` **202 条逐资产判决**（fail-closed）
  - 口径修正：台账"175"系记账口径错误（variant 记 35 实为 60、dairy 2 漏记）——真实总数 202；逐资产判决全部在案，无证据造假
