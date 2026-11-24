# 货架孪生 / ESR 线代码健康度复查 (twin_audit)

- 对象: `/Users/guohongbin/photo-dieline` @ `54b81ca`(审计前后 `git status` 一致, 仅既有未跟踪目录 `docs/reviews/recheck_2026-11-24/`)
- 范围: `scripts/build_hxl_shelf.py`、planogram/ESR/后置脚本、`data/shelf_twin/*.json`、`docs/shelf_twin/`、`docs/reviews/shelf_convergence.md`
- 方式: 全文静态阅读 + 只读复跑(输出全部重定向到 `/tmp/pd_recheck/twin_audit_evidence/`)。未运行 Blender/渲染, 未训练, 未改仓内文件。
- 证据标记: **[R]** 本次只读实跑复现 · **[S]** 静态阅读可证 · **[INFERENCE]** 推测, 需 Blender 探针核实

## 结论摘要

1. 共 28 条: **P0×1 / P1×10 / P2×12 / P3×5**。
2. **P0**: ESR 的 SKU 资产层在 HEAD 已失效——18 个 USD 全部丢失 class/material 标签、`phys:dimensionsMM`、`kind`,`box_tp_00` 实为 1 m 立方; 而入库的 `esr_acceptance.json`(COMPLIANT)、`conformance_score.json`(140/140)仍是回归前的旧报告。
3. **三门都没有否决能力**: 语义门接受任意 `semantics:labels:*`(P1-1); 物理门不读 USD、对质量/摩擦不敏感(P1-2); 渲染门是手写 `pass: true`,指向 32 个版本前的 v28d(P1-3); 像素门给白噪声判 ALIGNED(P1-4)。
4. **Step A 不可重放**: 三个生成器写同一路径、三种 schema; 按脚本链重放得到 30 组 `tp_*`,与已提交的 36 组 `d_*`(含 box/tray 手工组)不是同一份数据; 在已提交文件上重跑 `make_planogram_det.py` 直接 `KeyError: 'tray_lean'`(P1-5)。
5. **资产层与场景断链**: `build_hxl_shelf.py` 完全不引用 `sku_usd`/`sku_manifest`; 三门验收的资产不在被渲染的场景里(P1-6)。
6. **零测试、门禁空转**: 26 个 pytest 无一触及该线; `rule-enforcer.json` "保护 `scripts/**`" 的执行器只跑 `pd_guard_r3` 与核心包(P1-7)。
7. **可移植性与证据强度**: `ROOT` 硬编码绝对路径且渲染时写 tracked 目录(P1-10); manifest 自称"实测单源"的尺寸实为占位默认参数(P1-8); Oreo 产品照裁片入库无来源/许可记录(P1-9)。
8. **(b) 直接回答**: 种子全部确定但与抽取顺序耦合(靠 `_legacy_tray_rng` 回放垫片维持); 贴图缓存按文件名而非内容失效; HDRI 与 AI 印刷图已入库可复取, 参照照、官方 SimReady 资产、检测证据不在仓(后两者只有文档配方/仓外绝对路径)。
9. 巨石: `main()` 单函数 1133 行(占文件 54%),其中 631 行是只打印不判定的实验探针分支; 死代码比已记账的多 5 处。
10. 最高杠杆: 修 `export_sku_usd.py` 并重跑 label→enrich→三门落盘 → 给三门加真实否决条件 → `planogram.json` 冻结为唯一真源并把纯逻辑抽成无 bpy 模块补 pytest。

---

## P0

### P0-1 ESR 资产层在 HEAD 失效,入库的合规报告是回归前的旧结果

**证据 [R][S]**
- 回归点: `git show d03fa61:assets/sku_usd/box_tp_00.usda` 含 `kind="component"`(:16)、`phys:dimensionsMM`(:20)、`semantics:labels:material`/`wikidata_class`/`wikidata_qcode`(:21-23); 提交 `0a03d31` 重导出后 14 个文件各删 4 行并新增 4 个桶,只重跑了 `enrich_sku_usd.py`,没重跑 `label_sku_usd.py`。
- HEAD 现状(逐文件 grep + pxr 读回): 18 个 `assets/sku_usd/*.usda` 中 `semantics:labels:wikidata_class`=0、`semantics:labels:material`=0、`phys:dimensionsMM`=0,root `kind`=None; 仅剩 `wikidata_qcode`(`box_tp_00.usda:19`)。
- `box_tp_00.usda:34` `extent = [(-0.5,-0.5,-0.5),(0.5,0.5,0.5)]` → 世界包围盒 1000×1000×1000 mm,manifest 声明 120×45×190。根因 `scripts/export_sku_usd.py:95-101`: `o.scale`/`location` 设在临时对象 `o` 上,随后 `o` 被 unlink,`export()`(:68-78)用同一 mesh 新建单位变换对象 → 缩放与位置全部丢失。桶分支同理丢位置(:88-91): 桶/盒 z∈[-130,130](原点在几何中心),袋 z∈[-18,208](原点在底面),同库原点约定不一致。
- 袋网格无 `primvars:st`(`bag_tp_00.usda` 中 0 处),却绑定了 `UsdUVTexture`(1 处)→ 贴图无坐标可采样; 袋实厚 42 mm,声明 70 mm。
- 每个资产内含 Blender 默认世界灯 `DomeLight "env_light"`(`box_tp_00.usda:51-57`,引用 `./textures/color_0C0C0C.exr`)。
- 旧报告与现状: `data/shelf_twin/esr_acceptance.json`(`compliant: true`,14/14)、`conformance_score.json`(140/140)、`gate_semantic_coverage.json`(14 条)均落盘于 11-21 11:00,早于 manifest 扩到 18 个 SKU(11-22 00:10)。本次只读复跑 `check_simready_conformance.ours()` 于现盘资产: **126/180**(`WIKIDATA_LABELS` 0/18、`SEMANTIC_MATERIAL` 0/18、`EXTENTS_METADATA` 0/18); 且 d03fa61 当时的 140/140 本身就是在 1 m 立方上算出来的。

**影响**: 公开仓的 "ESR COMPLIANT 样例三件套" 在 HEAD 不成立; 任何引用 `phys:dimensionsMM` 的下游装配都会把盒子当 1 m、把桶/盒沉进层板一半。

**修法**: `export_sku_usd.py` 把 scale/location 烘进 mesh(或直接导出临时对象)并补 UV; 重跑 label→enrich→三门并把报告重新落盘; 给一致性检查加"网格世界包围盒 ≈ phys:dimensionsMM"的数值对账。

---

## P1

### P1-1 语义覆盖门恒真: 接受任意 `semantics:labels:*` 属性

**证据 [R][S]**: `scripts/gate_semantic_coverage.py:66-75` 的 `resolve_label` 返回祖先链上**第一个**匹配属性(USD 属性按名排序); :97 只要非 None 即算已解析; :154-160 据此算 `labelled_frac`。本次对现盘 18 个资产(只剩 qcode)重跑: **18/18 PASS,`taxonomies=['wikidata_qcode']`**; 旧报告里 14/14 的 taxonomy 也只有 `['material']`——该门从未确认过 `wikidata_class` 可解析。光栅化是逐资产自动取景的单件成像,不涉及场景级分割。

**影响**: 类别/材质标签整体丢失时门仍全绿; 门只证明"我方脚本写的属性我方脚本读得回"。

**修法**: 对要求的 taxonomy(至少 `wikidata_class` + `material`)逐个解析并各自要求 `labelled_frac ≥ 0.98`,缺一即 FAIL; 报告按 taxonomy 分列。

### P1-2 物理门与一致性检查恒真,且不读取被验收的 USD

**证据 [R][S]**
- `scripts/verify_sku_physics.py:22-46` 用 manifest 数字现搭 MJCF 盒子,不 import pxr、不开 USD; 判据 :45-46 只依赖 z 位置; :43 的 KE 只取线速度 `qvel[:3]`。
- 敏感性 [R]: 固定尺寸,质量 1 µg→10 t × 摩擦 0→3,判决集合恒为 {(stable, settled)}; 300 组随机输入(5–500 mm, 1 g–100 kg)中 233 组 µ≤0.6 全过,67 个失败全部是 µ=5.0。`box_tp_00`(1 m 立方)照样 PASS。
- `scripts/check_simready_conformance.py:59` `CORE_OPENUSD = stage is not None`(常真); :96 `EXTENTS_METADATA = dims is not None`(只查属性存在); :97/:128 `MASS_METADATA` 的质量取自 manifest 字典而非 USD; :130-131 `RIGID_BODY_MUJOCO` 走同一 `verify(sku)`。

**影响**: 物理门验证的是"MuJoCo 能让盒子落地",不是资产; 与 P0-1 叠加后,几何与声明相差 8 倍仍三项全绿。

**修法**: 从 USD 读世界包围盒与 `phys:dimensionsMM` 做数值对账后再仿真; KE 计入角速度; 报告记录所用摩擦/质量及其来源字段。

### P1-3 渲染对齐门是手写通过标志,像素门未接入验收

**证据 [S]**: `scripts/esr_acceptance.py:36-39` 的 `gate_render()` 只读 `data/shelf_twin/render_gate.json:5` 的 `"pass": true`(同文件 :3-4、:6 记为 "v26b vs v28d"、"v28d 4.8 > v26b 4.2"、2026-11-21); :53 的 protocol 是字面量,不随 `render_gate.json` 更新; :31-33 的语义门读的是落盘 JSON 而非重跑。HEAD 是 v60,其间经过用户 V50 终裁(推翻评审 mandate)、相机换 M31、V59 层板尺寸修复。`pixel_alignment.json` 不被 `esr_acceptance.py` 读取,且其 `:3` `"ref": "/tmp/blind/ref.jpg"`。与 `docs/reviews/shelf_convergence.md:140-142`("渲染门(参照对齐 D-协议 + 像素分布门)…GPT 仅作感知辅助不入验收链")矛盾——GPT 盲评判决正是通过这个 JSON 进入验收链的。另: 收敛日志自报 37 轮 D 系列对局,仓内原始评审记录只有 v15/v22/v39 与 d1d2d3 四份。

**影响**: "渲染对齐 1/1" 不指向任何现存渲染产物。

**修法**: 删除手写标志,改为绑定具体渲染文件哈希 + 像素门结果的机器可验记录; 盲评原始判决随轮次入库或明确标注为不可复核。

### P1-4 像素分布门无判别力: 白噪声图判 ALIGNED

**证据 [R]**: `scripts/gate_pixel_alignment.py:17-21` 权重与阈值 0.25/0.40; :24-50 `stats()` 不做分辨率归一。以 `data/shelf_twin_ref/primary.jpg` 为参照: 纯白噪声图(σ=0.35)得分 **0.2327 → ALIGNED**; 无内容竖向渐变 0.3264 → NEAR; 纯灰 0.3767 → NEAR; 已入库渲染 `render_v15_final.png` 为 0.210–0.215。同一张图缩到 1/2 再比自身,`edge` 偏差 0.113(贡献 0.019),即分数随分辨率漂移; `pixel_alignment.json` 的高光臂偏差 0.92(权重下贡献 0.074)仍判 ALIGNED。

**影响**: 该门测的是亮度/饱和度分布,与画面内容无关; 文档中以 0.003–0.01 的分差作为"新纪录/连胜"证据,落在该门的噪声与分辨率漂移量级内。

**修法**: 先统一重采样到参照尺寸; 用负对照(噪声/纯色/他店照片)标定阈值并要求负对照必须 DEVIANT; 分布门只作辅助,不作为"数据层面达标"的判据。

### P1-5 Step A 不可重放: 生成器与已提交的 planogram 脱节

**证据 [R][S]**
- 三个脚本写同一路径 `data/shelf_twin/planogram.json`: `make_planogram.py:17`(schema 1.1,`groups`,`tp_*`)、`measure_planogram.py:19`(:154 schema 1.0,键为 `segments`)、`make_planogram_det.py:90-93`(原地覆盖 `groups`,把旧组挪进 `vlm_ref`)。`build_hxl_shelf.py:1050` 读文件时不校验 schema。
- 重放 [R](输出重定向到 /tmp): `make_planogram.py` → 43 组; 再接 `make_planogram_det.py` → **30 组** `tp_*`; 已提交文件是 **36 组** `d_*`,含 `box`×1、`tray_lean`×1、`tray_flat`×1——仓内没有任何脚本能产出这份文件。
- 在已提交文件上重跑 `make_planogram_det.py` → `KeyError: 'tray_lean'`(:66 `UNIT_W` 无托盘键, :83)。
- 仓外依赖: `make_planogram_det.py:20` `DET = Path("/Users/guohongbin/gate-spatial/evidence/m31/hxl_sku110k_detect.json")`; 检测模型 `runs_r0 best.pt` 不在仓(`docs/shelf_twin/planogram.json:36`); 参照照 `data/shelf_twin_ref/` 被 `.gitignore:7` 忽略,`docs/shelf_twin/RECONCILIATION.md:5` 写"源 URL 见 provenance"但仓内无此文件。

**影响**: 陈列证据层无法从仓内重建; 误跑任一生成器即覆盖手工精修结果(`measure_planogram.py` 会让场景脚本直接 KeyError)。

**修法**: `planogram.json` 冻结为唯一真源并加 schema 校验; 生成器一律 `--out` 到新文件且禁止原地覆盖; 检测 JSON、参照照来源/许可(或可再分发的替身)入库。

### P1-6 ESR 资产层与渲染场景断链

**证据 [S]**: `scripts/build_hxl_shelf.py` 全文无 `sku_usd`/`sku_manifest`/pxr 引用,仅 :58、:1049、:1068 三处注释提到 "ESR Step"。场景袋体是布料库网格(基准 0.095×0.19 m,:751),宽=槽宽×0.985、高钳在 0.50–0.75·LEVEL_H(:1271-1273); manifest 袋是 110–150×70×160–210 mm。

**影响**: 三门验收的 18 个 USD 与 `render_v15_final.png` 所代表的场景没有任何几何/材质共享; "ESR COMPLIANT" 不构成对孪生场景的陈述。

**修法**: 二选一并写明——让场景以引用/实例方式消费 USD(尺寸、贴图、语义同源),或把该线如实命名为"独立的 USD 资产样例",不与货架孪生渲染共用合规结论。

### P1-7 零测试覆盖、机器门禁空转、依赖未声明、模块 import 即依赖 bpy

**证据 [R][S]**
- `tests/` 仅 `test_m1.py`(13,导入 `photo_dieline.*`,:12-17)与 `test_pd_guard.py`(13,:91 只子进程跑 `scripts/pd_guard_r3.py`); 本次 `pytest tests/ -q` 26 passed,无一触及货架/ESR 代码。
- `.omp/constraints/rule-enforcer.json:61-127` 中 R-UNITS/R-ARTIFACT/R-NUMERIC/R-FAMILY 声明 `protects: scripts/**`,执行器却只有 `pytest tests/test_pd_guard.py`(:67、:85、:103、:120)——改 `build_hxl_shelf.py` 只要无关测试仍绿就放行。
- `pyproject.toml:13-22` 未声明 `usd-core`/`mujoco`; `pip install -e ".[dev]"` 后 ESR 脚本无法运行。
- `scripts/build_hxl_shelf.py:25` 顶层 `import bpy`,:53 import 时读图,:59-67 import 时读 planogram; [R] Blender 之外 `import build_hxl_shelf` → `ModuleNotFoundError: No module named 'bpy'`。`_tight_box`/`_edge_extend`/`can_label`/`pil_tag_rail` 等纯 numpy/PIL 逻辑因此不可单测。

**影响**: 该线 60+ 次提交的全部行为正确性只靠人工看图与全帧差分。

**修法**: 把贴图合成、planogram 消费、门禁判据抽到无 bpy 模块并补 pytest(含负对照); rule-enforcer 为该线增加一条真实执行该测试的检查; 依赖分组声明 `esr = ["usd-core", "mujoco"]`。

### P1-8 "实测尺寸"实为占位默认参数

**证据 [S]**: `data/shelf_twin/sku_manifest.json:7` `"dimension_source": "make_pillow_bag 参数 + 占位资产规格 (实测单源, …)"`; `scripts/make_pillow_bag.py:17-23` 默认 140/200/70/18 mm——12 个袋的厚度全部恰为 70(= `DEPTH` 默认); `barrel_tp_00` 75×75×260 = `barrel_placeholder` 默认(`build_hxl_shelf.py:367`); `box_tp_00` 120×45×190 = `box_placeholder` 默认(:422、:428)。质量字段无任何来源。`docs/shelf_twin/DOMAIN_STUDY.md:37` 把 `phys:dimensionsMM` 表述为"实测尺寸"。与 `README.md:19` 证据分级(实测 > 可信来源 > 约束推导 > 模型推断 > 默认值)相悖。

**影响**: 证据等级被标高两级(默认值 → 实测),且该标签随 USD 的 `phys:dimensionsMM` 对外传播。

**修法**: manifest 增加 `dimension_evidence: measured|catalog|assumed` 与来源字段,现值如实标 `assumed`; 文档改口为"占位规格"。

### P1-9 第三方产品照裁片入库,无来源/许可记录(违反 ADR-011)

**证据 [S]**: `assets/food_patches/cookies.png`(已目检: Oreo 夹心饼干与带品牌包装的背景)由 `docs/reviews/shelf_convergence.md:215-216` 自述为京东在售图"净区裁剪…PROVENANCE: JD pid 记录",但仓内 grep 不到任何 pid/许可记录; `THIRD_PARTY_NOTICES.md:20-27` 的数据资产只列 gable-top 参照照,并承诺"任何进入本仓的照片/数据集样本将携带来源、许可与再分发元数据"; `docs/adr/README.md:17`(ADR-011)同旨。另: Poly Haven HDRI 与 MiniMax H3-Image 生成的 `assets/ai_prints/`(12 张)也未列入 NOTICES。

**影响**: 公开仓再分发第三方品牌产品摄影且无可审计许可,直接触碰本仓自定的治理红线。

**修法**: 补 `assets/PROVENANCE.md`(逐件: 来源 URL/pid、许可、衍生物)或替换为自制/CC0 素材; HDRI 与 AI 印刷的许可条目同步入 NOTICES。

### P1-10 `ROOT` 硬编码绝对路径,且渲染时写 tracked 目录

**证据 [S]**: `scripts/build_hxl_shelf.py:42` `ROOT = Path("/Users/guohongbin/photo-dieline")`(同线其余脚本用 `Path(__file__).parent.parent`,如 `make_planogram.py:16`)。运行期写入: :1197-1198 `boxfront_*.png` 无条件覆盖写入 `assets/pillow_designs/`(该文件已 tracked: `boxfront_design_20_2.png`); :1215-1219、:1247 设计图缺失时写入同目录; :1253-1267 派生 `.sat/.ar` 写入同目录(已 ignore)。

**影响**: 仓克隆到任何其他路径后,该脚本要么找不到资产,要么静默读写**原路径那一份**仓; 每次渲染都可能弄脏工作区。

**修法**: `ROOT = Path(__file__).resolve().parent.parent`; 所有派生图统一写到 `output/` 或按内容哈希命名的缓存目录; `boxfront_*` 移出 tracked。

---

## P2

### P2-1 贴图缓存按文件名失效,跨机/跨版本不可复现

**证据 [S]**: `build_hxl_shelf.py:200-202`(`/tmp/crop_{stem}_{seed}.png`,存在即返回)、:606-608(`*.tight.png`,存在即返回,改算法不失效)、:85/:96/:114/:126/:169/:193(固定 `/tmp/hxl_*.png` 全局名); `scripts/enrich_sku_usd.py:21-26` 从 `/tmp/crop_{color}_*.png` 取 `hits[0]` 决定 USD 贴图——USD 富化结果取决于渲染脚本留在 `/tmp` 的残留。`.gitignore:11-14` 忽略了派生图但没有任何版本/哈希键。

**影响**: 开发机与新克隆同一提交产出不同贴图(白翼修复后旧 `.tight.png` 仍是旧算法结果); USD 贴图不可复现。

**修法**: 缓存键加入源文件内容哈希 + 算法版本号; 缓存目录进 `output/cache/`; `enrich_sku_usd.py` 不读 `/tmp`。

### P2-2 `size=1` 半长病未清扫: 灯箱体、饰带、立柱 [INFERENCE]

**证据 [S]**: 本文件已两次记录该病(:1057-1058 层板、:486-487 托盘),但同模式仍在: :1012-1015 `signbox` `primitive_cube_add(size=1)` + `scale=(SHELF_W/2+0.01, 0.05, 0.25)`——x 是半长语义而 z=0.25 是全长语义,实际宽 1.21 m(招牌 2.4 m); :1034-1037 `fascia` 同; :1400-1402 立柱 `scale=(0.022, 0.03, top_z/2+0.08)` → 实际只覆盖 z∈[0.615, 2.005] m,离地 61 cm。按 Blender 语义 `size=1` 即棱长 1 m。

**影响**: 结构件尺寸减半/悬空; M31 取景下大概率不可见,属潜伏缺陷,换机位即现形。

**修法**: 全文件 `primitive_cube_add(size=…)` 逐处打印 `.dimensions` 对账(本文件自己的探针纪律),统一 `size=2` + 半长 scale。

### P2-3 `main()` 巨石与实验探针残留

**证据 [S]**: `main()` 占 :969-2101 共 1133 行(文件 54%),内含 37 个嵌套函数/lambda、15 处函数内 import、10 个 argv 开关、9 个环境旋钮; :1467-2097 共 631 行(30%)是 `--heal/--side/--v37a/--v37b/--v38/--v40/--collide/--depthtable/--topo` 探针分支。隐式依赖: `--v40` 块(:1953-2006)使用的 `bags` 只在更早分支定义,单独传入即 NameError; `--v38` 块(:1852 起)用到的 `BVHTree` 与 `ORIG36`(:1866、:1871)分别依赖更早分支的 import 与 `--v37b`(:1600-1601)。探针只打印汇总(:2052、:2096),`HXL_SHELF_OK`(:2101)无条件打印——没有阈值、没有退出码; 且碰撞/悬浮检查只看名字以 `bag` 开头且 lv≥3 的对象(:2011-2013、:2062-2064),桶/盒/托盘与 L1–L3 不在检查内。

**影响**: 生产路径与已废弃的"顶点手术"路线(`--heal`、`--v37a`,技能记录已禁)混在一个函数里; "穿板=0/全部落板"的验收标准只存在于文档。

**修法**: 场景装配(夹具/排面/灯光/相机)拆成独立函数或模块; 探针移到 `scripts/probes/`,各自带阈值与退出码; 删除已判废弃的分支。

### P2-4 死代码超出已记账范围

**证据 [S]**(AST 扫描 + 调用点 grep): 已记账的只有 `img_bag_thin`(:262,`shelf_convergence.md:341`)。此外模块级零引用: `pil_price_tag`(:117)、`pil_tag_single`(:172)、`img_bag_curved`(:856-946,91 行)、`TIGHT_CACHE`(:537); `main()` 内: `bag_names`(:1048)、`s0`(:1091)、`fbot`(:1188)、`flags`(:2024); :684-685 对 `coat_w/coat_r` 形参赋值被 :722-726 无条件覆盖(形参失效); :1469 `… if False else …`。另: 收敛日志判"挂架撤线维持"(`shelf_convergence.md:80`),但 `build_pyramid_rack_v2` 仍无条件入场景(:1457-1463)并连带保活 `crop_bag`/`ASSETS`/`pillow_bags`(13 MB)。

**修法**: 删除上述函数/变量; 挂架要么按文档撤出场景,要么修正文档。

### P2-5 重复逻辑

**证据 [S]**
- 发光贴图材质样板 ×5: :221-259、:267-285、:442-453、:678-733、:859-906(`bag_material` 文档串称"从 img_bag_curved 抽出",但原函数未改为调用它)。
- 枕袋网格 ×2 且已漂移: `make_pillow_bag.py:26-91`(带 UV)与 `export_sku_usd.py:25-65`(无 UV)——P0-1 的"袋无 UV"即此漂移。
- 碰撞探针样板 ×5–8: `_wbvh/_wt` 定义于 :1483、:1589、:1741、:1863、:2057; 同一对遍历条件重复于 :1498-1504、:1549-1558、:1621-1627、:1640-1646、:1771-1777、:1914-1920、:2025-2030、:2069-2075。
- MuJoCo 静置 MJCF ×3: `verify_sku_physics.py:26-37`、`check_simready_conformance.py:101-116`、`bench_simready_physics.py:37-60`; 摩擦表 ×2 且键集不同(manifest vs `check:22-23`/`bench:20-21`)。
- 家族色表 ×4(`make_planogram.py:36-37`、`measure_planogram.py:22-26`、`build_hxl_shelf.py:71-76`、`enrich_sku_usd.py:58-64`),靠注释"同序"维持; 夹具常量 ×4(层距 0.38 m vs 310 m 并存)。
- 两份 `planogram.json`: 夹具尺寸读 `docs/shelf_twin/planogram.json`(:59),分组读 `data/shelf_twin/planogram.json`(:1050)。
- 字体路径 `/System/Library/Fonts/STHeiti Medium.ttc` 硬编码 8 处,同时存在 helper `_load_font_cn`(:32)。

**修法**: 抽 `materials.py`/`meshes.py`/`settle.py`/`probes.py` 四个小模块,色表与夹具常量单源。

### P2-6 数据层字段未被消费或被硬编码覆盖;`design_id` 不是设计标识

**证据 [S]**: 场景只读 `levels[].groups[]` 的 7 个字段(:1093-1098);`sign_band`/`fixture`/`partial`/`vlm_ref`/`uncertainty_note` 全文未读(grep 无命中)。`facings` 在 :1072-1081 被归一到 ≤34、<14 再放大,在 :1101-1104 又按槽宽/密度常数改写; 价签用硬编码 `tag_texts`(:1047)按 `(lv+gi)%7` 取值(:1085),而 `docs/shelf_twin/planogram.json` 的 `price_tags` 未读。`LV_GIDX`(:47、:1108)按"层内首见顺序"分配设计图 [R]: `d_0` 在 L2/L3/L4/L5/L6 分别映射到 design_08/10/24/29/30 五种不同印刷(红袋/黄桶/棕袋/青袋/托盘),`d_4` 同时是黄袋、粉桶、蓝托盘——数据层无法回答"某组用哪张印刷"。

**影响**: "数据层管结构"只在颜色/形态/粗略宽度上成立; 增删任一组会让其后所有组换印刷。

**修法**: 数据层显式存 `design_asset`(路径或 ID)与 `facings_final`; 场景把归一/钳制结果回写或输出 `resolved_planogram.json`。

### P2-7 随机数与抽取顺序耦合,靠回放垫片维持

**证据 [S]**: 每层一条 `rng = default_rng(lv*31+7)`(:1069),在组×排×件的循环里有 ~22 个抽取点(:1097、:1132-1136、:1142-1152、:1165、:1272-1280、:1286-1296、:1306、:1318-1320、:1327-1336、:1345);任何抽取次数变化都会重排同层其后全部随机态,于是有 `_legacy_tray_rng`(:461-481)——只为"回放旧抽取序列"而空转。托盘前后两排用同一 seed(:1127-1128),缺位模式两排相同。没有任何冻结种子回归测试,验收靠人工全帧差分。

**修法**: 改为按 `(lv, group, row, slot, 用途)` 哈希派生的独立种子(文件里 :1322、:369 已有此写法),删除回放垫片; 加"同 commit 两次 NORENDER 位置表逐字节一致"的测试。

### P2-8 36 张设计图 = 12 张 AI 印刷 ×3 份字节相同副本;三工艺分支对 AI 路径失效

**证据 [R]**: md5 比对——`design_{00..35}_{0..2}.png` 与 `assets/ai_prints/*.png` 一一对应,每张 AI 印刷出现 3 次。代码 :1213-1219 在 `dpath` 不存在时先复制 AI 图,`style==1/2` 的"极简/牛皮纸"处理(:1228-1246)因此不可达。tracked 体积: `assets/pillow_designs/` 57 MB,其中 38 MB 是 `ai_prints/`(19 MB)的重复。

**影响**: `shelf_convergence.md:183、:205` 的"三工艺体系/30 款 × 三工艺"在现资产上不成立; 仓体积无谓翻三倍。

**修法**: 删除 `design_*.png`,场景按 `(gidx % 12, style)` 直接引用 `ai_prints/` 并在运行期应用 style。

### P2-9 布料库每次运行重算 72 次仿真;碰撞体疑似未启用且残留场景 [INFERENCE]

**证据 [S]**: `build_cloth_library(n_per=6)`(:740-853,:1052 调用)每次运行做 72 次 cloth 仿真,结果不落盘缓存。侧壁/前压板对象(:813-838)创建后既未启用 Collision 物理、也未被 unlink(:852 只 unlink 布料源对象),仍留在挂到场景的 `clothlib` 集合里。[INFERENCE] Blender 布料只与启用了 Collision 的对象碰撞,故 D36"接触形变"(`shelf_convergence.md:288`)可能从未生效; 残留的 ~158 片无材质面板位于原点附近 z<0.21 m,M31 取景外、默认取景内是否可见未核。

**修法**: 一次探针打印 `[o for o in lib_col.objects if o.collision]` 与各变体 `.dimensions`; 若确认则给碰撞体加 Collision 并在 apply 后删除; 布料库烘焙为磁盘缓存并带版本键。

### P2-10 官方资产"材质→摩擦"映射失效,对标协议并未镜像

**证据 [R][S]**: `bench_simready_physics.py:29-33` 对 token 数组属性 `str(attr.Get())` 得到 `"[rubber]"`,:85 `FRIC.get(mat, 0.5)` 落到默认值; `data/shelf_twin/bench_simready_physics.json` 三件官方资产 friction 全为 0.5(表内 rubber=0.7、clear_glass=0.4、plastic=0.4); `check_simready_conformance.py:148` 同。与 `bench_simready_physics.py:4-5`"协议与 verify_sku_physics 完全镜像"及 `docs/reviews/simready_benchmark.md:39-43` 表述不符(判决不受影响,因为 P1-2 已证摩擦与判决无关)。

**修法**: 取数组首元素并去括号后查表,查不到即 FAIL 而非静默默认。

### P2-11 外围脚本缺陷集

| 脚本:行 | 缺陷 | 证据 |
|---|---|---|
| `make_planogram_det.py:2-9` vs `:24-72` | 文档串称"x-gap>0.5×中位袋宽分簇 / 与 VLM 组 x 重叠≥40% 继承 / `--render-check`";实现是膝点分簇 + 按序号比例继承,无 argparse; `W`/`W_IMG`/`med_w` 未用 | [S] |
| `make_planogram_det.py:35-41` | 恰 3 个检测时 `gsorted[2]` 越界 | [R] `clusters(n=3)` → IndexError |
| `post_shelf_photo.py:27` | 原地覆盖输入渲染图,跑两次叠两次噪声,原始 Cycles 输出丢失 | [S] |
| `post_shelf_photo.py:17-19` | PIXEL_GATE FAIL 不改变退出码 | [S] |
| `esr_acceptance.py:7` vs `:57` | 文档串写 `docs/shelf_twin/`,实写 `data/shelf_twin/` | [S] |
| `esr_acceptance.py:60` | NOT COMPLIANT 仍退出码 0 | [S] |
| `enrich_sku_usd.py:78-84`、`:80` | `fail` 永远为 0;USD 无 manifest 条目时 `next()` 抛 StopIteration(同情况的 `label_sku_usd.py:62-65` 是记 fail) | [S] |
| `label_sku_usd.py:39-41` | 注释称"apiSchemas apply + 裸属性双写",实际只写裸属性;`api` 变量未用 | [S] |
| `check_simready_conformance.py:183` | 表头硬编码 "ESR(14)/官方(3)",现为 18 | [S] |
| `make_pillow_bag.py:51-55`、`:66` | 先建 4 个顶点又重建(孤儿顶点);`(0 if zs == 0 else 0)` 空操作 | [S] |
| `bag_print.py:100-108` | 条码/净含量 y 坐标用 `S` 而非 `H`,H=1707 时落在食品窗上方而非底部横幅(仅影响程序化回退路径) | [S] |

**修法**: 逐项按表修;门禁类脚本统一"失败即非零退出"。

### P2-12 终版渲染与环境旋钮不可复现

**证据 [S]**: 仓内最新货架渲染是 `docs/images/shelf_twin_v56.png` 与 `docs/shelf_twin/render_v15_final.png`(v15); HEAD 对应的 V57–V60 渲染未入库。9 个 `HXL_*` 环境旋钮在仓内文档只出现一次(`docs/reviews/ftc_camera_fit_v17.md:25` 的 `HXL_CAM=M31`); Blender 版本只出现在 USD 的 `doc` 字段; M31 相机常数(:1441-1444)是从仓外 `gate-spatial` 拟合结果手抄的,且该拟合触搜索域上界、留一验证 FAIL(`ftc_camera_fit_v17.md` 判决节)。

**修法**: 入库一份 `renders/README` 记录终版渲染的 commit、Blender 版本、全部环境变量与 argv; 相机参数连同拟合报告放入仓内 JSON 由脚本读取。

---

## P3

### P3-1 `data/shelf_twin/planogram.json` 元数据陈旧且自相矛盾,无逐组证据标注

**证据 [R][S]**: 顶层 `source.facings="vlm_est"` 与"桶罐列在每层左端"仍在,而 `uncertainty_note` 写"L1 全袋无桶"、分组 facings 来自检测与手改; 当前 `groups` 无 `facings_evidence`; `detection_note` 的组数在 7 层中 6 层与实际不符(如 L3 "→ 5 组"实为 9,L5 "→ 5 组"实为 3); 全部 `x0_frac/width_frac` 是两位小数的手填值; `fixture.level_height_m=0.38` 与场景实际用的 0.31 并存且未被读取。证据强度实际只有 VLM 读图、像素量测、单视角标定(±15%,`docs/shelf_twin/planogram.json:6-9`),没有任何实测尺寸。

**修法**: 每组补 `evidence: {method, source, confidence}`,过期字段删除或标 `superseded_by`。

### P3-2 `docs/shelf_twin/planogram.json` 内部不一致;证据指针指向不存在的文档版本

**证据 [S]**: `total_height_mm=2420`(:18)≠ `bottom_lip_mm 450 + 7×310 = 2620`(:7-9、:15); `build_hxl_shelf.py:3`、`make_planogram.py:105`、`measure_planogram.py:166`、`data/shelf_twin/planogram.json:16` 四处引用 "RECONCILIATION.md v2",而该文件标题是 "对账清单 v1"。

**修法**: 修正总数并给 RECONCILIATION 加版本号或改引用。

### P3-3 顶层文档对该线零记载;多处注释陈旧

**证据 [S]**: `README.md`、`DESIGN.md`、`docs/adr/README.md` 对货架孪生/ESR/SimReady 无一字(grep 无命中),而该线已占 60+ 次提交、tracked `assets/`+`docs/images` 162 MB。`shelf_convergence.md:86` "7 层 43 组" 对应现 36 组; `build_hxl_shelf.py:6-14` 头注台账(层距 0.38、板厚 0.025、旧相机位)与实现不符; :1051 "48 网格"、:741 "每味 4 变体" 对应实际 72; :1280 注释 "4%" 对应实际 5%。

**修法**: README 增一节"货架孪生 / ESR 样例(状态: 实验性)"并链接本报告; 头注台账删除或改为自动生成。

### P3-4 贴图 datablock 重复加载;"共享网格"只对 L1–L3 成立 [INFERENCE]

**证据 [S]**: 6 处 `bpy.data.images.load(str(path))` 均未传 `check_existing=True`; `bag_material` 逐袋调用,同一张 `.sat.png` 被重复加载。[INFERENCE] 每份 768×1556 解码约 5 MB,数百袋量级为 GB 级冗余。:1302-1303 对 lv≥3 的袋 `co.data = co.data.copy()`,布料库"网格共享"只在 lv<3 成立。

**修法**: `load(path, check_existing=True)` + 每袋独立 Mapping 节点。

### P3-5 像素门 spectral 臂误用直方图距离;标量臂超出声明值域 [INFERENCE]

**证据 [S]**: `gate_pixel_alignment.py:67` 把 24 bin 的有符号 log 幅度剖面交给 `wdist`(:53-55,按 `cumsum/sum` 归一的直方图 EMD),文档称"EMD"; :64-65 高光/暗部 ×10 可超过 1,与 :59 注释"归一化偏差 [0,1]"不符。实际影响未量化。

**修法**: spectral 臂改用去均值的剖面 L1/L2 距离; 标量臂裁到 [0,1] 或改注释。

---

## 对委托六问的逐项结论

| 问 | 结论 | 对应条目 |
|---|---|---|
| (a) 架构 | `main()` 1133 行;6 个模块级可变全局字典承担跨阶段状态;夹具常量/色表/价签多处硬编码并与数据层重复;死代码比已记账多 5 处;材质/网格/MJCF/探针样板各重复 2–8 次 | P2-3、P2-4、P2-5、P2-6 |
| (b) 可复现性 | 种子确定但顺序耦合;缓存按文件名失效;HDRI、AI 印刷、食品补丁、枕袋资产已 tracked,参照照/官方资产/检测 JSON 不在仓;终版渲染与运行旋钮未入库 | P1-5、P1-10、P2-1、P2-7、P2-12 |
| (c) 测试与门禁 | 无 pytest 覆盖;rule-enforcer 对 `scripts/**` 的保护由无关测试执行;pxr/mujoco 未声明;模块 import 即依赖 bpy | P1-7 |
| (d) 三门判据 | 语义门接受任意标签;物理门不读资产且对输入不敏感;渲染门是手写标志;像素门白噪声 ALIGNED;唯一非自证证据是 3 件官方资产"能跑过"——但它们证明的是门不设防而非门有效 | P1-1 ~ P1-4、P2-10 |
| (e) planogram 证据强度 | 仅 VLM/像素/单视角标定,无实测;逐组证据字段已丢失;`design_id` 非设计标识;manifest "实测" 实为默认参数 | P1-5、P1-8、P2-6、P3-1 |
| (f) README/DESIGN 出入 | 顶层文档对该线零记载;收敛日志与代码在挂架、组数、三工艺、三门构成上手多处不一致 | P1-3、P2-4、P2-8、P3-3 |

## 本次运行的只读命令(摘要)

- 全文阅读: `build_hxl_shelf.py`(2105 行)及全部目标脚本、`data/shelf_twin/*.json`、`docs/shelf_twin/*.md`、`shelf_convergence.md`、`simready_benchmark.md`、`ftc_camera_fit_v17.md`
- `git show`/`git log`/`git ls-files`/`git check-ignore`; md5 比对设计图与 AI 印刷
- pxr 读回 18 个 USD 的世界包围盒、标签属性、UV; `gate_semantic_coverage.py --out /tmp/...`; 内存调用 `check_simready_conformance.ours()`、`verify_sku_physics.verify()`
- 以重定向输出的方式重放 `make_planogram.py`、`make_planogram_det.py`
- `gate_pixel_alignment` 的负对照(白噪声/纯色/渐变/自身缩放)
- `python3 -m pytest tests/ -q`(26 passed)
- 证据产物: `/tmp/pd_recheck/twin_audit_evidence/sem_cov_now.json`、`/tmp/pd_recheck/twin_audit_evidence/sim/*.json`

## 未核项

- 以下为 [INFERENCE],按约定未运行 Blender,需一条探针确认: P2-2 三个结构件的实际 `.dimensions`; P2-9 碰撞体是否生效及残留面板是否入画; P3-4 内存占用。
- GPT 盲评各轮分数只有收敛日志自报,无法从仓内复核。
