# A3-01 尺寸与折叠姿态仲裁 + A3-02 表达契约冻结

- 日期：2026-11-27
- 方法：brick_family.py 源码实证（`analytic_bbox` L773、`_brick_world` L127、docstring L1-16）

## A3-01 四问裁决

**A01｜analytic_bbox 独立性**：独立闭式公式（`{"W": W+D, "D": D, "H": Hb+2*hr}`），不调用 fold_all、不读世界顶点 → 公式级独立 ✅（同模块作者，非实现级独立）。注意 key 命名陷阱：返回的 "W" 是**包裹总宽（W+D）**，不是参数 W（面板宽）。

**A02｜参数语义**：W=砖盒体宽（x∈[hx,tx]）；D=封口方向深（斜肩外伸 D/2×2）；Hb=壁高；hr=斜肩升高；glue_w=胶板宽；board_t=板厚。

**A03｜宽度增量 ≈D**：斜肩链 slopeB/slopeF 封脊偏 ∓D/2 → 总宽 = W + D（95.5=57.3+38.2 ✓）。物理语义：无菌砖封顶后整体长度=体宽+两端斜肩跨——设计正确。

**A04｜高度增量 = 2×hr**（非 hr）：顶斜肩升 +hr 且底斜肩反折 −hr（docstring"顶底反折"设计）→ H = Hb + 2hr = 138.6 ✓。

**折叠姿态判定**：fold_all 的 target_dir_3d 由解析世界像自动导出（docstring L15-16）→ fold world ≡ analytic world **由构造保证**，非独立证据；独立佐证 = 家族自带 closure_checks（远缘重合/环缝重合残差）已内建于 QA 门禁。
**裁决**：DIMENSION_CONFORMANCE = PASS_AS_CONSTRUCTION（构造一致）+ closure_checks 通过佐证；"真实商品尺寸正确"仍以实物对照为准（维持 GPT 保留）。

## A3-02 表达契约冻结（blank / visual / collision）

| 表达 | 文件 | 契约 | 验收规则 |
|---|---|---|---|
| blank（刀版/印刷制造） | blank.usdc | FLAT_PATTERN：开边界允许；**net 排样重叠区合法**（`allowed_overlap()` 登记集合内的面板重叠=设计重叠，其重复边不判缺陷）；边界可走环 | 边界可走 + 重叠区 ⊆ allowed_overlap + 印刷面 UV 无退化 |
| visual（货架/感知/渲染） | folded_solid.usdc | SOLID（胶板重叠排除后闭合）+ UV 携带（net→折叠同角序）+ **印刷面镜像禁止（待诊断纹理证明）** | 闭壳体积>0 + 顶点单扇 + UV 无退化 + 印刷镜像=UNKNOWN（证据未到）|
| collision（物理代理） | collision.usdc | 简化 SOLID（无 UV、粗化细节、体积>0） | 闭壳 + 体积 ≤ visual 体积 + 包络⊇visual |

- `allowed_overlap()` 已内建于家族（`_BUILDERS[cid][2]()`）——blank 的重复边须逐一对照该集合：在集合内=设计重叠（PASS）；不在=真缺陷。
- 红线维持：印刷镜像证据未到前，visual 表达的镜像项 = UNKNOWN。

## 对 R09-05 四问的落实映射

| 问 | 答 | 出处 |
|---|---|---|
| A01 | 闭式公式独立 | brick_family.py:773-777 |
| A02 | 上表参数语义 | docstring + BRICK_DEFAULTS |
| A03 | slopeB/slopeF 外伸 D/2×2 | _brick_world slopeB/slopeF 坐标 |
| A04 | 2×hr（顶+底反折） | slopeB2/slopeF2 z=−hr 坐标 |
