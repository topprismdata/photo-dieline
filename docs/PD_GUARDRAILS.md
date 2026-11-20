# PD-Guardrails v1（工程行为规范，GPT 立项判决 APPROVE WITH REVISIONS）

来源: 2026-11-20 关键节点审计（GPT 评审，docs/reviews/gpt_progress_review_2026-11-20.md 同会话续）
核心原则: **能被机器确定性证伪的，不依赖人的记忆；只能通过实验或专家判断的，不伪装成自动化门禁。**

## 三级治理

| 级 | 机制 | 例子 |
|---|---|---|
| L0 硬约束 | 命令证伪，违规拒行 | 单位断言、空产物、结构不变量、NaN |
| L1 验证纪律 | 必须提交可复核证据 | 独立 raw eval、根因实验、数据语义审核 |
| L2 评审原则 | 专家裁决 | 结论强度、架构取舍、制造适用性 |

## 规范目录（A-E 事故项 + GPT 补 F-M 八组）

- A 数值与口径: A1 单位契约(跨模块物理量显式单位+范围断言, mm↔m 双向测试) / A2 重大指标(>10%改善、首达门槛、宣布突破)必须独立 raw eval / A3 指标口径显式(分母、反归一化、逐样本保存)
- B 质检: B1 禁止单一像素统计判主体存在 / B2 vision 管语义、lapvar 管质量、冲突进人工复核 / B3 产物有效性≠存在性(主体 bbox/面积/可分离度)
- C 根因: C1 修复前必须有区分竞争根因的对照实验;紧急止血标 UNCONFIRMED_FIX / C2 结论五级: OBSERVED<REPRODUCED<SUPPORTED<CONFIRMED<UNKNOWN
- D 数据: D1 三字段分离 object_category/package_identity/package_structure_type + source_label/reviewed_label 不可互覆
- E 复用: E1 驱动隐含参数显式入配置(CameraFitConfig)+快照 / E2 禁宽泛 except TypeError(接口统一+Adapter) / E3 家族不变量机器验证, 回退必须留痕 FALLBACK≠SUCCESS
- F 数据泄漏(P0 新增): physical_object_id/geometry_instance_id 不跨集; 尺寸泛化与结构泛化分开报
- G 实验追溯(P0): run_id 绑 commit/config hash/data hash/seed/checkpoint; 产物不可覆盖
- H 统计分母(P0): 禁只报成功样本均值; SUCCESS/FALLBACK/SKIPPED/FAILED/INVALID 全分母
- I 摄影测量(P0): 坐标系显式声明; 内外参绑定图像版本; 投影往返数值测试
- J 制造完整性(P0): 网格合法≠结构合法; 折叠成功≠刀版合格(CUT/CREASE 语义/闭合轮廓/物理尺寸); 50mm 物理校验条
- K 数值稳定(P0): NaN/Inf/退化几何不入下游
- L 多视角(P1): 实例身份+配准几何一致性, 像素误差≠几何精度
- M 许可治理(P1): 来源/许可/审查状态逐资产登记

## 事故→规则映射（组织学习闭环）

| 事故 | 规则 | 状态 |
|---|---|---|
| d_fill×1000 相机 85m 外 | A1 | R1 |
| 0.11% 假精度 | A2/A3 | R1(已修正) |
| std 假检测器 | B1 | R1 |
| 空场景有图 | B3 | R1 |
| 相机假说误修 | C1 | R1 |
| 4-9% 过度归因 | C2 | R1(已改口径) |
| 关键词误标 44%/Milk 全灭 | D1 | R2(已实证) |
| eye=1.35d 隐含参数 | E1 | R1 |
| build_ir 签名 | E2 | R1 |
| H=Hf+D 破坏 | E3 | R1(已容错+留痕) |

## 实施三轮（GPT 裁定）

- R1 基础硬门禁(1-2 周): A1/A2/A3/B3/E1/E3/K/G → pd-guard 命令形态
- R2 数据与研究纪律(2-3 周): D/F/H/B1/B2/C
- R3 全链路(2-4 周): I/J/L/M + CI Release Gate

## GA 门槛（规范自身须验收）

1. 历史事故能被对应测试重新触发 2. 违规可靠阻断而非 warning 3. 合法样本不误拦 4. 豁免有审计记录 5. CI 独立报告每规则状态

判决全文: docs/reviews/（本会话归档）
