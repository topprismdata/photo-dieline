# photo-dieline 工程行为规范（PD-Guardrails 摘要，全文 docs/PD_GUARDRAILS.md）

任何 agent/开发者在仓内工作前必读。三级: L0 违规拒行 / L1 须提交证据 / L2 专家裁决。

## L0 硬约束（违反即停）
1. **单位契约**: 跨模块物理量必须显式单位; mm↔m 转换写具名函数并双向测试; 相机距离 0.01-10m、盒高 10-1000mm、填充率(0,1] 越界即 fail（特殊样本显式配置放宽，不许静默）。
2. **产物有效性**: 渲染"成功"= 文件存在 + 主体 bbox/面积/可分离度达标。禁用单一像素统计（std 等）判主体存在。
3. **结构不变量**: 家族锁定约束（如 H=Hf+D）参数扰动后必须机器复验; 失败回退原参数并写 FALLBACK 记录。
4. **数值稳定**: NaN/Inf/退化几何/空张量不得传入下游; 在生成边界检查，不靠最终渲染失败兜底。
5. **接口契约**: 禁用宽泛 except TypeError 兼容签名差异; 接口统一或显式 Adapter。

## L1 验证纪律（无证据不通过）
6. **独立评估**: 训练日志不作唯一证据。宣布"改善>10%/首达门槛/突破瓶颈"前，必须独立 eval 脚本读原始预测+原始标签, raw 单位, 保存逐样本误差。
7. **根因锁定**: 修 bug 前先做区分竞争根因的最小对照实验; 紧急止血必须标 UNCONFIRMED_FIX。
8. **数据语义**: 关键词匹配 ≠ 包装身份。入库前 vision 预审, 三字段分离 (object_category/package_identity/package_structure_type), source_label 与 reviewed_label 不可互覆。
9. **共享代码隐含行为**: 复用驱动/引擎时, 隐含参数（如 eye=d×1.35 margin）必须显式进入下游计算图, 并留存解析后配置快照。
10. **跑批改文件禁令**: 批处理运行中不得修改被批引用的脚本/配置; 先停批再改再重启。
11. **视觉与客观指标冲突时进人工复核**: vision 管语义结构, lapvar/边缘强度管图像质量, 互不越权。

## L2 评审原则
12. **结论强度 ≤ 证据强度**: 平台期≠信息极限; 经验误差带≠理论下界。结论标注 OBSERVED/REPRODUCED/SUPPORTED/CONFIRMED。
13. **统计分母完整**: 报告必须含全分母（SUCCESS/FALLBACK/SKIPPED/FAILED/INVALID）, 禁只报成功样本均值。
14. **可追溯**: 重要结论须能追溯到实验+原始数据+独立评审, 不存在于聊天记录即视为未确立。

## 机器门禁（.omp/constraints/rule-enforcer.json）
本仓的 L0/L1 事故类已有机器判据，已编译成 `.omp/constraints/rule-enforcer.json`，
由 OMP 运行时约束门执行：改受保护路径前必须跑对应 check，check 未过则写入被拦，
会话结束前未过 check 也不允许收尾。**不要绕过**：跑 check 就是跑测试本身。
- `CHK-GUARD` = `tests/test_pd_guard.py`（单位/产物/数值/家族锁定/刀版轮廓-strip-许可）
- `CHK-STRUCT` = `tests/test_m1.py`（IR schema/折叠闭合/SVG 物理层/PDF mediabox）
- `CHK-ALL` = 全量套件（蕴含前两者）
无机器判据的类（数据语义误标、跑批期间改文件、指标口径）仍以本文 L1 条款为准。

## 快速自检（提交/宣布前 30 秒）
- [ ] 数字有单位吗？换算双向测过吗？
- [ ] 指标是独立 eval 还是训练日志？
- [ ] "成功"的分母完整吗？FALLBACK 混进 SUCCESS 了吗？
- [ ] 根因是实验锁定的还是假设？
- [ ] 结论措辞超出证据了吗？
