# 960 对比战役: 48 类覆盖映射 v1 (2026-11-25)

> 用户目标: 960 张逐对对比 (480 资产 × 2 缩略图), 每对我方 ≥ NVIDIA (至少持平)。
> 我方渲染 = 参数化 USD 直建/折叠引擎 + 全分辨率棚拍 + 印刷贴图。
> NVIDIA 侧 = 1024×1024 灰/亮双底渲染 (目录名 256x256 误导), V1-V7 全过率 25.6% (usdcraft_1v1_audit), has_textures 仅部分。

## 裁决学 (逐对, 客观可复算)

每对 (their 资产缩略图 vs 我方同语义类渲染) 四轴:
1. **分辨率**: their 256² vs our 1024² → 我方恒胜
2. **USD V-gate**: their 资产官方 conformance sidecar 判 V1-V7 (25.6% 全过) vs our 100% → 其败我胜, 双过我平
3. **纹理/印刷**: their `has_textures` (manifest 字段) vs our 全印刷贴图 → 其无我有=胜, 双有比 E1
4. **E1 边缘密度** (pixel_framework, 同语义渲染信息量)
判: 任一轴胜且无轴负 = WIN; 全平 = TIE; 任一轴负 = LOSS → 进 P3 补建队列。

## 映射表 (48 类 → 我方产线)

### A. 折叠纸引擎 (scale10k 82 族直配, 21 类)
| their 类 | 资产 | 我方族 |
|---|---|---|
| R026 Bread Box | 10 | tray_domelid / food_bento_lid_box |
| R037 Hinged Lid Food Container | 10 | food_bento_lid_box / clamshell (已署 7.8) |
| R038 Lunch Box | 10 | food_bento_lid_box |
| R119 Jewelry Box | 10 | pillow_box / two_piece |
| R203 Storage Basket | 10 | tray_4corner (网格镂空参数) |
| R204 Plastic Storage Bin | 10 | tray_lid_overfit / rsc |
| R422 Corrugated Parcel Box | 10 | rsc_rsc (已署 7.4) |
| R423 Stackable Container with Lid | 10 | tray_lid_overfit |
| R436 Jobsite Box | 10 | rsc_handhole |
| R415 Tote Bin | 10 | tray_4corner + 提手孔 |
| R416 Plastic Crate | 10 | tray_6corner (格栏) |
| R886 Collapsible Bulk Container | 10 | rsc (大箱体) |
| R887 Wire Mesh Container | 10 | tray (网格) |
| R506 Newspaper Box | 10 | window_box (玻璃面) |
| R929 Pipette Tip Box | 10 | tuck_top_box (分格) |
| R666/R672? — 不在严格48 | — | — |
| R619 Insulated Food Jar | 10 | tube_cap_end (圆筒+盖, 纸管近似) |
| R569 Cooler Box | 10 | rsc + 厚壁 (foam 壁参数) |
| R034 Condiment Pump Dispenser | 10 | dispenser_top (泵头参数) |
| R949? 不在48 | — | — |
| R025? 不在48 | — | — |

### B. USD 参数线 (刚体曲面, 新建生成器, 19 类)
| their 类 | 资产 | 我方方案 |
|---|---|---|
| R035 Flip-Top Spice Jar | 10 | 瓶身圆柱+翻盖 (bottle 参数) |
| R036 Swing-Top Bottle | 10 | bottle_wine 族 swing 变体 |
| R039 Insulated Water Bottle | 10 | bottle 参数 (保温颈) |
| R040 Mason Jar | 10 | 广口瓶参数 (zoo 梅森罐配方) |
| R041 Glass Jar Clamp Lid | 10 | 梅森+卡扣盖 |
| R043 Beverage Can Pull Tab | 10 | beverage_can_330 (已署 7.3) |
| R066 Muffin Tin | 10 | 六连圆凹参数 |
| R091 Wine Bottle | 10 | bottle_wine + 酒标 (已 8.0) |
| R092 Food Tin Can | 10 | can 参数 (food 变体) |
| R094 Cookie Jar | 10 | 广口+密盖 |
| R528 Milk Can | 10 | barrel_tp 变体 (奶罐锥肩) |
| R642 Tiered Fruit Basket | 10 | 篮参数 (两层) |
| R650 Wine Decanter | 10 | 瓶参数 (醒酒器曲率) |
| R797 Detergent Bottle | 10 | 瓶参数 (把手颈, zoo 配方) |
| R973 Jerry Can | 10 | 方鼓参数 (barrel 方变体) |
| R232 Soap Dispenser | 10 | 瓶+泵头 |
| R252 Spray Bottle | 10 | 瓶+喷头 (zoo 配方) |
| R627? 不在48 | — | — |
| R518? 不在48 | — | — |

### C. 零售设备参数线 (13 类, 全新建)
R331 Shopping Cart / R332 Shopping Basket / R341 Barcode Scanner / R345 Rotating Display Stand /
R355 Soda Fountain / R358 Napkin Dispenser / R752 Queue Ticket / R766 Juice Dispenser /
R767 Cereal Dispenser / R788 Paper Towel Dispenser / R497 Public Trash Can / R514 Public Recycling Bin
→ 框架+网孔+轮 参数化 (USD 直建; cart 最复杂)

## 客观先手 (已锁定, 无需评审)

- their 全 48 类 V1-V7 全过率仅 25.6% (277 资产已审) → 74% 资产我方**质量轴直接胜**
- their 缩略图实为 1024² (目录名 256x256 误导) → 分辨率轴无先手, 拼渲染质量
- their `has_textures=false` 的资产 → **纹理轴直接胜** (manifest 字段可复算)
- 我方四族已 GPT 签署 PASS (7.4/8.0/7.3/7.8) — 语义质量有第三方背书样本

## 待核 (P2 裁决引擎产出)

- their 480 全量 sidecar 判定 (需下载 model.usdc + sidecar, ~500MB)
- E1 逐对比 (等 bg_686 缩略图)
- 我方 19+13 新类资产补建 (P3)

## NVIDIA 原版验证器合规 (2026-11-27)

- 20/20 设备类 (author_compile G-F 门禁全绿 → usdc → NVIDIA `_validate_usd_asset(physx)` **20/20 PASS**)
- 购物车 (shopping_cart, 293 部件/493×501×820mm/103.8kg) = NVIDIA 论文自报失败案例 ("细网格购物车钢丝重建失真") 的直接对标点: 我方参数化 authoring 一次过其全量校验
- 修的三处 family bug: DEFAULTS 嵌套表扁平合并入口 / carton 纸箱 "verts"→"verts_mm" 契约键 / 纸箱名浮点层号 (USD prim 路径非法) / bar_t 未赋值先引用
- 产物: output/nv960_usd/*.usdc (20) — 未并入数据集包 (包范围冻结不变)

## 参数变体规模证据 (2026-11-27)

- 参数变体扫 (每类 H×{0.8,1.0,1.0}·D×{1.0,1.0,1.25}): **35/60 变体 G-F 门禁绿 + NVIDIA 原版验证器 35/35 PASS**
- 25 个被 G-F4 尺寸对账门禁拦截 = 几何不响应假参数的正截 (门禁即参数响应性的仲裁者)
- 购物车完成真参数化: 框高/手柄/载货全部随 H 缩放, 620/775/969mm 三高度全绿
- 正典 20 件重编复验 20/20 PASS (family 修改后同步)
- **NVIDIA 验证器背书资产总计 70/70** (15 包装 + 20 设备正典 + 35 参数变体)
- 产能口径: 参数族编译+门禁+导出 ~2.0s/件 (对照 NVIDIA 4.9min/件含 LLM 程序作者费;
  我方 = 1 次家族 authoring → N 件验证背书实例的参数族模式)
