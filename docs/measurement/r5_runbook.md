# R5-A 执行手册 (Runbook) — 真实数据工作流可行性试验

> 协议: `r5_real_pilot_protocol.md` v0.1 + `v0.1-A` (参考锚点独立性) — 冻结, 修改走变更记录。
> 求解器基线: tag `r4-baseline`; 调参禁令 §4 适用。工具: `measurement/calibration.py`, `measurement/r5_ledger.py`。

## 0. 需要用户备置的实物 (P01)

| 组 | 采购示例 (任选其一) | 验证目标 |
|---|---|---|
| R01 | 任意长方体纸盒 (牛奶盒/手机盒) | 正常对照 |
| R02 | 屋顶包 (味全/雀巢/晨光 250–500mL) | 参数耦合 |
| R03 | 扁平装 (巧克力盒/茶包盒, 长宽比悬殊) | 弱可辨识 → 预期 MANUAL |
| R04 | 高反光/哑黑包装 (铝箔袋/深色礼盒) | 边缘定位误差 |
| R05 | 轻微磕碰/鼓胀/受潮变形的包装 | 模型失配行为 |

另备: 打印棋盘格 (9×6 内角, 10mm 方格, A4 实际尺寸勿缩放); 游标卡尺或直尺 (记录分辨率);
三脚架或固定支点; 卷尺 (量相机距离用, 非真值)。

## 1. 采集日流程 (P02/P03, 每实物约 15 分钟)

1. **session 开局**: 棋盘格拍 8–15 张 (多倾角/多距离), `calibration.calibrate()` 出内参;
   先跑 `calibration.selfcheck()` 确认标定链路 PASS 才算 session 有效 (正控制纪律);
2. **A 组视角**: 每实物 ≥3 视角, 方位圆跨度 ≥25° (`solve.capture_protocol_check` 过 OK),
   高度角 ≥10°; 拍后核对**关键面可见性清单** (每实物冻结必见面表);
3. **B 组对照**: 另拍 1 组近重复视角 (跨度 <25°, 预期 NEAR_DUP → MANUAL);
4. 每张记录: 设备/镜头/原图 (不裁剪不压缩), 原始文件名进 Observation.image。

## 2. 标注 (P04 独立性)

- 两名标注员**互不可见**对方采点; 各自按冻结角点定义图版独立标; 第三人仲裁;
- 2px 以上差值点强制仲裁并记录原因; 原始坐标不预处理, 直接入 `annotations[].points_raw`;
- 完成后各自填 `independent: true` (台账校验此字段)。

## 3. 参考测量 (P05 + v0.1-A)

- 真尺每边 **3 次重复**, 记仪器型号/分辨率; `r5_ledger.u_ref()` = 极差/√3;
- 每实物填 v0.1-A 九字段锚点记录 (`validate_anchor` 全过): anchor_id/方法/仪器/校准/值/
  u_ref/独立性/相关性/冲突裁决; 与图像采点共用尺或基准 → independence=shared_instrument
  且 correlation 必须写实;
- 结论措辞: 只许"与参考测量的一致性", 禁"精度 X mm" (§5)。

## 4. 求解与交付门

- Solver 字段: `git rev-parse HEAD` + 配置 + 种子 (与 r4-baseline 一致, 禁改阈值);
- 每视角跑冻结求解器 → `solve.capture_protocol_check` + `solve.delivery_policy`;
- 接受判定: `r5_ledger.compare()` — |测得−参考| ≤ max(1mm, 2·u_ref);
- 受控组 B–F 按 §6 单变量扰动执行, **与 A 组分开统计** (禁混为"真实精度"证据);
- 双率入账: `r5_ledger.dual_rate()` — R_auto 在零 AUTO 时为未定义, 禁记 0。

## 5. 收尾 (P07/P08)

- R03 类"合法但不可辨识"案例必须主动入账 (拒绝行为是能力);
- 产物核验: 由测量参数生成刀版 SVG/PDF 与实物折叠对照 (压线/粘口/鳍位);
- 全部 5 件 JSON 进 `r5/data/specimens/`, `python -m photo_dieline.measurement.r5_ledger r5/data/specimens` 出汇总。

## 6. 结论口径 (§9, 冻结)

5 件零失败 → 95% 单侧失败率上界 ≈45%: 只支持**工作流可行性**, 不支持任何可靠性声明。
可靠性量化属 R5-C 独立验收集。
