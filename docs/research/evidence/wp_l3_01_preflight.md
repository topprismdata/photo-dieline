# WP-L3-01 PREFLIGHT 六门禁 (R46, 采购前冻结)

日期: 2026-11-28 | 依据: R45 终裁 "WP-L3-01 Preflight 必须通过的六项" | 状态: 待 GPT 确认后执行采购

| 门禁 | 冻结内容 | 状态 |
|---|---|---|
| PF-1 实物身份及包装版本确认 | 金典纯牛奶 250ml 砖盒; package_version 待实物核验后回填 (PENDING_VERIFICATION) | 冻结 |
| PF-2 真实商品与资产几何家族一致 | 金典砖盒 (无菌砖形态) ↔ aseptic_aseptic_brick_v0000 (无菌砖家族) ✓ | 冻结 |
| PF-3 GTIN 有真实扫描或明确未核验声明 | gtin=null + GTIN_UNVERIFIED (扫描后更新) | 冻结 |
| PF-4 测量方法、仪器及重复次数冻结 | 卡尺 CAL-001 ±0.02mm × 3 次取均值; 电子秤 SCALE-001 ±1g; 起滑角斜面渐进法; 全部留 raw_values | 冻结 |
| PF-5 证据字段和来源等级冻结 | 绑定契约 v1 evidence 七字段模板 + 来源等级枚举 (REAL_MEASURED/BUSINESS_CLAIMED/ENGINEERING_ASSUMPTION) | 冻结 |
| PF-6 T1/T2/T3/T5 各自可测试范围明确 | T1=容量计算资格 (尺寸对比) / T2=陈列规划资格 (放置+标签) / T3=印刷与视觉资格 (实物摄影 vs 渲染) / T5=物理参数资格 (质量实测 vs 假设; 动态行为对照 DEFERRED) — 各自独立报告不混合 | 冻结 |

采购条件: PF-1..6 冻结 + 配对冻结 (本文档) → 授权执行 ≤¥150 采购。
