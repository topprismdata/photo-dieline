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
| 收割 | `output/datasets/oid_pack/`（本地，不入库）+ `MANIFEST.json`（入库：源 URL/许可/框坐标/裁切尺寸，每类 ≤25 例，面积占比 8-70%，非组框） |
| 证据分级 | **REAL_PHOTO**（真实商品实拍，多品牌像素——仅作几何/品类参照，不参与输出刀版复刻） |

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
