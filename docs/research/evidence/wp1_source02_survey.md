# WP1-SOURCE-02 公共真实商品参考资产调查报告 v1.0

日期: 2026-11-28 | 授权: R20 (IMMEDIATE, P0, 时间盒 2 工作日) | 状态: 调查完成 (SOURCE-01..07 全交付)

## SOURCE-01 YCB 食品包装资产清单 (10 件, 全部带毫米级规格+质量+3D 网格)

官方物品清单 PDF (ycbbenchmarks.com/wp-content/uploads/2015/09/object-list-Sheet1.pdf) 食品类包装物品:

| # | 物品 | 质量 | 尺寸 mm | 结构家族映射 |
|---|---|---|---|---|
| 1 | Cheez-it Cracker box | 411g | 60×158×210 | box |
| 2 | Domino Sugar box | 514g | 38×89×175 | box |
| 3 | Jell-O Chocolate Pudding box | 187g | 35×110×89 | box |
| 4 | Jell-O Strawberry Gelatin box | 97g | 28×85×73 | box |
| 5 | Spam Potted Meat can | 370g | 50×97×82 | can |
| 6 | Master Chef Coffee can | 414g | Ø102×139 | can |
| 7 | Starkist Tuna Fish can | 171g | Ø85×33 | can |
| 8 | Pringles Chips can | 205g | Ø75×250 | can |
| 9 | French's Mustard bottle | 603g | 50×85×175 | bottle |
| 10 | Tomato Soup can | 349g | Ø66×101 | can |

每件配套: 官方 3D 网格 (mesh+纹理) + 600 RGBD 图 + 点云 (S3 公开下载), 尺寸/质量由官方 PDF 独立发布 → **独立参考真值完备** (SRC-G04 满足)。

## SOURCE-02 GS1/GDSN 公开规格源调查

| 通道 | 访问方式 | 批量可用性 | 结论 |
|---|---|---|---|
| Verified by GS1 | 按 GTIN 逐条查询 (需账号) | 非批量 | 仅作单件核验权威 |
| GS1 US Data Hub API | 商业订阅 + API key | 付费 | 非免费公共池 |
| GDSN datapool | B2B 会员订阅 | 付费 | 非免费公共池 |

**结论: GS1/GDSN 无免费批量公共访问 → 不能作抽样母体; 可作特定 GTIN 尺寸的第三方核验权威。**

## SOURCE-03 KITchen 及真实扫描数据集调查

- **KITchen** (KIT, arXiv:2403.16238): 111 厨房物体 (选自 YCB + KIT object models + KIT bimanual), 205K RGBD, 6D 位姿标注; 数据许可 GPL-3.0; 物体与 YCB 重叠显著 → 增量独特包装件估计 10-30 件
- **KIT object models database** (2012, IJRR): 100+ CAD 模型, 多数为厨房食品杂货 (groceries) → 潜在增量包装件来源
- **Google Scanned Objects (GSO)**: 1,030 件 3D 扫描家庭物品, CC-BY 4.0 (HF: hugging-3d/gso-objects, codepawl/scanned-objects-glb 均标 cc-by-4.0); 含罐/盒/瓶类; 食品包装子集需逐件枚举 (估 50-150 件)
- **MetaFood3D**: 食品 3D + 营养值; 许可=仅非商业研究 → 商用排除

## SOURCE-04 许可与商用限制核验

| 数据源 | 许可 | RWI 企业研发用途 | 处置 |
|---|---|---|---|
| YCB | MIT 型宽松许可 (官方仓库 ycb-LICENSE.txt) | 允许 (保留版权声明) | **可用** |
| GSO | CC-BY 4.0 | 允许 (署名) | **可用** |
| KITchen / KIT | GPL-3.0 | 衍生物传染性待法务复核 | 待核验后再用 |
| SKU-110K | 学术/非商业 (官方明确) | 不允许商用 | 仅限 WP1-IMG-01 研究线 |
| MetaFood3D | 非商业研究 | 不允许 | 排除 |
| GS1/GDSN | 商业订阅 | 付费可用 | 核验权威, 非母体 |

## SOURCE-05 与 9,386 冻结发行集的身份重叠核验方案

- 冻结集 = 参数化自产通用资产 (77 家族, **零真实品牌、零 GTIN**)
- YCB/GSO/KIT 物品 = 真实带牌商品 (Cheez-it/Pringles 等)
- **身份级重叠 = 0** (可证明: 冻结集无 GTIN/品牌字段, 与真实商品身份空间不相交) → SRC-G02 未见性可满足
- 家族级重叠 = 有 (box/can/bottle 映射到冻结集家族) — 属设计预期, 与身份未见性不冲突, 公开登记

## SOURCE-06 YCB 10 件逐字段证据完备性检查 (SRC-G01..G06 硬门禁)

| 门禁 | 10 件 YCB 包装 | 依据 |
|---|---|---|
| SRC-G01 来源可追溯 | PASS ×10 | 官方编号物品清单 + 版本记录 (YCB-Versions.pdf) |
| SRC-G02 身份唯一+未见性 | PASS ×10 | 品牌+品名唯一; 与冻结集身份空间不相交 |
| SRC-G03 编译输入契约 | PASS ×10 | 家族+mm 规格+质量齐备 (上表) |
| SRC-G04 独立参考证据 | PASS ×10 | 官方 PDF 规格 + 3D 网格 + RGBD |
| SRC-G05 许可符合用途 | PASS ×10 | MIT 型宽松许可 |
| SRC-G06 独立持样/抽样/冻结/揭盲 | PASS ×10 | 官方物品集固定编号, 抽样协议可先冻后抽 |

**10/10 全部六门禁 PASS。**

## SOURCE-07 能否形成 100 件合格样本池 — 量化结论

| 层级 | 数量 | 资格状态 |
|---|---|---|
| YCB 食品包装 (全六门禁) | **10** | 立即合格 |
| GSO 食品包装子集 (CC-BY, 待逐件枚举) | 估计 50-150 | 待枚举审计 |
| KIT/KITchen 增量杂货 (GPL, 待法务) | 估计 10-30 | 待法务+审计 |
| **多源联合合格池 (中性估计)** | **60-150** | 待 GSO 枚举后定 |

**量化结论**: 100 件合格池 = **有条件可行** (多源联合; 单 YCB 仅 10 件不足)。建议:
1. **Pilot-10 先行**: YCB 10 件全六门禁立即合格, 直接构成首批正式 Pilot 样本 (协议先冻后抽)
2. GSO 子集枚举审计 (第二工作项, 预计将池扩至 60-160)
3. KIT/KITchen 待 GPL 法务复核后决定纳入
4. GS1/GDSN 保留为单件核验权威
5. **战略副产物** (R20 §二建议): YCB 官方网格 = 真实扫描参照, 与我方"同规格参数化直出"构成 **真实扫描资产 vs 参数化资产统一规格对照研究** 的完美素材 (同 mm 规格: 官方网格为参照真值, 我方编译为受测对象)

## 偏差登记

- GSO 食品包装子集数量为估计值 (50-150), 逐件枚举未执行 (时间盒内仅完成渠道级调查)
- KIT GPL 法务复核未执行
- YCB 许可核验基于官方仓库 LICENSE 副本, 下载时需再次核对随包许可
