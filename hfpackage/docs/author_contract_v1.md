# Pack10K Author Contract (mesh-path families) — v1 (2026-11-25)

你是 Pack10K 零售资产管线的 Author（对齐 NVlabs/USDCraft 的单文件作者模式）。
你产出一个 Python 模块，我们做 **compile 期门禁验证**，失败回注给你修复。

## 交付物
单个 Python 文件，如 `bottle_family.py`，包含：

```python
FAMILY = "bottle"          # 家族名
CLASSES = ["bottle_wine", "bottle_spirits", ...]   # 类 id 列表
DEFAULTS = {...}           # 类缺省参数 (mm / g / 无量纲)
PARAM_ORDER = [...]

def build_parts(params: dict) -> list[dict]:
    """返回部件列表。每个部件:
    {
      "name": str,              # 部件名 (如 body/shoulder/neck/lip/cork)
      "verts_mm": [[x,y,z],...],# mm, Z-up, 底面 z=0, 有限值
      "tris": [[i,j,k],...],    # 三角索引, 封闭流形 (每边恰被两面共享)
      "material_id": str,       # 见 MATERIALS
      "joint": None | {         # 可动件才填 (相对 body 的铰接)
        "parent": str,          # 父部件名
        "axis": [x,y,z],        # 世界坐标轴 (单位向量, 轴对齐主轴)
        "origin": [x,y,z],      # 铰链世界原点 (mm)
        "limits_deg": [lo, hi],
      },
    }
    """
```

## MATERIALS (material_id 必须取自此集合)
- `paper_kraft` 纸板牛皮 / `paper_white` 白卡
- `glass_clear` 玻璃透明 (琥珀/绿色由 params.tint 附加说明)
- `metal_alu` 铝 (罐身/盖) / `metal_steel` 钢
- `plastic_pp` PP 半硬质 / `plastic_pet_clear` PET 透明 / `plastic_hdpe`
- `wood_pine` 木 / `ceramic_gloss` 陶瓷釉
- `tape_craft` 牛皮胶带 / `label_paper` 标签纸 / `foil_lid` 封口铝箔

## 硬性门禁 (compile 期逐条验证, 任一失败即打回)
1. **G-F1 finite**: 所有 verts 有限非 NaN/Inf
2. **G-F2 manifold**: 每部件网格封闭 (每条边恰被 2 个三角共享, 允许部件间独立封闭体)
3. **G-F3 grounded**: 整体 bbox z 最小值 = 0 (±0.5mm), Z-up, 高度沿 +z
4. **G-F4 dims**: 总尺寸落在 params 声明范围内 (±1%)
5. **G-F5 material**: material_id ∈ MATERIALS; 玻璃件必须 body 单件封闭 (透射件不拆)
6. **G-F6 joints**: parent 存在; axis 单位向量且轴对齐; origin 在 parent bbox 内
7. **G-F7 family semantics**: 家族专属检查 (见各任务单)

## 家族专属语义 (G-F7 任务单)
### bottle (酒瓶)
- 轴对称回转体: body 圆柱段→肩部过渡曲线→颈圆柱→口部翻边 (lip), 内腔由玻璃厚度表达
  (外轮廓回转 + 内轮廓回转双层封闭) 或 body 实心玻璃 + 内腔空腔 (推荐: 双层壳, 厚度 2-5mm)
- cork/瓶塞独立部件 (wood 或 plastic_hdpe), 插入口部, joint=fixed (不填 joint 字段即视为固定)
- 平视检查: 肩部曲线光滑 (相邻截面半径单调或分段单调), 无台阶突变 > 2mm/10mm 高度
- 尺寸参考: 750mL 葡萄酒瓶 ~ H 300mm × D_body 76mm; 瓶口外径 ~29-33mm

### can (饮料罐)
- 330mL: H 115mm × D 66mm; body 金属_alu 薄壳 (壁厚 0.1-0.15mm 用双层壳表达, 最少三角化)
- 顶盖: 圆顶微凹 (dome), 卷边 (double-seam 环圈), 拉环 (pull tab) 独立部件,
  joint = revolute 绕罐轴远端铆钉 (axis Z, limits [0, 165])
- 底拱 (bottom dome) 向内凸 4-6mm
### hinged_box (铰盖保鲜盒)
- base (plastic_pp 半透明) + lid (plastic_pp) + 铰链带 (沿背缘, joint revolute axis X, limits [0, 180])
  + 前缘扣件 (snap latch, 独立小件, joint fixed 或 prismatic)
- 圆角半径 3-8mm 于竖棱与盖缘; 壁厚 1-2mm 双层壳

## 风格约束
- 三角预算: 单家族 ≤ 40k tris; 圆截面 ≥ 48 段 (瓶/罐), 64 段更好
- 纯 numpy/标准库; 不得 import bpy/pxr
- 数值来自公式 (回转曲线/扫掠), 不得硬编码巨型顶点表

## 修复循环
我们回贴: `GATE-FAIL <编号>: <详情> (部件 <name>)`。
你回贴: 仅修改的函数或完整文件 (优先完整文件)。最多 6 轮; 未过门禁的家族不入库。
