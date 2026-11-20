# 10 件实物冻结采集协议（P0）

> 目的: 为 E2b 冻结测试与 Sim2Real 缺口实测提供真实 GT。所有合成域数字(1.66%±0.06pp)的
> 真实域校准都依赖本批数据。**冻结纪律**: 采集后参数不再改, 所有实验共享同一批。
> 判决来源: docs/reviews/gpt_progress_review_2026-11-20.md

## 品类配额（10 件）

| # | 品类 | 数量 | 备注 |
|---|---|---|---|
| 1 | gable_top 屋顶包 | 3 | 优先: 利乐菱形屋顶包 250mL/500mL/1L 各一 |
| 2 | brick 砖形盒 | 2 | 利乐砖 250mL 与 500mL 各一 |
| 3 | folding_carton 折叠盒 | 2 | 食品级小盒(牙膏盒/茶盒级) |
| 4 | corrugated 瓦楞箱 | 2 | 快递箱/小家电箱, 含至少一个 E 瓦 |
| 5 | shaped 异形 | 1 | 异形瓶/软袋均可 |

## 每件必采数据

### A. 几何 GT（三选一, 优先级从高到低）
1. **刀版图**（品牌官网/包装展开/自制拆盒扫描）→ 交 `specs/<id>_dieline.{pdf,png}`
2. **游标卡尺/钢尺测量**: W/D/Hb/Hr/Ef(mm), 三次取中 → 填入 `specs/<id>_measurements.json`:
   ```json
   {"id": "gable_250_a", "family": "gable_top",
    "measurements": [{"name": "W", "value_mm": 45.0, "status": "MEASURED", "source": "卡尺, 三次取中"}]}
   ```
3. 只有卷尺: 允许, 但 status 标 "TAPE", 误差估计 ±1mm 记入 source

### B. 照片（每件 ≥6 张, 命名 `<id>_cam<k>.jpg`）
- **相机契约（I1/I2 强制）**: 记录每张的 焦距(35mm 等效)/俯仰/偏航/距离估计
  → `photos/<id>_cam<k>.json`（模板见下）
- 距离: 量相机到盒中心（卷尺即可, ±2cm）
- 角度网格: 俯仰 {5°, 20°, 35°} × 偏航 {-30°, 0°, +30°} 至少各一张（与 E3 合成网格同构, 便于缺口对比）
- **参照物强制**: 每张照片含**打印好的 50mm 校验条**（`scripts` 可从刀版 SVG 裁, 或直尺）放盒旁同平面
- 焦距: 手动固定(不使用广角端), 变焦记录等效值

### C. 环境记录
- 光照方向/类型（窗光/台灯/棚灯）, 背景（哑光纯色优先）
- 相机型号 + 是否三脚架

## 照片 JSON 模板（每张一份）

```json
{"image": "gable_250_a_cam1.jpg",
 "camera": {"equiv_focal_mm": 50, "pitch_deg": 20, "yaw_deg": 0, "distance_m": 0.35},
 "frame": "真实拍摄, 参照条 50mm 于盒旁同平面",
 "light": "窗光右侧", "background": "哑光灰板", "tripod": false}
```

## 交付结构

```
data/frozen10/
  specs/          # 每件: measurements.json (+ dieline 如有)
  photos/         # 每件 ≥6 组 (jpg+json 同名对)
  manifest.json   # 10 行: id/family/测量状态/照片数/缺失项
  CAPTURE_LOG.md  # 采集日期/环境/异常备注
```

## 验收门禁（采集完我来跑）

1. `pd-guard pairs --render-dir data/frozen10/photos` → 每张有 JSON+相机字段+frame 声明
2. 每件测量齐全（MEASURED/TAPE 标注）, 10 件全数
3. 参照条可见性抽查（裁局部 vision 读数）
4. 缺一项 → 该件标 INVALID, 不入 GT, 不静默补（H1 分母纪律）

## 时间预算

- 测量+拍摄: 每件 ~10 分钟, 共 ~2 小时
- 无需棚拍: 窗光+哑光背景即可（E3 网格本身含俯仰大角度, 假设就是非理想拍摄）
