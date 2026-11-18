# Architecture Decision Records

GPT 三轮评审通过的 11 项架构决策（R1→ADR-001..008，R2 六裁决并入，R3→ADR-009..011）。原文见 `../reviews/gpt_design_all_rounds.md`。

| ADR | 决策 | 状态 | 轮次 |
|---|---|---|---|
| ADR-001 | 参数化重建为主，视觉重建为辅（A 供视觉证据，B 产制造几何） | APPROVE | R1 |
| ADR-002 | Geometry IR 为唯一制造几何协议；SVG/PDF/3D 均由 IR 派生 | APPROVE | R1 |
| ADR-003 | 真实尺寸优先，视觉推断不能替代实测；证据五级状态 | APPROVE | R1 |
| ADR-004 | TRELLIS.2 为可选独立能力，非强制依赖 | APPROVE | R1 |
| ADR-005 | DielineForge 移至 M3 独立 CLI 评估（GPL 边界后移；M1/M2 自研直出） | APPROVE（法律审查留 M3） | R1+R2 |
| ADR-006 | M1 先做一个完整模板的垂直切片（gable-top），不贪多 | APPROVE | R1 |
| ADR-007 | 折叠验证纯 Python（NumPy 运动学+Shapely/Trimesh 相交）；Blender 仅可视化不进验收门 | APPROVE | R2 |
| ADR-008 | VALIDATED 与 PRINT-READY 分离；印厂签核为人工门 | APPROVE | R1 |
| ADR-009 | Learning-to-Parameter, Not Learning-to-Manufacture：模型只输出类型+参数（INFERRED），制造几何永远由模板+Geometry Kernel 生成 | APPROVE | R3 |
| ADR-010 | Synthetic-to-Real 评估协议：Real Golden Set 训练前冻结，三实验（纯合成/随机化消融/混合微调），三档随机化分报 | APPROVE | R3 |
| ADR-011 | Dataset Provenance & Licensing：每样本来源/许可/衍生/再分发元数据；CC 资产逐件核验后才可入公开数据包 | APPROVE | R3 |

## 附：R2 其余冻结项

- Geometry IR V0.1 顶层 = `meta/package/panels/edges/features` 五对象。
- 与母仓完全独立（Repository Independence）：CI 仅 checkout 本仓可跑全管线。
- CI 三层：L0 单元 / L1 集成（PR 阻断）；L2 Blender 渲染（Release 人工签核）。
- 仓库名终审：`photo-dieline`（弃 `dieline-kit`，辨识度弱）。
