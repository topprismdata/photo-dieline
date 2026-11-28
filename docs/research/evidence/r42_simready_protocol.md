# R42 SimReady 最小任务设计 + 物理参数资格审查 + 独立协议 (三合一)

日期: 2026-11-28 | 章程: RWI-L2 (WP-L2-05 NEXT PRIORITY) | R41-F 裁决: SR 最小任务设计+物理参数资格审查+独立协议 PREFLIGHT

## 一、最小任务设计 (遵 R31 四层 SR-1..SR-4, 取最小)

| 层 | 任务 | 状态 | 判据 |
|---|---|---|---|
| SR-1 | 资产加载: 单位/上轴/网格/包围盒验证 | **PASS** (r42_sr1_loading_check.json) | upAxis/metersPerUnit 正确; 4,992 顶点/29,952 面; bbox 85×85×235mm 合理 |
| SR-2 | 落地测试: 50mm 落差→接触→静置 | **PASS with limitation** (r42_sr2_drop_result.json) | 静置 ✓ 直立 ✓ (0° 倾角); 穿透 9.35mm=接触保真度限制如实登记 |
| SR-3 | 质量/质心/惯量/摩擦可信参数 | **BLOCKED** (物理参数资格审查 §二) | MEASURED_MASS_STATE_UNKNOWN + 上游自带头量荒谬 |
| SR-4 | 动态任务 (推/堆/抓) | DEFERRED (依赖 SR-3) | — |

## 二、物理参数资格审查 (核心发现)

1. **上游 SimReady 元数据自带 mass=0.0156kg (1L 奶瓶 15.6g — 物理荒谬) 且通过 NVIDIA conformance** — 上游数据质量发现, 已登记
2. RWI-L1 已知限制 MEASURED_MASS_STATE_UNKNOWN 与上游发现同源: 包装质量无实测数据是行业现状
3. SR-2 执行采用**工程假设质量 0.05kg** (空 1L 奶瓶 40-60g 区间中值), 明确标注非实测 — 遵 GPT "明确标注的工程假设场景" 允许条款
4. 资格结论: 碰撞/接触/静置稳定性 = **工程假设下可验证**; 真实物理保真 (跌落冲击/堆叠力学定量) = **BLOCKED 直到质量实测**

## 三、独立协议冻结 (SR 实验独立于 WP-L2-01/02 协议)

- 几何: hfpackage milk_bottle_1000 (非冻结发行集成员, 独立引用)
- 质量假设: 0.05kg (标注工程假设)
- 引擎: MuJoCo (L1 已验证本机可用)
- 判据: 静置 + 直立 + 穿透量化 (不设物理保真宣称)
- 已执行 RUN: SR-1 一次 + SR-2 一次 (r42_sr1/sr2 json)
- 负结果/限制登记: 穿透 9.35mm + 上游质量荒谬 + 网格非水密

## 四、测试对象说明

hfpackage/assets_dairy/milk_bottle_1000 (SimReady USD, 4,992 顶点/29,952 面, bbox 85×85×235mm) — 非 9,386 冻结集成员, 独立引用; L2 章程 WP-L2-05 允许。
