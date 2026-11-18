# 参照照片溯源（ADR-011 数据治理）

## reference_photo.jpg

| 项 | 值 |
|---|---|
| 来源 | Wikimedia Commons: [File:20111019-FNS-RBN-1752 - Flickr - USDAgov.jpg](https://commons.wikimedia.org/wiki/File:20111019-FNS-RBN-1752_-_Flickr_-_USDAgov.jpg) |
| 内容 | 美国弗吉尼亚州 Arlington Washington-Lee 高校午餐供奶的单份屋顶包（巧克力奶），National School Lunch Program 场景。Commons 分类含 "Gable-top food and drink cartons / Milk cartons / School milk" |
| 作者 | U.S. Department of Agriculture（USDA Flickr 流） |
| 许可 | **Public domain**（PD USDA，美国政府作品，无需署名；保留本台账作为良好实践） |
| 拍摄 | 2011-10-19，Nikon D2X，2100×1500px |
| 入库处理 | 原图重编码 JPEG q90（2100×1500 → 1001KB），未裁切/未调几何 |
| SHA-256 | `6dc5c7f5c7d99030…`（全量见 qa-report.json photo 字段） |

## 商标声明

照片为公版实拍场景，盒面可能含第三方乳品商标像素。本照片**仅作几何参照证据**（G01 证据门），不参与任何输出刀版的图形复刻；输出刀版使用虚构 TOPPRISM 印刷图案。

## 用途边界

该照片的几何参数**不自动提取**（M1 中照片为参照证据，参数来自 `spec.json` 的实测/推导向导输入）。
TDE 合成数据的 Real Golden Set 将另按 `docs/tde-spec.md` §Real Golden Set 协议采集与冻结。
