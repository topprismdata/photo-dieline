# R50-A: R49 失败案例冻结登记 (依 R49 终裁, 只归档不继续检索)

日期: 2026-11-28 | 样本: 金典纯牛奶 250ml 砖盒 (原样本, RETAINED WITHOUT REPLACEMENT)

## 冻结登记 (R49 终裁 YAML 逐字)

work_package: WP-L3-01-DOC
execution_status: CLOSED
execution_acceptance: ACCEPTED
evidence_sufficiency: EVIDENCE_INSUFFICIENT

binding_status: CANDIDATE
binding_basis: DOCUMENTED_ONLY

verification:
  verdict: UNRESOLVED
  gtin_status: GTIN_UNVERIFIED
  package_version: PENDING_VERIFICATION
  documented_spec_match: NOT_COMPUTABLE
  physical_verification: BLOCKED

stop_condition_triggered: true
sample_replacement: false
procurement_cost_cny: 0

## 交付项核对 (R50-A 四项)

| 交付项 | 状态 | 位置 |
|---|---|---|
| 证据包 (原始四份快照及 SHA256) | ✓ | l3_01_doc_evidence_pack.json + l3_doc_snapshots/ (2e0f803e/63d8f186/9c713d3f/038c2e4c) |
| 缺失登记 (NULL 字段保留) | ✓ | 冲突 C2 (尺寸 NULL) / C3 (版本 PENDING); 未反向补写 |
| 身份冲突 (有机与普通变体独立登记) | ✓ | 冲突 C1: NLC=有机变体 GTIN 6907992514970 ≠ OFF 6907992507095; plain SKU 无登记命中 |
| 绑定裁决 UNRESOLVED + 结项原因 EVIDENCE_INSUFFICIENT | ✓ | 本文档 + l3_binding_contract_v1.json (BIND-JINDIAN250-ASEPTIC) |

## 商品证据可获得性矩阵 (首案例, R49 终裁第五节落地)

| 属性 | 取得情况 |
|---|---|
| 商品存在性 | 部分取得 (京东零售线索) |
| 品牌与名称 | 部分取得 (登记层=有机变体) |
| 标称净含量 | 部分取得 (登记层 250ml) |
| 精确 GTIN | 未确认 |
| 包装形式 | 获得零售线索 (砖) |
| 包装版本 | 未取得 |
| 单件外尺寸 | 未取得 |
| 完整印刷素材 | 未建立 |
| 物理参数真值 | 未取得 |

矩阵描述证据取得情况, 非保真评分, 非等权覆盖率。

## 纪律声明
- 不删除金典失败记录; 不换 SKU 重算成功率; 原样本 WP-L3-02 NOT AUTHORIZED
- 图片推绝对尺寸 NOT AUTHORIZED; GS1/官网失败只登记取证路径未成功, 不断言资料不存在
