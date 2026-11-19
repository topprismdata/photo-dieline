# 公开数据集台账（实拍验证轨道 · ADR-011）

用途：以公开实拍数据验证模板动物园的品类覆盖与逆向-孪生-对比闭环。
原则：只取许可可再分发/可溯源的数据；大文件不入库（manifest 存源 URL 可复取）；客户品牌素材零容忍。

## 已接入

### Open Images V6 (OID) — 测试集真值框

| 项 | 值 |
|---|---|
| 来源 | Google Open Images v6，`storage.googleapis.com/openimages/`（免注册直链） |
| 许可 | 图像 CC-BY 2.0（Flickr 原作者署名，ImageID 溯源）；标注 CC-BY 4.0 |
| 体量 | test 625,282 真值框（52MB CSV）；train 1.46 万亿? 级（1.7GB，流式过滤） |
| 品类对账（test 集包装相关） | Bottle 979 · Juice 512 · Box 256 · Milk 39 · **Carton 0（只在 train 标注）** |
| 收割 v1 | 94 裁切件（Juice25/Box25/Bottle25/Milk19）→ **独立评审否决作几何正样本（2/10）**：OID 语义类 ≠ 包装实体（Milk 类含倒奶/杯装），多实例/陈列场景/截断混入 |
| 证据分级 | 降级为 **G2/G3 候选**（检测/分割用途）；几何正样本需按下方 G0-G4 协议重筛 |

## REAL_PHOTO 分级协议（GPT 评审冻结，2026-11-19）

| 级 | 定义 | 用途 |
|---|---|---|
| **G0** | 完整单包装 + ≥2 外表面可辨 + 结构清楚 | 几何逆向主验证集 |
| G1 | 单包装完整，仅正面/轻微侧面 | 外观、局部几何 |
| G2 | 单包装存在，遮挡/截断 | 检测、分割、局部特征 |
| G3 | 多实例/陈列场景 | 场景理解 |
| G4 | 内容物/非包装（液体、杯装） | 负样本 |

附加属性 `package_structure_type`（与 OID 语义类解耦）：gable_top / folding_carton / corrugated_box / rigid_box / plastic_bottle / glass_bottle / other。

**方向性结论（评审原文）**：需要"包装实例数据集"，不是"含包装语义的数据集"。

### ABO (Amazon Berkeley Objects) — 已接入 v1

| 项 | 值 |
|---|---|
| 来源 | `amazon-berkeley-objects.s3.amazonaws.com`（免注册直链） |
| 许可 | CC-BY 4.0 |
| 体量 | 147,702 产品；listings 10 分片已拉全（92,320 条筛入）；images-small.tar 3.25GB（本地） |
| 候选池 | 378 条（名称关键词 + item_dimensions 完整 2-80in）；结构粗分：corrugated_box 148 · folding_box 43 · bottle_jug 32 · gable_or_carton 5 · other 150 |
| 样本 | 37 棚拍件入库（`output/datasets/abo_pack/`，G0_CANDIDATE） |
| 独立评审 | **ACCEPT-WITH-FILTERS 5.5/10**（OID 2/10 → ABO 5.5/10）；01/05/07/08 保留；商品本体冒充包装/误标/展开结构混用问题记录 |

### 30 件 Benchmark 规格（评审冻结，数据轨验收合同）

5 结构类型 × 6 件：传统屋顶包 6 · 砖形复合纸盒 6 · 普通折叠纸盒(天地盖/插舌/锁底) 6 · 瓦楞纸箱 6 · 塑料瓶 6。
每件：≥3 方位实拍 + 官方尺寸及定义 + 单实例分割 + ≥1 组独立可核验几何 + 参数化孪生 + 配准误差报告。
另建 `DIELINE_REFERENCE` 子集（展开纸板结构照，研究刀版拓扑↔折叠结果关系）。

### 四项量化验收指标（评审冻结）

| 指标 | 对象 | 输出 |
|---|---|---|
| 尺寸误差 | L/W/H vs 官方 | mm + 相对% |
| 轮廓误差 | 实拍轮廓 vs 渲染轮廓 | IoU + Chamfer |
| 表面几何误差 | 重建 vs 独立扫描/GT | 平均距离 + P95 |
| 拓扑正确性 | 面板/折线/连接 | 结构检查 |

已知缺口：①官方尺寸定义(本体vs零售包装/方向/精度) ②相机标定(内参+畸变+多视角) ③独立几何GT(防"轮廓对但折叠错"假通过) ④ABO 结构类型细分(gable_top_classic / gable_top_screw_cap / aseptic_brick_carton / folding_carton / corrugated_box)。

### SKU-110K — 记录未接入

Trax Retail 密集货架数据（11,762 图 / 1.7M 框）。**需注册表单申请**，未下载。
定位：密集检测基线（仓库另有 14_sku110k_baseline.py 历史）；对本仓模板几何验证价值低（无单盒实例 mask），保持记录。

## 证据分级定义（本轮冻结）

| 级 | 含义 |
|---|---|
| REAL_PHOTO | 公开实拍单实例（OID 收割件），可跑照片-对齐闭环 |
| VERIFIED_SOURCE | 公开标称刀版/尺寸表（如 US 半品脱 57.15×57.15×95.25mm） |
| DERIVED | 由总高/板厚等推算 |
| DEFAULTED | 模板典型值 |

## 100 类验证对账（进行中）

- 口径：`gate_green = G02-G10 全 PASS`（G01 照片门按上表分级单列）
- 基建：模板契约注册表 + `photo-dieline batch`（对账 JSON + contact sheet）
- 当前注册类数：见 `output/zoo100/batch_report.json`（19 → 家族代理扩容中）
- 目标：≥100 拓扑签名类，每类十门绿 + 渲染缩略 + 证据分级标注
