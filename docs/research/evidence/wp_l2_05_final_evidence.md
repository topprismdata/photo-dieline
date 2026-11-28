# WP-L2-05 SimReady 工程研究 阶段终账 (R44-A, 不新增实验)

日期: 2026-11-28 | 依据: R43 终裁 (R44-A: 证据终账, 只归档) | 范围: hfpackage milk_bottle_1000 + MuJoCo 适配路径 (不外推)

## 一、实验运行全记录 (历史结果全部保留)

| RUN | 内容 | 结果 | 台账 |
|---|---|---|---|
| SR-1 | USD 加载 (单位/上轴/网格/bbox) | PASS (4,992 顶点/29,952 面, 85×85×235mm) | r42_sr1_loading_check.json |
| SR-2 首测 | 50mm 声明落差 (实际 105mm 口径) | 静置✓ 直立✓ 穿透 9.35mm | r42_sr2_drop_result.json |
| SR-2 复测 | 50mm 口径冻结重测 | 穿透 6.88mm (口径和解验证) | r43_ab_drop_collision.json |
| 推挤首测 | 2N (力/质量失配) | 飞出 12m+翻倒 82.5° (荒谬结果如实保留) | r43_c_push_stack.json |
| 推挤复测 | 0.2N (质量比例修正) | 位移 1.1mm/不倒 (物理合理) | 同上 |
| 堆叠 | 瓶2 同向叠瓶1 顶 | 稳定保持 (220.9/221mm); 凸包圆柱叠放=平凡稳定, 真实瓶盖接缝语义未表达 | 同上 |
| 材质 AREA 10mm | 三粗糙度 (瓶体曲面) | streak 全柱宽不可辨 (负结果) | r40_bottle_roughness_results.json |
| 材质 AREA 5mm | 四粗糙度 R41-FINAL | 仍不可辨 (光源尺寸假设证伪) | r41_final_results.json |

## 二、S1-S4 成熟度登记 (正式冻结, 编号遵 R43 裁决)

| 级 | 能力 | 状态 | 证据 |
|---|---|---|---|
| S1 能加载 | USD/单位/包围盒 | **REPORTED PASS** | r42_sr1_loading_check.json |
| S2 能参与动态任务 | 落地/推挤/堆叠运行 | **REPORTED PASS** (不代表响应正确) | r43_c_push_stack.json |
| S3 能正确接触 | 穿透 6.88-9.35mm; 碰撞表示对照未完成 | **NOT_ESTABLISHED** | r43_ab_drop_collision.json |
| S4 能可信模拟真实商品 | 缺独立物理参数与实际行为真值 | **BLOCKED** | r43_d_physical_reference.md |

范围限定: 仅 hfpackage 引用奶瓶 + MuJoCo 适配路径; 不外推至 77 发行类或 9,386 件冻结资产。

## 三、协议偏离登记 (R43 裁决要求)

1. G3-L 早于 G2-M2 送审执行 (时序违反) — PROTOCOL_DEVIATION_REGISTERED, 历史结果保留为探索性证据
2. 50mm vs 105mm 落差口径混用 — 已和解 (A 项), 双值分别保留
3. 2N 推力标定失配 — 原始荒谬结果保留 + 比例修正复测分开登记

## 四、补齐清单投资终态 (R43 裁决)

| 项 | 优先级 | 终态 |
|---|---|---|
| 实物称重 | P0 | 条件授权 (最小实物样本) |
| 摩擦文献标定 | P1 | 允许资料登记, 不替代实测 |
| 碰撞表示升级 | P2 | DEFERRED |
| 网格水密修复 | P2 | NOT AUTHORIZED (渲染几何开放边界≠碰撞代理失败) |
| 液体晃动 | OUT_OF_SCOPE | 本阶段排除 |
