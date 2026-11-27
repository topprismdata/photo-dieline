# 审计器契约 v2.2 — 观测/契约/裁决唯一权威定义（R09-03 WP-A0.2-C 收口）

- v2.2 变更：落实 R09-02 裁决 P0-01/02/03/04 —— 统一语义表、无向边分类、UNKNOWN 与客观 FAIL 分离、废弃 EXPECTED_SEAM 命名。

## L1 OBSERVATION（客观观测，不带裁决）

| 观测 | 定义 | 容差 |
|---|---|---|
| O1 tri-only | faceVertexCounts 全 3 | 精确 |
| O2 undirected_edge_faces | **无向边**关联面数 n：n=1 边界边；n=2 内部边；n≥3 非流形边 | 精确 |
| O3 interior_edge_direction | n=2 的共享边：两面绕向是否相反（同向=绕向错误，不是边界边） | 精确 |
| O4 boundary_walkable | 边界顶点恰被 2 条边界边触及 | 精确 |
| O5 face_components | 面经共享边连通分量 | 精确 |
| O6 vertex_fan_single | 顶点邻域扇形单连通（闭=环，开=链） | 精确 |
| O7 shell_signed_volume | 逐面分量体积（局部空间；镜像 prim 记录 mirrored 后按局部判） | 报告值 |
| O8 st_facevarying | 插值+长度（含 indexed 展开） | 精确 |
| O9 uv_face_area2 | 面角 UV 有向面积 | <1e-9 退化 |
| O10 uv_edge_pairing | 共享边端点对应：CONTINUOUS(全配) / PARTIAL_DISCONTINUITY(恰一端) / FULL_DISCONTINUITY(零配) | 1e-6 |
| O11 roundtrip | 二次展开 points/fvi/st 字节一致 | 精确 |
| O12 geom_degenerate | 3D 零面积三角 | <1e-7 |

## L2 CONTRACT（契约，资产登记）

SOLID（须闭合、外向体积>0）/ OPEN_SHELL（开口允许，边界可走）/ SURFACE（零厚度合法）/ FLAT_PATTERN（平面展开）/ COLLISION_PROXY。未登记 = 未登记（走 UNKNOWN 列）。

## L3 VERDICT（冻结语义表）

| L1 观测 | L2 契约预期 | L3 裁决 |
|---|---|---|
| CONTINUOUS | 连续 | PASS |
| PARTIAL_DISCONTINUITY | 允许切缝 | PASS |
| FULL_DISCONTINUITY | 允许切缝 | PASS |
| 任意不连续 | 要求连续 | FAIL |
| 任意不连续 | 未登记 | UNKNOWN |
| SOLID 且开边界 | 须闭合 | FAIL |
| O3 同向共享边（n=2） | 任意契约 | FAIL（绕向错误，客观） |
| O2 n≥3 非流形边 | 任意契约 | FAIL（客观） |
| O6 非单扇顶点 | 任意契约 | DISPUTED_FINDING（TRIAL 期；已知真值用例仍 FAIL） |
| O9 退化 UV 面 | 任意契约 | FAIL（客观） |
| O12 3D 退化三角 | 任意契约 | FAIL（客观） |
| O11 不一致 | 任意契约 | FAIL（客观） |
| SOLID 且体积≤0 | 外向 | FAIL（客观，局部空间+mirrored 记录） |

- **客观 FAIL 与契约解耦**：上表标注"客观"的项在契约未登记时仍判 FAIL；契约依赖项（接缝预期、闭合性语义）按 L2 登记。
- **总裁定**：任一客观 FAIL → FAIL；否则存在 UNKNOWN 项 → CONTRACT_UNKNOWN；否则 PASS。
- 法线属性缺失 = NOT_APPLICABLE（不得声称法线已验收）。
- 命名：废弃 EXPECTED_SEAM/UNEXPECTED_SEAM 作为裁决名；接缝仅记录 CONTINUOUS/PARTIAL_DISCONTINUITY/FULL_DISCONTINUITY + declared 标志。
