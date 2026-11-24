# ESR Measurement Framework — V0.1 (研究草案)

> 北极星: Evidence-Simulation-Ready (ESR) — 用最新开源组件与 agentic 技术构建超越 NVIDIA SimReady 的框架。
> 本文档是 ESR 的 **measurement 层规范 V0.1 研究草案**, 第一个垂直实例 = photo-dieline 参数化测量层。
> 依 R4 咨询裁决 (2026-11-25): "ESR Measurement V0.1 研究 APPROVED; ESR 通用有效性声明 NOT VALIDATED"。

## 0. 定位声明 (防"改名学"指控, ESR-C01)

ESR measurement 层**不声称发明**测量学/VVUQ 原则。继承关系:

| 成熟体系 | 继承能力 | ESR 增量 (待证) |
|---|---|---|
| JCGM GUM / JCGM 100 | 测量模型、不确定度传播 | 不可辨识时的显式拒绝契约 (REFUSED/OUT_OF_DOMAIN) |
| NIST 测量科学 | 参考测量、重复性 | 参考值不确定性进入比较口径 (u_ref) |
| NASA-STD-7009 | 仿真可信度生命周期 | 证据治理的可执行化: 冻结/探针/负结果台账为机器可查工件 |
| ASME V&V 10/20 (VVUQ) | 风险导向验证确认 | 交付门禁三态 (AUTO/MANUAL/REJECT) + 双率评价制度 |
| 逆问题文献 (Brynjarsdóttir & O'Hagan 2014 等) | model discrepancy 与参数混淆 | 对抗可辨识性探针 (P4 协议) 作为常规验收项 |

**ESR 的差异化命题**: 把上述原则编译为 **Agent 能执行、能自查、能复现、不能静默绕过的工程契约**。
该增量本身需要 ESR-C01/C06 的对照实验证明, V0.1 只建档不宣称。

## 1. 七层架构 (L0–L7)

```
L0 Measurement Intent    测量对象/物理量/用途/容差 (冻结)
L1 Observation           采集、标定、误差结构 (协议冻结)
L2 Model                 物理模型、参数域 D0、模型失配声明
L3 Identifiability       可辨识性、退化、对抗反例、观测充分性
L4 Estimation & UQ       求解、误差传播、偏差分析 (σ 口径)
L5 Simulation Evidence   合成真值、受控注错 (含负结果台账)
L6 Physical Evidence     独立参考测量、实物验证 (u_ref 口径)
L7 Delivery Adjudication 按冻结契约裁决: AUTO / MANUAL / REJECT
横贯: 证据治理 = 冻结版本 · 探针纪律 · 负结果台账 · 可复现性 · 独立裁决 · 变更控制
```

## 2. 三层域契约 (DOM-02, 已实现)

- **D0 Mathematical Domain**: 数学声明域 (`param_domain_violations`) — 不因治理方便而收窄;
- **D1 Measurement Domain**: 测量有效域 (lean≤75° V1.0 保守边界, 等价 gap≤1.9319·Ef, DOM-01 核对) —
  违规转人工, 不入 D0;
- **D2 Automatic Delivery Domain**: σ 门槛 + 协议检查 + 失配门 (delivery_policy)。
- 不变式: D2 ⊆ D1 ⊆ D0; 数学合法 ≠ 可测 ≠ 可自动交付。
- 治理风险备忘 (GPT): 收窄 D0 会把应被识别的退化案例排除出测试范围, 削弱门禁证明价值 — 禁止。

## 3. 双率评价制度 (强制, ESR-C05)

每份验证报告必须同时输出:
- `C_auto = N_auto / N_total` (自动交付覆盖率)
- `R_auto = N_wrong,auto / N_auto` (自动交付错误率; 无 AUTO 时为**未定义**, 不得记 0)

案例入账: B06 门禁战役 — 门禁关 AUTO 36/36 错 21 (R_auto=58%) → 门禁开 AUTO 0/36 错 0。
C_auto=0 时 R_auto 无意义 — "错误清零"不是能力, 双率才是。95% 转人工写入负面案例库。

## 4. 仿真自证禁令 (inverse crime, ESR-C03)

- 禁止: 同一几何假设 → 合成真值 → 生成观测 → 同模型反演 → 宣布测量正确 (只证数学一致性);
- 合成域证据 (L5) **不得自动升级**为物理测量精度证据 (L6);
- L6 证据须含独立参考 (真尺+u_ref) 或不同来源正向模型;
- photo-dieline 现状: 无噪声合成实验 = 数学一致性证据; 物理有效性证据 = R5 真实试验 (未完成, 如实标注)。

## 5. 独立评审六项挑战与应对 (ESR-C01..C06)

| 编号 | 挑战 | V0.1 应对 |
|---|---|---|
| C01 | 原创增量? | §0 映射表; 增量=契约化, 待对照实验 |
| C02 | 只适用 PhotoDieline? | 第二垂直实例 = 货架空间测量 (OpenUSD 场景, 复用本仓合成管线); 规范先于第二实例冻结 |
| C03 | 仿真自证? | §4 禁令; R5-A/B/C 真实证据分级 |
| C04 | 冻结判据冻结错误? | 变更控制: 判据版本化 + 影响分析 + 重验收流程 (findings 记账) |
| C05 | 拒绝换安全? | §3 双率强制 |
| C06 | 优于现有方法? | 同任务 有/无 ESR 契约 对照实验 (待设计) |

## 6. 核心原则沉淀 (B06 案例)

> 当问题根源在**观测信息不足**时, 不能靠增加统计复杂度替代信息补充; 当系统无法证明自己知道答案时,
> **正确识别自身不可辨识的边界**本身就是需要独立验证的工程能力。

技术负结果台账 (全部机器可查: docs/reviews/recheck_2026-11-24/):
三明治稳健σ/jackknife/归一化闭合差 三通道负 → P4-A b∈col(J_x) 能量占比 1.0 (机理形式化) →
P4-B 对抗解对 0.061px vs 2.39mm (构造性证明) → P4-D 双率对账 → 范围限定结论冻结。

## 7. V0.1 有效性与下一步

- 本规范: 研究草案, **单垂直实例**, 无有效性声明;
- 下一步: R5-A 真实试点 (协议已冻结 docs/measurement/r5_real_pilot_protocol.md) →
  依其结果修订 L1/L6 → 第二垂直实例 (货架空间测量) 启动前冻结 V0.2。
