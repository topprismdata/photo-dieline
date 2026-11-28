# R50-B/C: 文档证据绑定正控候选与双案例协议 (依 R49 终裁任务书)

日期: 2026-11-28 | 时间盒内 | 预算 0 | 原样本金典 250ml 冻结不替换

## R50-A 已交付
金典案例冻结登记完成: r50a_jindian_case_freeze.md (EVIDENCE_INSUFFICIENT / verdict UNRESOLVED / 九项可获得性矩阵 / 四交付项核对含快照哈希)。

## R50-B 正控候选登记 (唯一候选)

**候选**: Coca-Cola Original Taste 330ml 易拉罐 (英国市场规格, 单件)

| 门禁 | 要求 | 核对 | 证据 |
|---|---|---|---|
| PC-01 | 真实商品非虚构 | ✓ | 在售知名商品, 渠道在售 |
| PC-02 | 明确商品型号/身份 | ✓ | Coca-Cola Original Taste 330ml x24, Erudus ID 5bf60cc1f61c4ba2a46c8ecbf18e7eca |
| PC-03 | 厂商公开单件外部尺寸 | ✓ | **Inner Component: 67×67×116 mm** (单件口径显式区分于 Outer Case 404×271×118 mm) |
| PC-04 | 规格与版本明确对应 | ✓ | 规格 PDF Version 1.0, Status Published, 变更日期 2025-07-31 |
| PC-05 | 存在于已有资产表达范围 | ✓ | L1 冻结发行集 `tube_tube_double_seam` 家族 (双接缝管罐形态) |
| PC-06 | 不新增家族/不修改冻结资产 | ✓ | 仅读取, 零改动 |
| PC-07 | 证据获取成本 0 | ✓ | 公开 PDF, 零采购 |

**选择理由** (按 R49 要求记录): 按"证据可获得性"筛选的正控样本, 非随机代表样本。
- 单件口径显式 (Inner Component vs Outer Case 分列) — 直接回应 R48"禁混用单件/整箱尺寸"纪律
- 毫米级精度 + 版本化受控文档 (Version 1.0 + 日期) — PC-04 最强形态
- 备选观察 (不进登记): IKEA 365+ 保鲜盒 3.1l (文章号 192.767.77, 官网 32×21×9 cm, 快照 ikea_558344.html 已存) — 因厘米整数精度 (±5mm) 证据质量弱于 Coke, 未选为候选

### EV-DOC-005 (七字段)

- evidence_id: EV-DOC-005
- subject_id: PRODUCT-POSCTRL-001 (Coca-Cola Original Taste 330ml can)
- attribute: single_item_external_dims
- value: {depth: 67, width: 67, height: 116}
- unit: mm
- source_level: DOCUMENTED_MANUFACTURER
- source_uri: https://dgduupz79pcvd.cloudfront.net/documents/cts/ct0021_spec.pdf
- source_locator: Erudus 平台托管的厂商规格表 (厂商提交, 第三方平台托管 — 如实登记托管层级)
- retrieved_at: 2026-11-28
- source_snapshot_sha256: coke_erudus_ct0021.pdf (见快照清单)
- assertion_type: DECLARED_SPECIFICATION
- package_version_ref: spec Version 1.0 (2025-07-31)
- verification_status: UNVERIFIED

### 资产侧配对件

- asset_id: tube_tube_double_seam_v0131 (L1 冻结发行集成员)
- 声明 extents: 53.779 × 53.779 × 106.923 mm (model.json asset_extents_m)
- model.usdc SHA256: 49802b254e4d67ab26bab8a53e7bc4da2eed3c8632e17b19df9e66344fc70eb8 (64 位实测)
- virtual_brand: TOPPRISM (品牌分离纪律不变)

### 预计算 delta (展示口径, verdict 留治理回路)

| 轴 | 资产声明 mm | 文档声明 mm | delta | delta% |
|---|---|---|---|---|
| 宽 (直径) | 53.779 | 67 | −13.221 | −19.73% |
| 深 (直径) | 53.779 | 67 | −13.221 | −19.73% |
| 高 | 106.923 | 116 | −9.077 | −7.83% |

**delta 状态: COMPUTABLE** — 与金典案例的 NOT_COMPUTABLE 形成对照, 双案例机制可区分"证据不足"与"证据充分但数值不符"两类结局。

## R50-C 双案例协议 preflight

| 案例 | 商品 | 证据状态 | delta | 绑定裁决路径 |
|---|---|---|---|---|
| Case 1 (负例, 冻结) | 金典纯牛奶 250ml | EVIDENCE_INSUFFICIENT | NOT_COMPUTABLE | UNRESOLVED (已终裁) |
| Case 2 (正控候选) | Coca-Cola 330ml | 文档链完整 (身份+单件尺寸+版本) | COMPUTABLE | 待协议裁决: 数值差异 −7.8%~−19.7% 下 verdict 枚举取值需 GPT 明确 |

**提请裁决的两个协议点**:
1. Case 2 若 delta 数值差异显著 (几何非同一), binding_status 应取何值? (候选枚举: CANDIDATE_REJECTED / DOCUMENTED_MISMATCH / 保留 UNRESOLVED 加 mismatch 字段) — 本协议只测机制, 不预设结论
2. 正控判定"机制可行"的判据 = delta 可计算 + 字段级归因可登记, 而非 delta 为零 — 请确认此判据, 或给出您的判据

停止条件维持: 若正控候选七门禁失败 → BLOCKED_BY_DOCUMENTED_REFERENCE + L3 收口评估。本轮七门禁全过, 未触发。

## 快照清单 (sha256)

- coke_erudus_ct0021.pdf: f2aada8c8a76e2af91d83441e734c45533423c6b2cd207501db82f543d4aace9 (184039 bytes)
- ikea_558344.html: 06f709121da9b78839bad2fbe25cd12d57ed5a2bac608906b6be8ec2bd78cb7f (备选观察快照, 不进候选登记)
