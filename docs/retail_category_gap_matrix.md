# 零售类目差距矩阵 — 对标 NVIDIA SimReady Assets (2026-11-26)

> 数据基线: `nvidia/simready-assets` HF 树全量拉取 2919 资产目录名 (前缀=类目)。
> 前缀统计: food 539 (produce 223/processed 89/prepared 86/beverage 85/egg 13/canned 12),
> kitchenware 179, box 154, consumable 77, cleaning 44, container 44, grocery 20, pallet 64, warehouse 67。
> NVIDIA 无 beverage 顶层类 (饮料在 food_beverage_* 下), 无 alcohol/liquor 专类。

## 我方现有覆盖 (通用零品牌)

| 域 | 族 | 类数 | 状态 |
|---|---|---|---|
| 纸盒包装 | gable/clv/cone/food (TDE) | ~25 变体 | 训练语料 5010 样本已产 |
| 刚性容器 | bottle_wine / beverage_can_330 / food_container_1l / rsc | 4 | USD 已导 |
| 酒类 | beverage_liquor v1 (啤酒瓶330/500·易拉罐500·白酒瓶·洋酒瓶×2·礼盒) | 8 | 几何契约过+渲染目检过, USD 待导 |
| 零售设备 | nv960_fixture (购物车/篮/扫描器/陈列架/分配器×7/垃圾回收/流利架/网筐×3/模具/果篮/油桶/泵) | 20 | 已入 nv960 战役 |

## 差距矩阵 (零售货架视角, 双轴: 商品类目 × 包装结构)

### 轴 A: 饮料酒水 (本轮, 用户指定)

| 商品类目 | 包装结构 | NVIDIA | 我方 | 行动 |
|---|---|---|---|---|
| 啤酒 | 玻璃瓶 330/500 | beerBottle 单一形制 | v1 两类 ✓ | USD 导出 |
| 啤酒 | 易拉罐 330/500 | 无罐 (beverage can 散见) | 330 已有 + v1 500 ✓ | USD 导出 |
| 白酒 | 玻璃瓶 500 (鼓腹/经典) | **无** | v1 ✓ | 补酱香/浓香两种瓶形 |
| 洋酒 | 威士忌/伏特加 700 | 无专类 | v1 ✓ | — |
| 葡萄酒 | 波尔多/勃艮第 750 | wineBottle? 散见 | bottle_wine 已有 | 精版对齐 |
| 即饮茶咖 | PET 瓶 500 | bottledDrink 玻璃标 | **缺** | PET 瓶形 v2 |
| 软饮 | PET/CAN 330/500 | 无罐 | 缺 PET | PET 瓶形 v2 |

### 轴 B: 食品日化 (下一轮)

| 类目 | NVIDIA 对应 | 我方 | 优先级 |
|---|---|---|---|
| 生鲜果蔬 | food_produce 223 | 0 | P1 (形状族: 球/长圆/串状, 参数化可覆盖大半) |
| 乳制品 | dairy 2+grocery 1 | 屋顶包语料 (包装侧) | P2 利乐砖/爱克林形 |
| 罐头 | food_canned 12 | food_tin_can 已有 | P1.5 变体扩 |
| 调味品 | condiment 3+4 | condiment_pump 已有(设备) | P2 瓶形族 |
| 清洗日化 | cleaning 44 | detergent_bottle 已有 | P1.5 形制扩 |
| 零食烘焙 | grocery_snack/bakery | hinged/clv 盒形已有 | P2 袋形族 |
| 蛋盒 | egg 13 | 0 | P3 |

### 交付结构差距 (GPT 讨论核心: 资产契约)

| 项 | NVIDIA | 我方 | 行动 |
|---|---|---|---|
| 语义标签 | wikidata_class prim 属性链 | box_tp 样式标签 | 对齐语义 schema |
| 物理 | USD Physics 公共基础 + 运行时验证 payload | 质量常缺 (GPT R4 已删伪值) | 按 Profile 实现, 不造假 payload |
| payloads/ | MuJoCo/Newton/PhysX (经运行时验证) | 无 | **不做无验证 payload (虚假兼容)** |
| .metadata + thumbs | 有 | 无 | USD 导出时补 |
| 验收 | 静态+运行时+组合三层 | 像素层强 (nv960) + QA 十门 | 扩语义/物理/运行时层 |

## 里程碑

- M1 (本轮): 酒类 8 类 USD 导出 + .metadata/thumbs 结构对齐
- M2: PET 瓶形族 + 白酒第二瓶形 → 轴 A 覆盖 ~12 类
- M3: 果蔬参数化族 (球/椭圆/串) → 对齐 NVIDIA 最大类 food_produce
- M4: 语义 schema 对齐 + 资产规格 schema (来源分级) → 零售本体 v0
- M5: SimReady Central Library 贡献路径调研 (GPT 建议: 互补者, 非挑战者)
