# photo-dieline 核心管线复查 (core_audit)

基线: HEAD `54b81ca`, 只读。`python3 -m pytest tests/ -q` → 26 passed; `photo-dieline batch` → 100/100 green (5.5s)。
范围: `core/ir.py`、`folding/engine.py`、`parametric/base.py`、`parametric/gable_top.py`、`qa/pipeline.py`、`export/svg.py`、`export/pdf.py`、`align.py`、`render/twin.py`、`render/mesh.py`、`batch.py`、`cli.py`、`schemas/`、`tests/test_m1.py`、`examples/gable_top/`。
所有结论以代码 + 探针实跑为准 (探针在 `/tmp/pd_recheck/probes/probe1..10_*.py`, 可直接复跑); 推断处标 `[INFERENCE]`。

## 结论摘要

1. **交付物本身是坏的, 而 QA 与测试全绿。** golden 样例的 `dieline.svg`/`dieline.pdf` 缺失 4 块底封板 (画到画布外), `dieline.pdf` 在 poppler 渲染为全白、Apple CoreGraphics 打不开。
2. 两个 P0 都是普适的 (无输入假设): 导出器丢弃净图原点偏移 (95/100 模板几何出页); 手写 PDF 有两处语法错误。
3. QA "十道门" 实为 8 道 (G01、G09 不存在), 其中 G07 是恒真门, G04 有 2 条恒真判据并对 4/13 个面板零覆盖, G03 没有非流形/悬空边检查。
4. 对 IR 做 27 个单点破坏 (粘口折向盒外、底板未折、两鳍重合、非流形、M/V 全互换、SVG 缩半/清空、PDF 加缩放 …), **15 个 (56%) 仍判 VALIDATED**。
5. 折线 MOUNTAIN/VALLEY 标注自相矛盾 (同为向盒内 90° 折, 墙|墙标 VALLEY、墙|底板标 MOUNTAIN); 引擎自身的 M/V 判别在数学上恒为平局 (当前因全模板用 `target_dir_3d` 而未触发)。
6. "实测尺寸优先" (ADR-003) 未实现: `measurements[].value_mm` 从不参与几何, 证据状态只是从 spec 拷来的字符串; 照片内容对输出零影响 (三张不同照片输出逐字节相同)。
7. CLI 只能构建 `gable_top` 一类, `spec.package` 被静默忽略; README 的 "屋顶包/瓦楞箱/纸盒"、"十门"、"7 图层"、"恒等判据视为无效" 均与实现不符。
8. 零板厚: `board_t` 全仓零使用; G05 "golden 尺寸" 是参数自洽检查 (残差 3.5e-14 mm), 对制造精度零信息。

**条数**: P0 ×2 · P1 ×10 · P2 ×15 · P3 ×13 (合并项)。

---

## P0

### P0-1 导出器丢弃净图原点偏移 → 底封板画到画布外 (交付物残缺)

- 证据: `src/photo_dieline/export/svg.py:37-38` `T(x,y) = (x+MARGIN, y+MARGIN)`; `export/pdf.py:43-44` 同样只按 `net_w/net_h` 定页面并 `+shift`。`net_bbox()` (`svg.py:111-117`) 返回 `(x0,y0,x1,y1)`, 但所有调用点只传宽高: `cli.py:37,41`、`batch.py:48,50`、`tests/test_m1.py:29-31`。
- 事实: `gable_top` 净图 `y∈[-D, Hb+s+Ef]` (`parametric/gable_top.py:140-143` 底板 `rect(..., -D, 0)`), 原点不在左下角。half-pint 参数下净图 `y∈[-57.15, 122.02]`, SVG `viewBox="0 0 264.600 203.173"` 而几何坐标 `y∈[-48.15, 137.02]`: 33% 顶点在 viewBox 外, 页面底部 66.15 mm 空白。
- 实证 (仓内已提交产物 `examples/gable_top/artifacts/dieline.svg`): 4 块底板 `flapF/flapB/flapL/flapR` 整体位于 `y<0`; CUT 层 28%、BLEED 层 40% 坐标出界。librsvg 与 MuPDF 两个独立渲染器都显示 `y∈[140,190] mm` 为全空白, 墙带底缘折线 (SVG y=12) 上方没有任何翻板。PDF 同理: 路径起点 `y` 低至 -48.15 mm (页高 203.17 mm); MuPDF 解析语法修补版也给出几何 `y` 跨越 [66.15, 251.32] mm (页高 203.17 mm)。
- 影响面: 注册表 100 类中 **95 类** 的 SVG/PDF 几何超出页面 (最极端 `cup_sleeve` 整图在页外 441 mm)。
- 为何没被发现: G07/G08 只核对 "页面尺寸 = 净图宽高 + 24" (`qa/pipeline.py:194,211-212,225`), 而页面尺寸恰好算对了; `test_svg_physical_layers` 只断言 `width > 100` (`tests/test_m1.py:104`)。CI 还把这个残缺产物当 artifact 上传 (`.github/workflows/ci.yml:20-22`)。
- 修法: `render`/`build_pdf`/`_layer_geo` 一律接收 `(x0,y0)` 并平移 `T(x,y)=(x-x0+MARGIN, y-y0+MARGIN)`; G07/G08 增加 "全部几何坐标落在 `[0,W]×[0,H]` 内" 的硬判据, 并给 gable_top 补一条断言 4 块底板在页内的测试。

### P0-2 手写 PDF 有两处语法错误, golden PDF 在独立引擎下打不开/全白

- 证据: `export/pdf.py:85` `f"P{i} {oid} 0 R"` — `/Properties` 字典的键缺前导 `/`; `export/pdf.py:90` `f"/P{i} BDC"` — `BDC` 需要 "tag properties" 两个操作数, 这里只有 tag, 规范写法是 `/OC /P{i} BDC`。
- 实证 (对 `examples/gable_top/artifacts/dieline.pdf`, 与 HEAD 输出同结构):
  - poppler `pdftoppm`/`pdftocairo`: 29 条 `Dictionary key must be a name object`, 栅格化结果 **全白** (min pixel 255)。
  - Apple CoreGraphics: `CGPDFDocumentCreate → None`, `sips` rc=13 `Cannot extract image from file`。
  - MuPDF: `non-page object in page tree`, 页面尺寸读成默认 612×792。
  - pypdf (lenient): 14 条 `PdfReadError` 后才恢复。
  - 字节级二分: 只补 `/` 仍全白; 把 `BDC` 改成 `/OC /P.. BDC` 并补 `/` 后 poppler 与 Quartz 都能渲染且零语法错误 → 两处都是致因, 缺一不可。
- 为何没被发现: G08 只对前 4096 字节正则数 `/Type /OCG` 的个数 (`qa/pipeline.py:225-226`), 从不打开文件; DESIGN §9 (`DESIGN.md:99`) 列了 pypdf 但全仓未用。
- 修法: 修两处语法, 并把 "用 pypdf/PyMuPDF 打开成功 + 渲染后非空" 作为 G08 的前置条件。

---

## P1

### P1-1 PDF 图层挂载错位, GLUE/REGISTRATION/INFO 为空层, 全图无颜色

- 证据: `export/pdf.py:89-90` 用 `enumerate(streams)` 的下标拼 `/P{i}`, 而 `/Properties` 里的 `P{i}` 对应的是 `LAYERS` 下标 (`pdf.py:84-85`)。只要中间有图层为空, 之后的全部错位。
- 事实 (静态核对内容流与对象表): 有内容的图层依次是 CUT/CREASE-MOUNTAIN/CREASE-VALLEY/BLEED/INFO, 于是 `streams[3]`(BLEED 多边形, 47 段) 被标 `/P3` → 对象 9 = **GLUE**; `streams[4]`(50 mm 校验条) 被标 `/P4` → 对象 10 = **BLEED**; P5(REGISTRATION)、P6(INFO) 无任何内容。根因之一是 `_layer_geo` 只建 CUT/两条压线/BLEED 四层 (`cli.py:69-75`), GLUE 与 REGISTRATION 根本没有几何。
- 同时: `_path_cmds` 丢弃颜色 (`pdf.py:24` 的 `_color` 未用), 全部描边为默认黑; SVG 有 GLUE 填充与四角标, PDF 没有 → 同一 IR 的两个交付物图层内容不对等。README 称 "7 图层 OCGroups" (`README.md:63`), 实际成立的是 "7 个字典 + 3 个正确挂载的图层"。
- 修法: `chunks` 用 `LAYERS.index(name)` 取下标; `_layer_geo` 补 GLUE/REGISTRATION; 输出 `r g b RG`; G08 改为解析内容流核对每个 OCG 是否有对应 `BDC/EMC` 块。

### P1-2 折线 MOUNTAIN/VALLEY 标注自相矛盾, 且没有任何门校验

- 证据: `parametric/gable_top.py:154,173-180` 把粘口与 4 条底板折线标 `MOUNTAIN`; `:156-166` 把墙|墙、墙|坡标 `VALLEY`。导出器原样映射到图层 (`export/svg.py:59`、`cli.py:90`、`export/pdf.py` 的 BDC 分层)。
- 实证 (按折叠结果判定折向, 面 A = `polygon_2d` 逆时针法线 = 盒内面): `e_wl_bk`(wallL→back) 与 `e_ft_fl`(front→flapF) 的偏转角都是 90.0°、子面板 away 方向与父面板 A 面法线点积都是 +1.000 (同样向盒内折), 标注却一个是 VALLEY 一个是 MOUNTAIN。12 条折线中: 以盒内面为基准错标 5 条 (e_glue + 4 底板), 以印刷面为基准错标 7 条 (4 墙 + 2 坡 + 2 鳍) — **不存在任何一个观察面使全部标注成立**。
- 无门拦截: 把 12 条 `mt_va` 全部互换 → 仍 VALIDATED; `test_panel_fold_counts` 只断言两种标签都出现 (`tests/test_m1.py:62-69`)。合同项 "折线语义正确 — CUT/SCORE/MOUNTAIN/VALLEY 区分" 实际没有被检验。
- 修法: 在 QA 里加 "折线语义" 门 — 用折叠后法线计算每条边的实际折向, 与 `mt_va` 比对, 并在模板文档里固定观察面 (建议: 以 `polygon_2d` 正面为准)。

### P1-3 G04 有 2 条恒真判据, 且对 4/13 个面板零覆盖

- 证据: `parametric/gable_top.py:72-73` `wallL.top.B == slopeB.bottom.L`、`wallR.top.B == slopeF.bottom.L` 比较的是两条铰链的交点 — 铰链上的点在折叠中不动, 残差恒为 0。
- 实证 (逐条扰动 tdir, `probes/probe4_closure.py`): 上述 2 条在全部 15 个完成的变异下残差都是 0.0000 (另有 2 个变异使下游折叠抛异常); README 却声明 "恒等判据视为无效" (`README.md:33`)。
- 零覆盖: 把 `e_glue` 折向盒外 (粘口没贴上)、把 `e_bk_fl` 折成下垂 (背底板完全没折)、两鳍重合、粘口宽 12→2、背底板高 D→D/2 — 10 条判据全部仍为 0。`flapF.far.mid == flapB.attach.mid` 比的是 flapF 远边与 flapB 的**铰链边**, 对 flapB 自身完全不敏感。
- 另: 两鳍重合穿插被 G06 的 `ALLOWED_OVERLAP {finB,finF}` 豁免; `fin_gap_mm` 参数在 QA 里没有任何残差 (鳍被 `solid_roles()` 排除在 G05 之外, `gable_top.py:58`), 只有测试里查 (`tests/test_m1.py:96-97`)。
- 修法: 删掉 2 条恒真项; 为 glue↔front、flapB、finB/finF 各补一条非铰链点残差 (如 glue 远边中点到 front 平面的距离、两鳍顶缘中点距 = `fin_gap_mm`); 把 "每条判据对一个已知变异敏感" 写成参数化测试。

### P1-4 "实测尺寸优先" 未实现: 实测值不参与几何, 证据状态只是标签

- 证据: `core/ir.py:102-108` 只从 `spec.measurements` 取 `status` 字符串, `value_mm` 被丢弃; `cli.py:29-30` 直接用 `spec.params` 建几何。
- 实证: `params.W=50` 而 `measurements` 里 `W=45 MEASURED` → rc=0、VALIDATED, IR 里 `params.W=50.0` 且 `params_evidence.W="MEASURED"`。拼写错的 `"Widht"` 被静默忽略。
- 后果: ADR-003 "模型回归值 = INFERRED, 永远不能覆盖 MEASURED" (`DESIGN.md:63`) 没有任何执行点; "基准误差 ≤0.5mm" 无从谈起 (见 P2-3)。
- 修法: `build()` 里对每个 `MEASURED/VERIFIED_SOURCE` 项断言 `|value_mm - params[k]| ≤ 0.5`, 不一致即 `ARError`; 证据状态改由系统按来源推导而不是由 spec 自报。

### P1-5 G07 (SVG) 是恒真门, 不检验 1:1、分层内容与校验条

- 证据: `qa/pipeline.py:191` 只查 7 个 `id="<layer>"` 字符串存在 — 而 `svg.py:46,102` 无条件为 7 层各输出一个 `<g id>`, 空层也有; `:194` 只比较 `width` 与 `viewBox` 两个属性是否相等, 净图宽高只写进 metrics 不参与判定; `:195` 名为 `cut_closed`, 实际只是 `stroke-width="0.3"` 出现 ≥1 次。
- 实证 (5 个 SVG 篡改全部 PASS): `width/height/viewBox` 同除以 2 (非 1:1); 清空全部几何只留 `<g id>` 与一条 0.3 线; CUT 层与 CREASE-VALLEY 层内容互换; 删除 50 mm 校验条; 校验条改 40 mm。
- 修法: G07 解析 SVG (XML) 后逐层核对: CUT 层 = `net_bbox` 平移后的并集外轮廓 + `cut_segments`, 折线按 `mt_va` 落到对应层, `width_mm == net_w + 2*MARGIN`, 校验条端点距 = 50.000 user-units, 并断言 `1:1` 无 `transform`。

### P1-6 G03 没有非流形、悬空边、面积重叠检查

- 证据: `qa/pipeline.py:91-112` 只做两件事: 折线长度与 "最近顶点间距" 一致 (`:266-272`)、并集是单部件 (`:103`)。DESIGN §6 列的 "非流形拒绝、面板边界闭合" (`DESIGN.md:68`) 与合同项 "无悬空边、非法共享边" 都没有实现。
- 实证: 第三块板共享 `wallL|back` 折线 (3 面板共边) → VALIDATED; `front` 左移 5 mm 与 `wallR` 面积重叠 → G03 PASS (并集面积 150, 重叠被静默合并), 只是被 G05 因 bbox 变化间接拦下; 若重叠不改变 bbox 则无门可拦。`_seg_len_in_panel` 用 "最近顶点" 而不是 "这条边确实是面板的一条边", T 形汇合会被误报、对角线折线被漏报。
- 修法: 对全部面板边做半边统计: 出现 0 次 = 悬空, 2 次且是折线 = 合法, >2 次 = 非流形; 并断言 `sum(panel area) == union area` (容差 1e-6)。

### P1-7 G01、G09 不存在, "十道门" 实为 8 道; 照片对输出零影响

- 证据: `qa/pipeline.py:1-5` 文档字符串列 G01–G10, 实际只有 `Gate("G02".."G08")` 与 `Gate("G10")`; `:252` 的 `if x.id != "G01"` 过滤的是永不存在的门; 全仓没有 `"G09"`。`pipeline.py:1` 称 "缺照片参照 = DRAFT", 实际 `from_raw`(photo=None) 路径照样 VALIDATED (batch 的 100/100 green 即无照片)。
- 实证: 三张完全不同的 ≥1000 px 图 (纯色、噪声、真实照片) → SVG/PDF/IR(除 `package.photo`) 逐字节相同; GIF 也被接受 (无格式白名单, `core/ir.py:29-38` 只看最短边像素)。
- 与文档出入: `README.md:33,39` "十门全绿", `:64` "qa-report.json (G01-G10 门禁)"。
- 修法: 要么实现 G01 (写入报告, 并在无照片时降级 DRAFT) 与 G09 (报告自检: 门数、ID 集合、status 与各门一致), 要么把文档改成 8 门; 照片门至少加格式白名单与 EXIF/尺寸记录。

### P1-8 G06 豁免面过大, 且在通用管线里硬编码 gable 面板名

- 证据: `qa/pipeline.py:28-32` 的 `ALLOWED_OVERLAP` 是 gable 专属的 `flapF/flapB/glue/front/finB/finF`; `:170` 相邻面板一律跳过; `:172` 任意两个 `flap` 一律跳过。
- 实证: 报告写 `checked_pairs: 78`, 实际跳过 4 (允许对) + 12 (相邻) + 4 (flap–flap), 真正检查 58 对; 两鳍重合穿插 → VALIDATED; `flapL` 加长一倍后与 `flapR` 重叠 22.5 mm → 只被 G04 抓到, G06 因 "flap–flap" 不报。
- G06 没有任何测试: `_intersect3d` 的近平行分支 (`:286-288`) 只用单个顶点的距离判共面, 夹角 <2.5° 且真穿插的两板会漏检; 非平行分支把 B 投到 A 平面后比较面积, 会把 "穿过 A 平面但交线远离 A" 误报 (`:290-296`)。实测 (`probes/probe11_misc2.py`): 夹角 1.15° 的板穿过 A → `False`; 交线离 A 40 mm 的倾斜板 → `True`。
- 修法: 允许对只取模板的 `allowed_overlap()`, 删除管线里的硬编码集合; 相邻面板只在折角为 0°/180° 时豁免; `metrics.checked_pairs` 写真实检查数; 给 `_intersect3d` 补真穿插/假穿插两组单测。

### P1-9 CLI 只能构建 gable_top, `spec.package` 被静默忽略

- 证据: `cli.py:12` 直接 `from .parametric import gable_top`; `cli.py:30` 无条件 `gable_top.build_ir(params)`, 不读 `spec["package"]`, 也不走 `parametric.base.get()` 注册表。
- 实证: `spec.package="FEFCO_0201_not_supported"` → rc=0, 产出 `template.id="gable_top"`。
- 与文档出入: `README.md:5` 称可重建 "屋顶包/瓦楞箱/纸盒", 其余 99 类只能经 `batch` 用默认参数跑 QA, 无法从 spec 生成 IR/SVG/PDF。`align.py` (相机拟合) 与 `render/mesh.py` (OBJ) 都没有 CLI 入口, 也没有测试。
- 修法: `build` 改为按 `spec.package` 经注册表分发, 未知类显式报错。

### P1-10 测试只有正例, 没有一个负探针

- 证据: `tests/test_m1.py` 13 个用例中只有 `test_photo_gate_rejects_small` (`:44`) 与 `test_invalid_spec_rejected` (`:149`) 两个负例, 后者还用 `pytest.raises(Exception)` 兜底。没有任何用例验证 G03/G04/G05/G06/G07/G08 "能拒绝坏输入"。
- 实证: 27 个单点破坏中 15 个仍判 VALIDATED (见下表), 其中包括 P0-1/P0-2 对应的两类破坏 (几何出页、PDF 语法错误) — 现有测试对它们完全不敏感。
- 修法: 把下面的变异矩阵固化成 `@pytest.mark.parametrize` 的负探针测试, 每个变异断言 "至少一道指定的门 FAIL"。

---

## P2

### P2-1 折叠引擎的 M/V 判别在数学上恒为平局 (当前潜伏)

- 证据: `folding/engine.py:96-104` — 候选得分是 `d @ pc_world`, 而 `away` 与 `pc` 都在父面板平面内且都垂直于折线, 两个候选的得分恒相等 (`interior=90°: +0.000/+0.000`, `60°: +0.5/+0.5`, `120°: -0.5/-0.5`), 排序永远取 `sign=+1`。
- 实证: 构造仅 `mt_va` 不同 (VALLEY vs MOUNTAIN)、无 `target_dir_3d` 的两条边, 折后位姿逐点相同 (`interior` 取 90/60/120/45° 均如此)。文档字符串 `:7` 声称的 "VALLEY 折向父质心侧" 无法区分折向。`SCORE` 也落入同一分支折成 VALLEY。
- 影响面: 注册表 947 条边全部带 `target_dir_3d` (统计于 86 个可用默认参数构建的类), 所以当前无触发路径; 但它是公开 API 且是模板契约的默认折法。
- 修法: 判别量改用父面板法线 (`d @ n_parent > 0` 为 VALLEY), 并在 `mt_va` 与 `target_dir_3d` 矛盾时报错。

### P2-2 SCORE 没有独立图层; IR `edges` 无法表达 CUT/PERFORATION

- 证据: `export/svg.py:59` 与 `cli.py:90` 都是 `... if mt_va == "MOUNTAIN" else "CREASE-VALLEY"`, SCORE 被并入 VALLEY; `export/pdf.py:11` 的 `LAYERS` 无 SCORE。schema `edges[].kind` 是 `const "FOLD"` (`schemas/geometry-ir.schema.json:220-221`), 而 `DESIGN.md:53` 写的是 "MOUNTAIN/VALLEY/SCORE/CUT/PERFORATION"; 裁切线实际由导出器从面板边反推 (`svg.py:120-134`), 不在 IR 里。
- 实证: 12 条边全部改成 `SCORE` → VALIDATED, SVG 中 12 条线全在 CREASE-VALLEY 层。
- 修法: schema 给 `edges[].kind` 加 `CUT/PERFORATION/SCORE` 枚举并让 CUT 边进 IR; 导出器对未知 `mt_va` 报错而不是落 else。

### P2-3 G05 "golden 尺寸" 是参数自洽检查, 不是基准

- 证据: `qa/pipeline.py:143` 的期望值来自 `mod.analytic_bbox(params)` (`parametric/gable_top.py:44-47` 直接返回 `W/D/Hb+Hr`), 与折叠用的是同一组参数和同一批常量 `target_dir_3d`。实测值 (见 P1-4)、独立基准文件、零板厚都没有参与。
- 实证: 残差 3.55e-14 mm (仓内 `qa-report.json` 同值)。`analytic_box()` 给出的 `gable_apex_L/R`、`ridge_mid` (`gable_top.py:224-226`) 没有任何调用方使用。
- 修法: 引入人工核验过的 golden 基准 (期望 bbox + 期望外尺寸来源: 内/外), 让 G05 读基准文件而不是读参数。

### P2-4 G08 不解析 CTM; SVG 校验条无 QA; release gate 的 dieline 检查对真实输入是空检查

- 证据: `qa/pipeline.py:213-226` 只用正则在内容流里找一条 50 mm 线段并数 OCG 字典, 不处理 `cm`。
- 实证: 在内容流最前面加 `0.5 0 0 0.5 0 0 cm` (校验条实际 25 mm) → G08 PASS; 在 `/P1 BDC` 之后插入同样矩阵 → PASS。
- SVG 侧: 校验条长度/存在性没有任何门 (P1-5)。唯一会量 SVG 校验条的代码是 `scripts/pd_guard_r3.py --svg`, 而 workflow 跑的是 `pd_guard_r3.py dieline --spec examples/gable_top/spec.json --allow-missing-strip` (`.github/workflows/pd_guard.yml:12`): 该 spec 没有 `polygons` 字段 (0 个轮廓), 又豁免了校验条 → 对真实产物什么都没检查。
- 修法: G08 用 pypdf/PyMuPDF 取绘图指令并合成 CTM 后量长度; G07 量 SVG 校验条; workflow 改为对 CLI 输出的 `dieline.svg/pdf` 跑检查并去掉 `--allow-missing-strip`。

### P2-5 SVG 与 PDF 关于水平轴互为镜像

- 证据: `export/svg.py:37-38` 直接把净图 (y 向上) 映射到 SVG (y 向下), 没有翻 y; `export/pdf.py:43-44` 用 PDF 原生 y 向上。同一 IR 的两个交付物手性相反 (鳍在 SVG 里画在画布下半部, 在 PDF 里在上半部)。
- 后果: `MOUNTAIN/VALLEY` 是相对观察面的 (`svg.py:1-5` 未声明观察面), 镜像后观察面翻转, 与 P1-2 叠加后两个文件各自的错标数不同 (SVG 以印刷面为准错 7 条, PDF 以盒内面为准错 5 条)。
- 修法: SVG 用 `transform="scale(1,-1)"` 或在 `T()` 里翻 y, 使两个交付物同向; 在 IR `meta` 里固定 `mt_va` 的观察面。

### P2-6 SVG CUT 层每条线段都被画了两遍

- 证据: `export/svg.py:48-55` 先输出并集外轮廓 `<polygon>`, 再输出 `cut_segments(ir)` 的全部 `<line>`; 而 `cut_segments` (`:120-134`) 返回 "所有非折线面板边", 包含外轮廓边。
- 实证 (half-pint): CUT 层 = 1 个外轮廓多边形 (周长 1016.53 mm) + 30 条 `<line>`; 其中 24 条与外轮廓重合 (930.81 mm 被重复), 其余 6 条是 3 条内部裁切缝 (`x=81.15/138.30/195.45`) 各画两遍 (相邻翻板各贡献一条, 重叠 28.575 mm)。
- 后果: 视觉无差别, 但作为刀模/CAM 数据是重复实体 (重复切割风险, 也是 CAD 预检会报的项)。
- 修法: `cut_segments` 对外轮廓边与共享缝去重, 只输出 "并集外轮廓 + 内部缝" 各一次。

### P2-7 IR `features` 不驱动任何导出, 出血/校验条/粘口全是硬编码

- 证据: `export/svg.py` 与 `cli.py:66-96` 都不读 `ir.features`; 出血 `buffer(3.0)` (`svg.py:71` / `cli.py:85`)、校验条 `(12,8)-(62,8)` (`svg.py:87` / `cli.py:95`)、粘口按 `role=="glue"` (`svg.py:66`) 各自硬编码。
- 实证: 把 `f_bleed.offset_mm` 改 10、`f_check.length_mm` 改 30、`f_glue.panel_id` 改 `front`, 甚至把 `features` 清空 → SVG/PDF 逐字节不变, schema 仍合法。
- 漂移已发生: SVG 出血用 `buffer(3.0)`(默认 `quad_segs=8`), PDF 用 `quad_segs=2` (`cli.py:85`) → 218 vs 46 个顶点, 最大偏差 0.353 mm (大于 G04 的 0.2 mm 门)。两条 INFO/校验条实现也是各写一份。
- 修法: 导出器统一从 `ir.features` 取偏移/长度/位置; SVG 与 PDF 共用一个 `layer_geo` 生成器 (放 `export/` 下, 而不是 `cli._layer_geo`)。

### P2-8 零板厚: `board_t` 零使用, 尺寸语义未定义, 底板判据把 "全深双层翻板" 钉死

- 证据 (可证部分):
  - `board_t` 仅出现在 `gable_top.py:22,34,86` (参数表/校验/默认值), 不进入任何几何计算; 文档自认 "板厚补偿 P1 不做" (`:15`)。
  - 折叠引擎是零板厚刚体; G06 以 `|d| < 1e-6` 判共面 (`qa/pipeline.py:286-288`); 渲染器以 0.6 mm 做共面仲裁 (`render/twin.py:139-140`)。
  - `flapF` 与 `flapB` 都是 `W×D` 全底板 (`gable_top.py:140-141`), 加上 `flapL/flapR` 底面三层共面; 判据 `flapF.far.mid == flapB.attach.mid` (`:74-75`) 要求前翻板高等于 D — 把 `flapF` 改成常见的半深 (D/2) 会被 G04 以 22.5 mm 残差拒绝。
  - `fin_gap_mm` 与 `board_t` 无耦合: spec 注释写 "双层板厚叠层", 但 3.0 ≠ 2×0.45; `fin_gap_mm=40`(`Ef=14`) 时 `lean` 被钳到 90° (`gable_top.py:150,221`), 折叠后顶缘距实测 28.000 mm (偏差 12 mm), 没有任何门报告这个差异 (只是碰巧被 G06 以穿插拦下)。
- `[INFERENCE]` 工艺影响: 实测外尺寸 (spec 写 "卡尺") 对应的刀版面板宽应扣掉板厚/折痕补偿; 0.45 mm 与 MVP 的 0.5 mm 门同量级, 所以零板厚下 "≤0.5 mm" 既不能被 G05 证实也不能被证伪; 底部三层板在墙根处会相互顶起, 粘口与前脸共面只是零板厚下的重合。
- 修法: 在 IR `meta` 里声明名义尺寸是内尺寸还是外尺寸; `board_t` 至少用于折痕补偿并让 G05 对 "外尺寸 = 名义值" 做对账; `validate_params` 加 `fin_gap_mm < 2*Ef`。

### P2-9 schema 接受 NaN/Inf, 生成边界无非有限检查

- 证据: `schemas/geometry-ir.schema.json:89-93` 的 `params` 只要求 `type: number`; `gable_top.validate_params` (`:32-36`) 的 `v <= 0` 对 NaN 为 False。
- 实证: `W=inf` → G02 PASS (到 G04–G08 才失败); `W=nan` → 通过 schema, 直到 shapely 才抛 `GEOSException`。与 `AGENTS.md` L0-4 "NaN/Inf 不得传入下游; 在生成边界检查" 相悖。折叠引擎只对子面板做 `isfinite` 检查 (`folding/engine.py:114`), 根面板没有。
- 修法: `validate_dict` 后加一遍 `math.isfinite` 扫描 (params/polygon/seg/target_dir); 根面板同样检查。

### P2-10 非 editable 安装不可用: wheel 不含 `schemas/`

- 证据: `core/ir.py:12` 用 `parents[3] / "schemas"` 定位 schema (依赖仓库根布局); `pyproject.toml` 无 `package-data`, `schemas/` 不在 `src/` 下。
- 实证: 在 /tmp 用仓库副本 `pip wheel` → wheel 41 个文件, 不含任何 schema; 装进 site-packages 风格路径后 `validate_dict` → `FileNotFoundError`。CI 用 `pip install -e` (`ci.yml:13`) 所以没暴露; 合同项 15 "Core 独立安装测试" 只覆盖了 editable。
- 修法: 把 schema 移入包内 (`src/photo_dieline/schemas/`) 并用 `importlib.resources` 读取, CI 增加一条非 editable 安装的冒烟。

### P2-11 `align.py` 与渲染器只在一组默认值下同构, 参数边界与依赖声明不足

- 证据: `align.py:46` `half = 320.0` 硬编码; `align.py:22` `HI` 的 `cx/cy` 上界 1040 px; `render/twin.py:46,52` 把 `d_factor=3.0`、`fov=28°` 写死, `render_twin` 只暴露 `az/el`。
- 实证: 640 px 默认相机下 `align.project` 与 `twin.render_twin` 的投影差 5.7e-14 px (一致); 但 `size≠640` 时必须把 `(cx,cy,scale)` 设成 `(size/2,size/2,size/640)` 才等价, 拟合出的 `d_factor/fov/scale/cx/cy` 无法在 `render_twin` 里复现。合成拟合 (14 点, 3 px 噪声): 真值在 640 画布时 mean 2.6 px ✓; 真值在 2100×1500 (示例照片分辨率) 时 `cx` 撞上界 1040, mean 9.5 px; 3000×4000 时多参数撞界、mean 883 px。
- 其它: `align.py:53` 需要 scipy, 但 `pyproject.toml` 未声明、G10 禁用表也不含 scipy, 而 G10 的 metrics 却硬编码 "numpy/shapely/jsonschema/PIL/typer only" (`qa/pipeline.py:248`); 模块文档说关键点标在 "裁切实拍" 上 (`:4`), `overlay()` 却按原图缩放重映射 (`:88-95`) — `[INFERENCE]` 若 px 确为裁切图坐标, 叠加会整体错位。`align.py` 无调用方、无测试。
- 修法: `render_twin` 接收完整相机参数 (或两者共用一个 `project()`); 界限随图像尺寸缩放; 声明 scipy 或换 `scipy`-free 的最小二乘; G10 的 metrics 改成实际扫描结果。

### P2-12 对比图把任意照片都标成 "USDA PD" 公版

- 证据: `render/twin.py:167` `"A. 实拍照片 (USDA PD)"`、`:170` `"twin: gable_top IR folded"` 写死。
- 后果: README 明确支持换成用户自己的照片 (`README.md:49`), 输出对比图却声明该照片是 USDA 公版 — 与 `AGENTS.md` L1-14 可追溯、ADR-011 许可台账相悖。
- 修法: 标注从 `ir.package.photo` / 溯源文件读取, 没有溯源信息时写 "来源未声明"。

### P2-13 README / DESIGN 与实现的出入清单 (以代码为准)

| 声称 | 出处 | 实际 |
|---|---|---|
| "十门全绿"、"G01-G10 门禁" | `README.md:33,39,64` | 8 门, 无 G01/G09 (`qa/pipeline.py`) |
| "恒等判据视为无效" | `README.md:33` | gable_top 有 2 条恒等判据 (`gable_top.py:72-73`) |
| "7 图层 OCGroups" | `README.md:63` | 2 层空、2 层错挂、渲染器打不开 (P0-2, P1-1) |
| "裁切/压线/粘口/出血/套准" | `README.md:5` | PDF 无粘口与套准几何; SVG 的 "套准" 是四角裁切标 |
| "屋顶包/瓦楞箱/纸盒" | `README.md:5` | CLI 仅 gable_top (`cli.py:12,30`) |
| "模型值永不覆盖实测" | `README.md:19`, `DESIGN.md:63` | 无执行点 (P1-4) |
| edges 语义 5 种、features 5 类 | `DESIGN.md:53-54` | schema: `kind=FOLD` 常量、features 4 种且不驱动导出 (P2-2, P2-7) |
| P0 硬门 10 项 | `DESIGN.md:67-68` | 未实现: 非流形拒绝、尺寸闭合、粘口出血、面板数对账; 名存实亡: 1:1 物理尺寸 (G07)、CUT/SCORE 分层语义 (P1-5, P2-2) |
| 技术栈 Trimesh + pypdf | `DESIGN.md:99` | 两者都未使用 (相交检测是自写近似, PDF 从不被解析) |

### P2-14 `_intersect3d` 的两条已知错误路径

- 证据: `qa/pipeline.py:286-288` 近平行分支只用 `pa[0]` 一点的离面距离判共面; `:290-296` 非平行分支把 B 投影到 A 平面后比面积。
- 实证 (A = 20×20 平板; `probes/probe11_misc2.py`): 竖直板穿过 A 中心 → `True` ✓; 平行板距 5 mm → `False` ✓; **夹角 1.15°、交线在 A 内部 (真穿插) → `False` ✗**; **交线离 A 40 mm 的倾斜板 → `True` ✗**。对 gable_top 的 M1 形状不触发, 但 G06 是通用门且零测试。
- 修法: 近平行分支改为 "两板最近距离 < ε 且投影重叠"; 非平行分支求真实交线段再做区间重叠。

### P2-15 CI 与发布门把残缺产物当合格证据

- 证据: `.github/workflows/ci.yml:20-22` 构建 golden 样例后直接 `upload-artifact`; `pd_guard.yml:12` 的 dieline 检查对真实 spec 是空检查 (见 P2-4)。
- 后果: PR 上显示 "全绿 + golden artifacts 可下载", 而 artifact 本身缺底板、PDF 打不开。
- 修法: CI 里用独立渲染器把 `dieline.pdf`/`dieline.svg` 栅格化并断言非空、几何 bbox 落在页内; release gate 对 CLI 输出而不是对输入 spec 跑。

---

## P3 (合并)

1. `qa/pipeline.py:179` `checked_pairs` 报 78, 实测 58 (P1-8)。
2. `qa/pipeline.py:248` G10 的 `imports` metrics 是硬编码字符串 (与实际不符: `align.py` 需要 scipy), 禁用表里也没有 scipy。
3. `core/ir.py:68-69` `GeometryIR.folds_from()` 访问不存在的 `e.fold` → `AttributeError` (全仓无调用方, 死代码 bug)。
4. `render/twin.py:148-149` `_norm` 对零向量无保护 → batch 中 18/100 类触发 `invalid value encountered in divide` (79 次), NaN 法线进入着色路径; `:98` 轮廓线不做深度测试, 被遮挡面板的线透出。
5. `folding/engine.py:70-73` 根帧 `R0` 第三列全 0 (秩 2, 非旋转矩阵), 当前只喂 z=0 的净图向量所以正确, 但 `Rp @ (0,0,1)` 会得到零向量; `:81-83` 同一 child 的第二条入边被静默丢弃且无残差; `:127` `target_dir_3d` 不垂直铰链轴时不报错 (实测偏差 35°)。
6. `render/mesh.py:29` 所有 `usemtl` 都写在任何 `f` 之前 → 整个 OBJ 实际只用最后一个材质; 不产出 `.mtl`; 无 CLI 入口。
7. `parametric/base.py:41-47` 自动发现期 `except Exception` 吞掉模板模块的导入错误, 只打 stderr; batch 的 `total_classes` 不与预期类数对账 (与 `AGENTS.md` L1-13 "分母完整" 相悖)。
8. `batch.py:49` 与 `tests/test_m1.py:31` 都从 `cli` 导入私有 `_layer_geo` — PDF 图层几何的唯一定义在 CLI 模块里, `export/` 不拥有它 (与 P2-7 同根)。
9. `cli.py:17-18` `MM` 死代码; 负参数只抛裸 `ValueError` traceback; `core/ir.py:96` 把调用时的路径字符串 (可能是相对路径) 写进 IR 的 `photo.path`。
10. `export/pdf.py:24` 颜色被忽略; `:28-29` 虚线样式只取前两个数 (valley 的 `10,3,2,3` 变成 `10,3`); `:58-61,91` INFO 文本不在任何 OCG 内 (关掉 INFO 层文本仍在); 无 `TrimBox/BleedBox`。
11. `parametric/gable_top.py:40-41` `if __name__ != "__main__": pass` 空语句; `:146` `wall_of` 指向自身且只有 wallL 设了; `:216-230` `analytic_box` 的关键点无调用方; `:51` 注释 "过脊鳍对叠" 与实际 V 形张开几何不符。
12. `examples/gable_top/artifacts/dieline.pdf` 是旧版代码产物 (出血用高分辨率圆弧, 内容流 7793 字符 vs HEAD 重建 4273 字符), 与 HEAD 输出不同步。
13. `core/ir.py:102` 只取 `spec.measurements[]` 的 `name` 与 `status`, `source` 与不确定度都丢弃; 合同项 "记录尺寸来源和不确定性" 只剩一个枚举字符串。

---

## QA 门逐门体检 (审查点 a)

| 门 | 名义 | 实际检验了什么 | 判定 |
|---|---|---|---|
| G01 | 照片证据 | **不存在**。只有 `photo_evidence()` 的异常 (文件存在 + 最短边 ≥1000 px), 不进报告 | 缺失 |
| G02 | IR Schema | 真 schema 校验 + 模板必备参数键; 不拒 NaN/Inf, 不查引用完整性 | 弱 |
| G03 | 拓扑闭合 | 折线长 = 最近顶点距; 并集单部件。无非流形/悬空边/面积重叠 | 弱 (P1-6) |
| G04 | 折叠闭合 | 模板自报的 10 条残差: 2 条恒真, 4/13 面板零覆盖 | 有洞 (P1-3) |
| G05 | golden 尺寸 | 参数自洽 bbox (残差 ~1e-14) | 非基准 (P2-3) |
| G06 | 穿插 | 78 对里查 58 对; 近平行分支有漏检; 零测试 | 弱 (P1-8) |
| G07 | SVG 1:1+分层+校验条 | 7 个 id 存在 + 两个属性相等 + 一个字符串出现 | **恒真** (P1-5) |
| G08 | PDF MediaBox+50mm | MediaBox 公式 + 正则找 50 mm 线段 + OCG 字典计数; 不开文件、不解析 CTM | 弱 (P0-2, P2-4) |
| G09 | 报告自检 | **不存在** | 缺失 |
| G10 | core 隔离 | 扫 `src/` 的 import 语句; metrics 硬编码 | 形式化 |

## 变异矩阵 (审查点 a/g; `probes/probe5_qa_matrix.py`)

27 个有效单点破坏, **12 拦 / 15 漏**:

| 破坏 | 结果 |
|---|---|
| 粘口 `e_glue` 折向盒外 | **VALIDATED** |
| 背底板 `e_bk_fl` 下垂未折 | **VALIDATED** |
| 两鳍重合穿插 | **VALIDATED** |
| 粘口宽 12→2 | **VALIDATED** |
| `params.W=50` 而 measurements `W=45 MEASURED` | **VALIDATED** |
| 12 条 M/V 全部互换 | **VALIDATED** |
| 12 条 `mt_va` → SCORE | **VALIDATED** |
| 第三块板共享折线 (非流形) | **VALIDATED** |
| SVG `width/height/viewBox` 缩半 | **VALIDATED** |
| SVG 几何全清空 | **VALIDATED** |
| SVG CUT↔CREASE 层互换 | **VALIDATED** |
| SVG 删校验条 / 校验条改 40 mm | **VALIDATED** |
| PDF 内容流加 `0.5 … cm` (校验条实为 25 mm; 两个位置) | **VALIDATED** |
| `fin_gap_mm=40`、`Hr=0.001` | DRAFT (G06 间接) |
| `W=inf` | DRAFT (G04–G08); `W=nan` 在 shapely 才炸 |
| 右底板折到墙外、左底板加长一倍 | DRAFT (G04) |
| 鳍倒伏、坡面 `target_dir_3d` 带轴分量 | DRAFT (G06) |
| `front` 与 `wallR` 面积重叠 | DRAFT (G05 间接; G03 PASS) |
| 悬空折线、`finB` 断开 1 mm | DRAFT (G03) |
| PDF 内容流清空、MediaBox 改 A4 | DRAFT (G08) |

## 审查点速查 (b–g)

- **(b) 运动学与闭合**: 位姿求解正确 — 铰链轴取父帧下折线方向 (`engine.py:86-90`), 绕轴把子面板 away 方向转到目标 (`:124-134`), 共铰链点在 15 个完成的变异下残差恒 0 可证其刚体性; 折序与结果无关 (每面板位姿只依赖父帧)。缺陷: M/V 判别恒平局 (P2-1)、多余约束静默丢弃、只验终态不验过程、残差定义里混有恒真项 (P1-3)。
- **(c) 零板厚**: 见 P2-8。
- **(d) SVG/PDF**: 单位正确 (user unit = mm, `mm→pt = 72/25.4`, MediaBox 实测 264.600×203.173 mm 与 SVG 一致); PDF 校验条本身是 141.732 pt 的矢量线 — 对语法修补后的 HEAD 输出用 MuPDF 独立解析实测 50.0000 mm (机器可量, 前提是文件能打开); 出血是外轮廓外扩 3 mm 的单一闭合环; "套准" 是四角裁切标且仅 SVG 有。问题集中在 P0-1、P0-2、P1-1、P1-5、P2-4、P2-5、P2-6。
- **(e) align vs 渲染器**: 默认相机下逐像素一致 (5.7e-14 px); 同构只覆盖 `size=640` 且固定 `d/fov` 的情形 (P2-11)。
- **(f) CLI 与文档**: 见 P1-7、P1-9、P2-13。
- **(g) 测试缺口**: 见 P1-10; 另无任何测试覆盖 G06、折线语义、1:1、分层内容、几何在页内、PDF 可被第三方解析、CLI 端到端 (CI 里有一步但不栅格化)、`from_raw` 往返、`board_t`/`fin_gap` 的域、证据状态不被覆盖。

## §10 十六项合同对照

| # | 合同项 | 实现 | 测试 |
|---|---|---|---|
| 1 | 读照片 (文件/分辨率/格式) | 文件+分辨率; 无格式门 | 1 正 1 负 |
| 2 | 接受 mm 尺寸 | ✓ (`units` 常量 mm) | 间接 |
| 3 | 记录来源与不确定性 | 只有状态枚举; 值不参与 | 1 正 |
| 4 | 合法 IR | ✓ | 1 正 1 负 |
| 5 | 拓扑闭合 (无悬空边/非法共享边) | 部分 (P1-6) | 0 负例 |
| 6 | 折线语义 (CUT/SCORE/M/V) | 不自洽, SCORE 无层 (P1-2, P2-2) | 仅存在性 |
| 7 | 基准尺寸 ≤0.5 mm | 自洽检查 (P2-3) | 自洽断言 |
| 8 | 1:1 SVG | 渲染器对, 门不验 (P1-5) | `width > 100` |
| 9 | PDF 页面尺寸与 SVG 一致 | 尺寸一致; 内容互为镜像, 文件打不开 (P0-2, P2-5) | 正则 MediaBox |
| 10 | 50 mm 校验条 | PDF 有; 门不抗 CTM; SVG 无门 | 正则 |
| 11 | 分层结构正确 | SVG 可; PDF 错挂/空层 (P1-1) | id 存在性 |
| 12 | 折叠闭合 | 有洞 (P1-3) | 正例 |
| 13 | 无穿插 | 弱 (P1-8) | 0 |
| 14 | 报告所有失败项 | JSON ✓; 缺 G01/G09 | 1 正 |
| 15 | 无 TRELLIS 可跑 / 独立安装 | editable ✓; 非 editable 不可用 (P2-10) | 无 |
| 16 | 许可隔离清单 | `THIRD_PARTY_NOTICES.md` 有 5 个依赖; 缺 scipy (P2-11) | 无 |

## 复现

```bash
cd /Users/guohongbin/photo-dieline
python3 /tmp/pd_recheck/probes/probe1_engine.py        # 引擎 M/V 判别恒平局
python3 /tmp/pd_recheck/probes/probe3_mv.py            # gable 折线标注 vs 实际折向
python3 /tmp/pd_recheck/probes/probe4_closure.py       # closure 判据敏感性
python3 /tmp/pd_recheck/probes/probe5_qa_matrix.py     # QA 变异矩阵
python3 /tmp/pd_recheck/probes/probe7_offset.py        # 净图原点偏移 / 画布外
python3 /tmp/pd_recheck/probes/probe8_misc.py          # features / 照片 / CLI spec
python3 /tmp/pd_recheck/probes/probe10_render_committed.py  # 独立引擎渲染仓内 golden 产物
python3 /tmp/pd_recheck/probes/probe11_misc2.py         # _intersect3d 正负例 / CUT 内部缝 / fin_gap 钳位
```

## 未验证 / 局限

- 未测 Adobe Acrobat/Illustrator 对该 PDF 的容忍度 (本机无); 结论限于 poppler、Apple CoreGraphics、MuPDF、pypdf 四个引擎。
- PDF 图层错挂 (P1-1) 的依据是内容流与对象表的静态对应; 因 P0-2 文件打不开, 未能用渲染器 "关层看消失" 直接验证。
- 其余模板家族的内部几何不在本次范围, 只统计了它们受 P0-1 影响的面 (95/100) 与 `target_dir_3d` 的使用面 (947/947)。
- 零板厚的工艺量级 (P2-8) 是 `[INFERENCE]`, 未做板厚折叠仿真。
