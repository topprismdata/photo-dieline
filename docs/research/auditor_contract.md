# 审计器契约（auditor_contract.md）— 观测/契约/裁决三层定义

- 版本：v2.1 对应
- 地位：审计器输出语义的唯一权威定义；数值容差在此冻结，改动需走裁决流程

## L1 OBSERVATION（客观几何观测，不做质量判断）

L1 只记录测量事实，输出布尔/数值，不带 PASS/FAIL 语义：

| 观测项 | 定义 | 容差（冻结） |
|---|---|---|
| O1 tri-only | faceVertexCounts 全为 3 | 精确 |
| O2 dup_directed_edges | 同一有向边出现 ≥2 次 | 精确 |
| O3 boundary_edges | 无反向配对的有向边集合 | 精确 |
| O4 boundary_walkable | 每个边界顶点恰被 2 条边界边触及 | 精确 |
| O5 face_components | 面经共享边形成的连通分量数（非顶点并查） | 精确 |
| O6 vertex_manifold | 每顶点邻域面构成单扇形（无蝶形/双扇非流形顶点） | 精确 |
| O7 shell_signed_volume | 逐面连通分量分别计算 Σ(dot(v0,cross(v1,v2)))/6 | 报告值 |
| O8 st_facevarying_count | primvars:st 长度与插值 | 精确 |
| O9 uv_face_area2 | 逐面角 UV 二倍有向面积 | |a|<1e-9 判退化 |
| O10 uv_edge_pairing | 共享边两端 UV 对应关系 e1..e4 | 1e-6 |
| O11 roundtrip_bytes | 二次展开 points/fvi/st 字节一致 | 精确 |

## L2 CONTRACT（结构语义契约，资产按契约归类）

| 契约 | 定义 | 零厚度 | 开边界 | 绕向要求 |
|---|---|---|---|---|
| SOLID | 封闭实体 | 禁止 | 禁止 | 体积>0 |
| OPEN_SHELL | 开口容器/筒 | 视用途 | 允许，边界须可走环 | 相邻面一致 |
| SURFACE | 曲面片 | 允许 | 允许 | 相邻面一致 |
| FLAT_PATTERN | 包装展开图 | 允许（必然平面） | 允许 | 相邻面一致 |
| COLLISION_PROXY | 碰撞代理 | 依碰撞体类型 | 依类型 | 依类型 |

- 契约来源（优先级）：资产元数据声明 > 结构家族模板缺省 > `UNKNOWN`（未登记契约，裁决降级）。
- **默认契约=UNKNOWN 时，L3 只能输出 UNKNOWN，不得输出 PASS/FAIL。**

## L3 VERDICT（裁决规则）

| 输入 | 裁决 |
|---|---|
| SOLID + O2/O4 异常或体积≤0 | FAIL (topology/winding) |
| OPEN_SHELL/SURFACE/FLAT_PATTERN + O2/O4 异常 | FAIL (topology) |
| SOLID + 体积≤0 | FAIL (winding) |
| O9 退化 UV 面 >0 | FAIL (uv) |
| O10 全配 | EXPECTED_SEAM（合法图集切割，计数） |
| O10 恰一端配 | **UNEXPECTED_SEAM**（crack 候选，需人工/L2 仲裁） |
| O10 零配 | UNKNOWN（可能是图集切割意图，登记不裁决） |
| O11 不一致 | FAIL (roundtrip) |
| 显式 normals 缺失 | `NOT_APPLICABLE`（不得声称法线已验收） |
| 未知契约 + 任何异常 | UNKNOWN（不静默 PASS） |

## 特殊语义不变式（验收门禁用）

- 语义保持操作（顶点重编号、三角形重排、整体平移、正缩放）不得改变任何 L3 裁决。
- 负缩放（奇次行列式<0）按 USD 方向语义翻转绕向后裁决。
- 非法输入、属性缺失、未知契约一律不静默 PASS。
