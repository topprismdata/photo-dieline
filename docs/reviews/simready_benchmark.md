# SimReady 官方资产对标实验 (2026-11-21)

## 目的

"超越 SimReady"声明的第一块硬证据:官方 SimReady 资产能否被 ESR 三门直接量测——
即 ESR 验证层是否**对外部官方资产可比**,而非自证。

## 源

`huggingface.co/datasets/nvidia/simready-assets` (NVIDIA 官方, **CC-BY-4.0**, 2,919 件,
免门禁)。取食品域 3 件跨形类:

| 资产 | 形类 | 主文件 |
|---|---|---|
| food_beverage_beerBottle_a01 | 玻璃柱体 | sm_...usd (crate) |
| food_beverage_bottledDrink_a01 | 塑料瓶 | sm_...usd (crate) |
| food_banana_a01 | 不规则曲面 | sm_...usda (文本) |

复取命令(资产不入库, >8MB 纪律):
`curl -sL "https://huggingface.co/api/datasets/nvidia/simready-assets/tree/main/<dir>/simready_usd?recursive=true"`
逐文件 `resolve/main/<path>` 下载。

## 语义覆盖门 v1.1 — 3/3 PASS

门升级在先:原 SL.001 判定是硬编码恒真(“我方只打 root 标签”)。升级为**真逐 prim
祖先链解析**(自身→父链找 `semantics:labels:*` 裸属性), 未解析 prim 像素计 unlabelled。
我方 14 SKU 回归 **14/14 保持**(root 标签经祖先链命中)。

| 资产 | on_coverage | labelled_frac | 解析到的标签 |
|---|---|---|---|
| beerBottle | 0.178 | 1.000 | wikidata_class=[glass bottle] |
| bottledDrink | 0.191 | 1.000 | wikidata_class=[glass bottle] |
| banana | 0.084 | 1.000 | wikidata_class=... (root) |

## 物理静置门 — 3/3 PASS

官方元数据直接喂我方 MuJoCo 静置协议(free joint + 5mm 间隙 + 1s + KE≈0 + 贴地):

| 资产 | dims_mm (asset_extents×1000) | mass_kg (元数据) | 材质标签 | KE | 结果 |
|---|---|---|---|---|---|
| beerBottle | 60 × 60 × 221.5 | 1.2954 | clear_glass | 1.08e-23 | PASS |
| bottledDrink | 52.8 × 52.8 × 174.9 | 0.6759 | plastic | 8.27e-25 | PASS |
| banana | 38.6 × 197.2 × 74.1 | 0.2729 | rubber | 3.34e-25 | PASS |

## 渲染门(可渲染性) — 1/1 PASS

Blender `wm.usd_import` 导入 beerBottle: 1 mesh、AgX 出图、爆白 0%
(`docs/images/simready_bench_beer.png`)。
坑:空场景下 `import_scene.usd` 需 addon 启用且 5.x 已改名为 `wm.usd_import`。

## 双向发现

### 官方资产侧

1. **标签双写形态**: root 级 `semantics:labels:wikidata_class=[glass bottle]` +
   `wikidata_qcode=[Q5567094]`,apiSchemas listOp 显式含 `SemanticsLabelsAPI:*` +
   `SemanticsAPI:*`(仅元数据声明,非 ApplyAPI 调用——plain usd-core 可读不可 Apply,
   与我方踩坑记录一致)。我方缺 **qcode 富化**。
2. **验证矩阵内嵌于主文件**: customLayerData `SimReady_Metadata.validation` 携带
   CAP/FET 能力清单(CAP000_Core.OpenUSD / CAP003_RigidBody.MuJoCo /
   CAP046_WikidataLabels / FET011_SemanticLabels 等)含 passed 标志与版本——连
   Multibody(DisplayColor)也有 passed=0 的**可选失败照实记录**。我方三门报告与
   其同构但未内嵌资产文件。
3. **变体门控三后端物理**: RootNode variantSets MuJoCo/Newton/PhysX,"Enabled" 各
   payload `runnables/physics/<backend>.usd`,默认 Disabled。我方等价物是
   verify_sku_physics.py 协议+manifest,形态不同、证据等价,但无 per-backend
   变体分发。
4. **标签瑕疵一处**: banana 材质 prim 名 `m_opaque__plant__banana_clean_a01` 而
   标签 `material=rubber`——官方标签库自身数据质量问题。
5. `metersPerUnit=1 / upAxis=Z` 与我方一致;mass/extents/qcode 元数据与我方
   manifest 字段一一对应。

### 我方管线侧

6. **pip usd-core 0.26.8 嵌套实例代理遍历缺口**: 官方 obj 层 `instanceable=true`,
   其下 Mesh 在 `TraverseAll` 不可见(嵌套代理)——gate 与 bench 均需先内存解除
   instancing(`SetInstanceable(False)`,不落盘)才可聚合几何。
7. 组合链考古: main →(references)→ base.usda →(references)→ instances.usda
   →(references)→ geometries.usd;Sdf 层 prim stack 三层齐全但 prim 子树对遍历器
   隐藏,属上述缺口表现。

## 结论

**ESR 三门对外部官方 SimReady 资产全部可用且全过**——验证层具备跨资产可比性,
这是"超越 SimReady"叙事的必要前件。差距条目(诚实清单): qcode 富化、验证矩阵
内嵌、per-backend 物理变体。我方独有优势: 参照对齐门(官方无参照坐标系)与
语义覆盖 CPU 光栅化(官方验证矩阵不含量化覆盖率)。

## 复跑

```
python3 scripts/gate_semantic_coverage.py                                  # 我方 14 SKU
python3 scripts/gate_semantic_coverage.py --usd-dir assets/simready_official/beer --out /tmp/g.json
python3 scripts/bench_simready_physics.py                                  # 官方 3 件静置
```
