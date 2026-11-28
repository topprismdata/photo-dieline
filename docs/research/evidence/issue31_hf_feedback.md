# #31 HF Dataset Issue 反馈文本 (R27 授权, 措辞遵 R28 限定)

数据集: huggingface.co/datasets/hugging-3d/gso-objects
对象 ID: Granimals_20_Wooden_ABC_Blocks_Wagon_g2TinmUGGHI

## 标题 (依 R28 建议措辞)
Preview image mismatch for Granimals Wooden ABC object

## 正文 (限定措辞版)

We found a preview/asset identity inconsistency for object `Granimals_20_Wooden_ABC_Blocks_Wagon_g2TinmUGGHI` in the catalog (revision @main, catalog.parquet sha256 recorded in our governance ledger).

**Observed**: The catalog entry's name and description are "Granimals 20 Wooden ABC Blocks & Wagon 18+ months" with size ~19.0 × 5.07 × 6.35 cm, but:
- `previews/Granimals_20_Wooden_ABC_Blocks_Wagon_g2TinmUGGHI.webp` renders as a butterfly can opener
- `previews/Granimals_20_Wooden_ABC_Blocks_Wagon_g2TinmUGGHI.glb` (858,792 bytes, sha256-prefix fd84fbf923b02ef4, 12,336 faces, single mesh) renders as the same butterfly can opener geometry

**Evidence hashes** (sha256 prefix):
- webp: 6637f72acef042ca (verified identical between two independent downloads)
- glb: fd84fbf923b02ef4
- Scene texture reference: catalog.parquet mesh path points to this same preview GLB

**Reproduction**: Download the two preview files for the object ID above and render/inspect.

**Note**: Per governance discipline we do not assert the cause (thumbnail generation vs asset ingestion mismatch); we only report the confirmed mismatch between the catalog metadata (toy blocks & wagon) and the actual preview geometry (can opener). In our downstream usage this object is quarantined as IDENTITY-mismatched.

## 状态
- 文本已按 R27/R28 限定措辞定稿 (不断言上游算法成因; 附完整 ID/哈希/复现步骤)
- 提交通道: HF 账号未配置 → 待账号或由用户代发; 非阻塞 (R28 授权)
