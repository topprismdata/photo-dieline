# PhotoDieline 设计方案 V1.0（架构已冻结）

> 实物包装照片 → 印刷级 1:1 刀版图（dieline）的全开源管线。
> 设计经 GPT 三轮架构评审收敛（R1 总体方案 → R2 六项裁决+M1 冻结 → R3 TDE 孪生训练方向），
> 原始判决全文见 `docs/reviews/gpt_design_all_rounds.md`。

> **状态勘误（2026-11-24 从头复查，详见 [复查证据账](docs/reviews/recheck_2026-11-24/findings.md) 与 [优化清单](docs/reviews/recheck_2026-11-24/OPTIMIZATION_PLAN.md)）**：本文是冻结的架构设计；各节的*实现现状*与之有出入，以 README 的成熟度表为准。
> - §7 里程碑：M1 垂直切片在复查中发现导出件被平移出画布、PDF 语法错误，已修复并以手算金标与变异矩阵回放重验；M2 的 T1/T2 只有合成域结果，真实照片上未达可用；模板按成熟度分级（L2 1 / L1 83 / L0 16）。
> - §8 TDE：冻结规范的六维随机化在引擎里只落地了相机、光照、粗糙度三维；印刷随机化、ISP 退化链、环境均未实现。
> - §6/§10 门禁：原实现只有 8 道门且多道恒真；现为 10 道，含对导出件的独立解析核对与通用折叠扰动探针。板厚补偿仍未实现。
> - 路线裁决（GPT 复查评审第 1 轮）：学习线下一步是真实实物黄金集 + 参数化逆向拟合；CNN 直接回归暂停扩张；"原版复原"与"功能等价再设计"须分开定义验收；全局 0.5mm 不足以作制造验收，须按特征定义容差。


## 1. 北极星

**一张手机照片 + 少量实测尺寸 → 参数化制造几何（Geometry IR）→ 分层 1:1 SVG/PDF 刀版 → 折叠回包数值验证。**

不承诺"任意照片端到端生成可印刷刀版"；不确定就拒绝自动交付。

## 2. 主线裁决（ADR-001）

混合架构，**B 参数化重建为主干，A 视觉 3D 重建为辅证**：

- A（TRELLIS 3D→展开）单图无法同时保证外观/结构/尺寸/面板边界/折叠拓扑/可制造六项，不做 MVP 主路径。
- B（照片→识别箱型→量尺寸→参数化拓扑→刀版）只需识别结构+恢复少量关键尺寸即可构造制造几何。
- **A 提供视觉证据，B 负责制造几何。** 所有路线汇入同一 Geometry IR。

## 3. 系统架构

```
照片/尺寸/规格文字 ──► Evidence Layer (OCR/VLM/图像分析, 尺寸证据+置信度)
                          │
                          ▼
                   Package Classifier (箱型分类)
                    known ┌────────┴────────┐ unknown
                          ▼                  ▼
              Parametric Recon (主干)   Vision 3D 辅证 (TRELLIS, M3)
                          │                  │
                          └────────┬─────────┘
                                   ▼
                          Geometry IR  ◄─── 唯一制造几何协议
                          (meta/package/panels/edges/features)
                             │                    │
                 2D Layout(自研)              3D Folding(纯Python数值)
                   SVG/PDF 1:1                运动学+相交+闭合
                             │                    │
                             └────────┬─────────┘
                                      ▼
                              QA & Validation
                         (DRAFT / VALIDATED / PRINT-READY)
```

## 4. Geometry IR V0.1（冻结：5 个顶层对象）

| 字段 | 类型 | 语义 |
|---|---|---|
| `meta` | object | IR 版本、单位、坐标系、来源 |
| `package` | object | 箱型、整体尺寸、材料、模板身份 |
| `panels` | array | 面板 2D 轮廓 + 3D 参考几何 + 语义角色 |
| `edges` | array | 面板连接、折叠语义（MOUNTAIN/VALLEY/SCORE/CUT/PERFORATION）|
| `features` | array | 粘口、开窗、提手、出血、套准标记 |

- 不设 cuts/folds/glue/bleed 独立顶层数组：折线入 `edges`，制造特征入 `features`。
- 坐标一律浮点 mm；证据为参数附属属性，状态五级：`MEASURED / VERIFIED_SOURCE / DERIVED / INFERRED / DEFAULTED`。
- Schema 落 `schemas/geometry-ir.schema.json`（M1 D1-2 交付）。

## 5. 尺寸标定协议（ADR-003）

每箱型定义"最小必需参数"集。精度阶梯：MVP ≤0.5mm（golden 基准）→ P1 ≤0.25mm → 交付按印厂公差。
**模型回归值 = INFERRED，永远不能覆盖 MEASURED。**

## 6. QA 门（三态：DRAFT / VALIDATED / PRINT-READY）

MVP P0 硬门（16 项验收合同见 §10）：1:1 物理尺寸、50mm 校验条（PDF MediaBox 实测）、CUT/SCORE 分层语义、
闭合轮廓、非流形拒绝、面板边界闭合、折叠回包（数值判据非渲染图）、尺寸闭合、粘口出血、面板数对账。
照片对齐/纸板利用率/纹理方向 → P1。**刀版周长 ≠ 纸板利用率。**

## 7. 里程碑（TDE 插入后重排）

| 阶段 | 内容 | 验收 |
|---|---|---|
| **M1**（两周垂直切片，已冻结） | gable-top 屋顶包 Golden Sample：照片+实测尺寸 → IR → 自研 2D Layout → 分层 SVG/PDF → 纯 Python 折叠 QA | 原 16 项全过；无 TRELLIS/DielineForge/母仓依赖 |
| M2-A | 模板库扩展（FEFCO 0201 / gable 完善 / Template Contract） | 多模板统一 IR |
| M2-B | **Twins Data Engine**：参数域采样→3D→Blender 域随机化渲染→(照片, 类型, 参数真值, IR, 刀版) 自动配对 | 数据可追溯（来源/许可/版本） |
| M2-C | Real Golden Set（200-300 张真实实物照，训练前冻结+哈希） | 独立测试集 |
| M2-D | T1 箱型分类（含 UNKNOWN 拒识） | Real Macro-F1 ≥0.90 |
| M2-E | T2 参数回归（类型条件化+预测区间） | 关键尺寸 MAE ≤1.0mm, P90 ≤2.0mm |
| M3-A/B/C | TRELLIS 视觉辅证 / 智能交互补参 / T3 端到端研究 | 模型不接管制造几何 |

M2-B 可用 M1 的 gable 模板先行；M2-C 真实基准集必须先冻结再训练。

## 8. Twins Data Engine（本轮新增主线，ADR-009/010/011）

**数据飞轮：参数化模板生成真值 → 真值规模化孪生数据 → 模型学习 → 真实照片识别 → 参数化几何重建 → 制造 QA。**

- 结构来源三路：自有参数化模板（GO，最高可信 Ground Truth）；Sketchfab CC 资产（CONDITIONAL，逐资产核许可）；
  PackBox/DieCutStudio 输出（CONDITIONAL，先核输出版权）。
- 每样本携带 `source_type/source_uri/source_license/derivative_status/redistribution_allowed/dataset_split/generator_version`。
- 域随机化三档分报：REALISTIC / MODERATE / STRESS（随机化强度 ≠ 泛化）。
- Sim2Real 三实验：A 纯合成基线 → B 随机化消融 → C 合成+真实微调；Real Golden Test 永不参与训练/调参。
- 合成数量 ≠ 独立信息量：按参数空间/结构变体/制造边界衡量覆盖度。
完整冻结规范（六维随机化三档参数表 / CaptureProfile 联合采样 / 结构多样性判据 / T2 基线 / MVE 两周实验 / 文献映射）见 **[docs/tde-spec.md](docs/tde-spec.md)**（GPT 第四轮冻结版）。

## 9. 技术栈

Python + NumPy/Shapely（2D 几何）+ Trimesh（网格/相交）+ JSON Schema + pypdf + Typer CLI + pytest；
Blender headless 仅本地可视化（L2，不进 CI）；TRELLIS.2 可选依赖（不装也能跑全管线）；
T1/T2 训练沿用母仓 SDG→YOLO 微调方法论但加结构约束标签。

## 10. M1 验收合同（16 项，机器判定优先）

输入：真实照片读取/尺寸 mm 输入/证据状态记录 · 几何：IR Schema 合法/拓扑闭合/折线语义/基准误差≤0.5mm ·
刀版：1:1 SVG/PDF/50mm 校验条/分层结构 · 3D：折叠闭合残差/无穿插 · QA：JSON 报告 ·
工程：无 TRELLIS 可跑/许可隔离清单。

## 11. 工程纪律

- 与母仓 `openusd-retail-twin` 完全独立（无 submodule/import/复制，仅 README 互链；模板按公开几何规则重写）。
- CI 三层：L0 单元（PR 阻断）/ L1 集成含 SVG/PDF+折叠运动学（PR 阻断）/ L2 Blender 渲染（Release 签核，不入库）。
- DielineForge（GPL-3.0）整体移至 M3 评估，届时独立进程隔离+许可证审查；M1/M2 主链无 GPL。
- VALIDATED 不得自动升级 PRINT-READY；印厂签核为人工门。
