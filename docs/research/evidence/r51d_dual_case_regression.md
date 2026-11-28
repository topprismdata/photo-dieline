# R51-D: 双案例回归 + R51-E 时间维度契约

日期: 2026-11-28 | 协议: WP-L3-02-DOC (R51)

## R51-D 回归结果

| 案例 | 期望 (预冻结) | 实际 | 一致 |
|---|---|---|---|
| Case 1 金典 250ml | 正确保持 UNRESOLVED (EVIDENCE_INSUFFICIENT) | l3_binding_contract_v1.json binding_status=UNRESOLVED 未变; r50a 冻结文件未动 | ✓ |
| Case 2 Coke 330ml | 按证据判定 | r51c: MISMATCH → CANDIDATE_REJECTED (三轴超差, 预冻结容差) | ✓ |

机制在两分支正确分派: 证据不足→UNRESOLVED; 证据充分但超差→CANDIDATE_REJECTED。
回归方法: 直读契约 JSON 当前值 + git 工作区未改动核对 (零覆盖红线)。

## R51-E 时间维度契约 (设计, P1)

### 版本绑定与失效触发

1. **版本字段绑定**: 每条 evidence 记录必须携带 package_version_ref (如 "Version 1.0, Changed 2023-12-19") 与 retrieved_at
2. **失效触发器** (任一触发即证据失效, 绑定回 UNRESOLVED 待重验):
   - source 版本变更: 规格表 Version bump / Changed 日期晚于已登记值
   - 快照漂移: 重取快照 sha256 ≠ 已登记 source_snapshot_sha256
   - 来源下架/404: source_uri 不可达且无替代登记源
3. **分任务重验规则** (失效后只重验受影响字段):
   - 身份类字段 (品牌/GTIN/型号) → 重验 BIND-G01
   - 尺寸类字段 → 重验 BIND-G03 (可计算性) + G04 (按当前冻结容差重新判定)
   - 判定枚举状态 → 全链 G01..05 重走
4. **追加不覆盖**: 重验结果 append-only 进证据台账 (新 evidence_id, 旧记录保留失效标记, 永不删除)
5. **有效期声明**: retrieved_at + valid_until (默认绑定至 spec Changed 时间被超越为止); valid_until 过期 → 证据降级为 STALE, 不可用于新判定
