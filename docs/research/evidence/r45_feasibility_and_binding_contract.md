# R45: 实物证据可行性评估 + 最小产品-资产绑定契约 v0.1 (两件合并)

日期: 2026-11-28 | 依据: R44 (R44-B BLOCKED + R45 授权设计)

## 一、实物证据可行性评估

| 项 | 评估 | 结论 |
|---|---|---|
| 实物采购 | 京东在售金典纯牛奶 250ml×12 提 (≈¥65/提, 单盒≈¥5.4); 京东管线 L1 已验证 (在售链接可溯) | **可行** (当日达/次日达) |
| 量具 | 电子秤 ±1g (¥50 级); 游标卡尺 ±0.02mm (¥30 级); 量角器 | **可行** (低成本即可) |
| 印刷摄影 | 手机微距 + L1 渲染管线 (白底产品图 L1 已验证) | **可行** (研究级) |
| 起滑角 | 斜面法 (可调斜板或书本垫渐进) | **可行** (粗测级) |
| 人员 | 执行侧 1 人 (采买/测量/摄影/建档) | **可行** |
| 预算合计 | 实物 ¥10-15 + 量具 ¥80-100 (一次性) | **总成本 <¥150, 时间 ≤3 天** |

**结论: REAL PRODUCT EVIDENCE FEASIBLE** — 无阻塞。实物到手即可执行 R44-B 六项测量全流程。

## 二、最小产品-资产绑定契约 v0.1 (草案字段)

```yaml
binding_id: BIND-<GTIN或自编>-<asset_id>
real_product:
  gtin: "6901234567890"          # 或 null + 无GTIN声明
  brand: "TOPPRISM-VIRTUAL"      # 虚拟品牌纪律: 真实品牌仅存于实物侧, 资产侧保持虚拟
  product_name: "纯牛奶 250ml 盒装"
  spec: "250ml"
  package_version: "2025 在售版"
asset:
  asset_id: "aseptic_aseptic_brick_v0000"
  asset_sha256: "<64字符>"
  fidelity_tiers:                 # 分层保真框架 (Task-Oriented v0.1 Physical 分支)
    T1_capacity: MET_CONDITIONAL
    T2_planning: MET
    T3_commercial: NOT_MET
    T5_simulation: CONDITIONAL
evidence_chain:
  dims_source: "REAL_MEASURED (卡尺±0.02mm, 3次取均值)"   # 升级自 BUSINESS_CLAIMED
  mass_source: "REAL_MEASURED (电子秤±1g, 空瓶+满瓶)"      # 升级自 MEASURED_MASS_STATE_UNKNOWN
  print_reference: "REAL_PHOTO (实物正面+背面+顶面 微距×3)"
  slide_angle_deg: null           # 起滑角实测后填
verification:
  dims_match_delta_mm: null       # 实测 vs 资产声明 逐轴差
  verdict: null                   # SKU_EXACT / GEOMETRY_EQUIVALENT / APPROXIMATED / UNRESOLVED
governance:
  charter: "RWI-L3 (批准后)"
  protocol_run: "WP-L3-01"
```

## 三、契约纪律 (草案)

1. 真实品牌信息仅存 evidence_chain.real_product 摄影/记录, 资产渲染侧保持 TOPPRISM 虚拟品牌 (L1 纪律)
2. 每字段带来源等级标签 (REAL_MEASURED / BUSINESS_CLAIMED / ENGINEERING_ASSUMPTION)
3. verdict 变更须走 GPT 治理回路 (禁止执行侧自行升级 SKU_EXACT)
4. 冻结发行集零覆盖: 绑定记录独立于发行资产存储
