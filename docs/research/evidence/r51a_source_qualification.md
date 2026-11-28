# R51-A: 来源资格复核 (Erudus 规格 PDF 逐字段)

日期: 2026-11-28 | 快照: l3_doc_snapshots/coke_erudus_ct0021.pdf (184039 bytes)
SHA256: f2aada8c8a76e2af… (完整值见 ev_doc_005_coke_posctrl.json)

## 原文逐字段 (PDF 文本提取, 非转述)

| 字段 | 原文 | 备注 |
|---|---|---|
| 产品名 | Coca-Cola Original Taste 330ml x24 Can | 单件=330ml 罐, 外箱 24 件 |
| Brand | Coca-Cola | |
| Manufacturer Product Code | 407477 | |
| Erudus ID | 5bf60cc1f61c4ba2a46c8ecbf18e7eca | |
| Specification Type | Legacy | |
| **Inner Component GTIN** | **05449000000996** | **单件口径 GTIN — 身份字段较 R50 登记升级** |
| Outer Case GTIN | 05017726180034 | 整箱口径, 按 R48 纪律不混用 |
| Version | 1.0 | |
| Status | Published | |
| Changed | Dec 19, 2023 08:54 | ⚠ 更正: R50 送审词中"2025-07-31"是 PDF 渲染页脚日期, 规格变更日期=2023-12-19 |
| Inner Component Weight | 0.36 kg | 单件质量声明 |
| **单件尺寸原文** | "PRODUCT DIMENSIONS Inner Component Inner Component Depth 67 mm Inner Component Width 67 mm Inner Component Height 116 mm" | Inner Component/Outer Case 显式分列 |
| Outer Case 尺寸 | 404 × 271 × 118 mm | 仅登记, 不参与单件对照 |

## 资格复核裁决 (BIND-G01 输入)

- 商品身份: ✓ (Brand + 产品名 + 单件 GTIN 05449000000996)
- 声明主体: ⚠ 附注合格 — PDF 无供应商法人名称字段 (仅 Brand + Manufacturer Product Code); 声明主体 = Erudus 平台厂商提交规格表 (第三方平台托管, 厂商提交机制), 托管层级如实登记, 独立厂商官网佐证未取得
- 版本与单件尺寸语义: ✓ (Version 1.0 + Published + Inner Component 显式口径)
- 更正记录: package_version_ref 由 "Version 1.0 (2025-07-31)" 更正为 "Version 1.0, Changed 2023-12-19" (EV-DOC-005 同步修订)

GTIN 05449000000996 登记状态: UNVERIFIED (GS1 Verified 服务需客户端渲染, 本轮未核验; 与金典案例同口径, 不扩大检索)
