# 模板动物园制造合理性复查 (photo-dieline HEAD 54b81ca, 只读)

范围: `src/photo_dieline/parametric/*.py` (15 模块 100 类 8980 行) + `src/photo_dieline/batch.py`.
口径: 以代码为准; 所有数字由仓外探针脚本对默认参数实测 (复用仓内 `build_ir/from_raw/fold_all/cut_segments/run_qa`), 未改仓内任何文件.
版本钉定: 审计期间 (08:42–08:48) 工作区出现他人改动 (`batch.py`/`cli.py`/`core/ir.py`/`export/pdf.py`/`export/svg.py` 被修改, 新增 `export/layout.py`), 非本审计所为; 为避免污染, 全部数字在 `git archive 54b81ca` 导出的快照 `/tmp/pd_recheck/head_54b81ca` 上复跑确认 (见 §8), 文中行号均指 HEAD 54b81ca.
`[INFERENCE]` = 基于行业常规的推断, 非代码可直接证明.

## 0. 结论摘要

1. `photo-dieline batch` 实跑: **100/100 GREEN, 5.4 s**, 最差闭合残差 5.8e-05 mm (tray_6corner), 无失败项. 但 GREEN 只说明默认参数能过 G02–G10, 不说明可制造.
2. **P0 × 1**: 15 类在默认参数下导出的 CUT 层切穿结构 (14 类净图面板重叠 + 6 类折线两缘顶点细分不一致, 两者有重叠), batch 仍判 GREEN.
3. **P1 × 6**: 37 类粘口折回自身墙板 (筒体不闭合); 2 类隔板十字无槽相穿且 G06 检不出垂直穿越; divided_tray_3comp 底板多边形自交缺 1/3; closure 覆盖不足且 batch 无负探针 (1597 条折线中 145 条 180° 翻折不被检出, 1343 条判据中 27 条恒真); 2 类食品盒无底; G06 实际只测 50.5% 的面板对.
4. **P2 × 11 / P3 × 6** (另 P1-5 表内有 5 类 P2 级开口): 板厚是死参数且瓦楞约束缺失、插舌与锁扣零间隙、RSC 折翼无间隙、两件式 web 用折线相连、折线 MOUNTAIN/VALLEY 相对图面不一致、窗框共面假折线、validate 边界缺口、星形托盘角缝无连接等.
5. 默认参数按各模块 `validate_params` 全部合法 (没有一类落进自身非法区); 问题在于 validate 与 closure 的判据本身覆盖不到这些制造规则.
6. 修复顺序建议: 先给 G03 加"面板两两重叠面积 = 0"与"CUT 段不得落入他板内部或折线"两条判据 (可一次拦住 P0), 再统一粘口 tdir, 再把负探针接进 batch.

## 1. batch 实跑记录

- 命令: `photo-dieline batch --help` 查看用法后执行 `PYTHONDONTWRITEBYTECODE=1 photo-dieline batch --out /tmp/pd_recheck/zoo100` (5.9 s, 远低于 15 分钟上限); 之后在 HEAD 快照上复跑一次 (输出 `/tmp/pd_recheck/zoo100_head`, 5.3 s, 100/100 green), 两次结果一致.
- 输出目录改到仓外: 仓内 `output/` 虽已 gitignore, 但 `output/zoo100/batch_report.json` (11-19) 属仓内文件, 按只读约定不覆盖.
- 结果 (`/tmp/pd_recheck/zoo100/batch_report.json`): total_classes=100, green=100, gate_green_ratio=1.0, elapsed_s=5.4; G02–G08、G10 各 100 PASS (G01 按 batch 设计不计); non-green 无.
- `qa_worst_closure_mm`: 98 类为 0.0, tray_6corner 5.8e-05, food_noodle_pail 1e-06.
- 家族分布: prism 28, pyramid 8, clv 7, food 7, gable 6, rsc 6, tray 5, tube 5, cone 3, crashlock 3, mailer 3, envelope 2, 其余各 1.
- 副产物: 运行期 1 条 `RuntimeWarning: invalid value encountered in divide` (`render/twin.py:149`), 来自面板内共线分点造成的零面积三角 (三角扇自 v0 展开); 退化三角出现在 18 类 (prism_dust × 9, egg_tray_2x4, rsc_display_panel, two_piece, window_box, prism_tuck_window, mailer_diecut, clv × 3).

## 2. P0

### P0-1 导出 CUT 层在默认参数下切穿结构 (15 类, batch 判 GREEN)

机制: `export/svg.py:120-132` 的 `cut_segments()` 只排除"与某条折线 `seg_2d` 两端点完全相等"的面板边, 其余面板边全部进 CUT 层 (SVG `export/svg.py:51-55`, PDF `cli.py:83-84`). G03 (`qa/pipeline.py:91-113`) 只数并集环数, 不查面板重叠, 也不查 CUT 落点. 两类触发:

**(a) 净图面板重叠 (14 类)**: 两块面板占用同一块材料, 后建面板的边成为落在他板内部的 CUT.

| 类 | 净图重复面积 mm² | 落入他板内部的 CUT mm | 代码位置 | 后果 |
|---|---|---|---|---|
| egg_tray_2x4 | 15680 | 440 | `sundry_family.py:268` (wAf 建在 (0,0)–(W,H), 即底盘前带内), `:272` (dvm), `:277-278` (cs/cn 与母墙共位) | 前墙顶边成为横贯底盘的全宽切断线, 前墙与 6 片横隔被切离底盘 |
| food_sushi_tray | 26559 | 727 | `food_packs.py:667` (`shift = yfl - uvs[4][1]` 把盖盘底平移到托盘之上而非 web 之后) | 盖底与盖墙压在托盘底和托墙上 |
| food_noodle_pail | 4431 | 610 | `food_packs.py:332-349` (tf 展开位取径向外侧, 落在梯形墙内), `:352-368` (wg) | 8 片收顶片与 2 片对折翼的边切在墙内 |
| crashlock_divider | 5160 | 226 | `struct_ext.py:436-437` (bF), `:486-489` (dvl/dvt 建在 bF 之上) | 隔板边切在底板内 |
| divided_tray_3comp | 6250 | 309 | `special_shapes.py:352-356` | 同上, 另见 P1-3 |
| cup_sleeve | 960 | 312 | `sundry_family.py:167-168` (hemB 用 `+hd*um` 径向外偏; 应朝锥顶取 `-um`) | 12 片底缘折片占掉每片墙底 5 mm, 三边被切开后整片脱落 |
| pyramid_frustum_n4/5/6/7/8/9/10/12 | 1296–14510 | 204–1669 | `odd_family.py:137`, `fan_net_ext.py:141` (`Fk = mid + a_t*u(k+0.5)`, 尖点取径向外侧 = 母墙内) | 每片顶三角完全落在母墙内, 母墙顶部被切出三角形开口 |
| gable_screw_cap | 258 | 428 | `brick_family.py:292-302` (`_sliver_quads`: 相邻裙片在孔心互相重叠, 首末片压入坡面) | 16 片裙片互切 |

**(b) 折线两缘顶点细分不一致 (6 类)**: 模板为满足 G03 "折线端点须为多边形顶点"在面板里插入共线分点, 折线 `seg_2d` 仍是整段, 被细分的一侧不再与折线端点相等, 铰链有材料的部分被画成 CUT.

| 类 | 被画成 CUT 的铰链实体段 | 代码位置 |
|---|---|---|
| rsc_handhole | 130 mm = e_t0 两侧肩 65+65, 即顶翼与前墙的全部实际连接 | `struct_ext.py:308-311` (w0 顶缘被提手缺口断开), 折线 `:338` |
| egg_tray_2x4 | 860 mm (前后墙与底盘铰链各 160 全宽, 左右墙各 80 全深, 另 380 为重叠段) | `sundry_family.py:268-269` |
| divided_tray_3comp | 440 mm (e_wf 180 全宽, e_wb 120, 另 140 为隔板重合段) | `special_shapes.py:352` |
| crashlock_divider | 136 mm (e_bF 100 全宽, 另 36 为 dvt 重合段) | `struct_ext.py:436` |
| gable_screw_cap | 38 mm = 两鳍过脊铰链各 19, 即鳍与坡面的全部实际连接 | `brick_family.py:317-320` |
| food_noodle_pail | 36 mm = e_tf0/e_tf4 实际有墙支撑的全部 18+18 | `food_packs.py:264-276`, `:346` |

实测方式: 直接调用仓内 `cut_segments(ir)`, 与折线段求共线重叠长度, 并与他板内部求交.
修法: G03 增加两条判据 — 面板两两交集面积 ≤ 1e-6 mm²; 每条 CUT 段与他板内部、任一折线的重叠长度 = 0. 模板侧按上表逐类改展开位 (frustum 顶三角需改为独立扇形或只取交替墙位).

## 3. P1

### P1-1 粘口折回自身墙板, 筒体不闭合 (37 类)

证据 (折叠后粘口只与父面板共面重叠, 实测重叠面积 = 粘口面积 100%):

| 模块:行 | 类 | 数量 |
|---|---|---|
| `generic_prism.py:114` | prism_n{4..12}_{open,tuck} | 18 |
| `prism_dust.py:166` | prism_dust_n{4..12} | 9 |
| `odd_family.py:368` | tube_glue | 1 |
| `fan_net_ext.py:379` | tube_glue_n8, tube_glue_n24 | 2 |
| `special_shapes.py:261`, `:294` | hexagonal_flip, tube_double_seam | 2 |
| `struct_ext.py:444`, `:558` | crashlock_divider, tube_cap_end | 2 |
| `tray_family.py:243`, `:330` | crashlock_rect, crashlock_rect_tuck, lockbottom_123 | 3 |

这些折线用 `tdir=(1,0,0)`, 即沿首墙 w0 自身方向; 同拓扑的正确写法已在仓内: `rsc_family.py:132`, `closure_variants.py:94`, `box_essentials.py:213`, `struct_ext.py:135` (prism_tuck_window 用末墙方向 `face5`), `odd_family.py:259` (cone_wrap 搭接缝).
closure 判据对此恒真: 只验"粘口落在 w0 平面" (`generic_prism.py:198`, `odd_family.py:402`, `fan_net_ext.py:413`, `struct_ext.py:584`), tube 三类甚至把"粘口远缘与 w0 远缘重合"写成判据 (`odd_family.py:404`, `fan_net_ext.py:415`, `struct_ext.py:585`).
修法: tdir 改沿末墙 (prism 系为 `-tangent[n-1]`); closure 改为"粘口与非父面板的共面重叠面积 ≥ 粘口面积 × 0.98".

### P1-2 隔板十字无开槽相穿, 且 G06 检不出垂直穿越 (2 类)

- `special_shapes.py:355-356`: dvl 全宽 W、dvt 全深 D、同高 H, 两片实板在 x=xt, y=D/2 处十字相穿 (实测交线 35 mm). 备注写"T 字相贯", 但 dvt 全深会分成 4 格, 不是 3 格.
- `struct_ext.py:486-489`: 同样十字; `:932` 还把 `{"dvl","dvt"}` 写进 `allowed_overlap` 显式放行.
- G06 `_intersect3d` (`qa/pipeline.py:283-312`) 把 B 投到 A 平面再算面积, 两面垂直时投影退化为线段, 恒返回 False. 用线段求交的稳健探针复测: 两类均检出, divided_tray_3comp 标 `G06_MISS`.
修法: 横隔改半深 (止于纵隔) 或在 IR 增开槽特征; G06 增加"边-三角形穿越"检测.

### P1-3 divided_tray_3comp 底板多边形自交, 缺 1/3 面积

`special_shapes.py:352`: `[(W,D),(0,D),(0,0),(xt,0),(W,0),(xt,D)]` 在 `(W,0)` 后漏了 `(W,D)`, 多边形自交 (`shapely is_valid_reason` = `Self-intersection[60 90]`), buffer(0) 后面积 10800 mm² 而 W×D = 16200 mm², 右上三角 5400 mm² 缺失; 并集出现 2 个非预期孔 (850、1350 mm²); e_dvl 靠右 60 mm 无底板支撑.
修法: 顶点序改为 `[(xt,0),(W,0),(W,D),(xt,D),(0,D),(0,0)]`; G03 增加面板 `is_valid` 判据.

### P1-4 closure 判据覆盖不足, batch 无负探针

- `batch.py:32-58`: 只用默认参数 build 一次并读门状态, 没有任何扰动; `tests/test_m1.py` 只覆盖 gable_top, 不调用任何 `probe()`.
- `probe()` 只存在于 6 个模块 (box_essentials, closure_variants, food_packs, special_shapes, struct_ext, sundry_family, 共 40 类), 另 9 个模块 60 类没有; 且全仓 (src/tests/scripts) 无调用方. 手动执行这 40 类的 probe 全部通过 (扰动后残差 1.46–41.79 mm).
- 通用负探针 (每条折线绕真实铰链轴 ±35° 与 180° 扰动 tdir, 取 closure 最大残差, 门限 0.2 mm) 结果: 1597 条折线中 30 条 ±35° 不检出, 145 条 180° 不检出.

| 类 | ±35° 不检出 | 180° 不检出 | 原因 |
|---|---|---|---|
| gable_top | e_glue, e_sl_fb, e_sl_ff, e_bk_fl (4/12) | 同左 | `gable_top.py:62-84` 无粘口判据; `flapF.far == flapB.attach` 只用到 flapB 的铰链点; 鳍只验共点 |
| gable_window_front | 同上 4 条 (4/15) | 同左 | `struct_ext.py:259-290` 同构 |
| gable_screw_cap, gable_fin_gap_wide | e_glue, e_bk_fl | 同左 | `brick_family.py` |
| gable_finless | e_glue, e_bk_fl | 加 e_sl_gf | `gable_variants.py:127-155` |
| rsc_handhole | e_b1, e_b3, e_t1, e_t3 (4/12) | 8/12 | `struct_ext.py:365` 的 `mnr` 实为 b2/t2, 小翼完全没验 |
| two_piece | 10/26 | 13/26 | `box_essentials.py:593-618` 只查 be1/le1, 另 6 片外翻缘无判据 |
| slide_box | e_db1, e_db3 | 4/15 | `box_essentials.py:621-643` |
| rsc_rsc | 0 | 8/12 | `rsc_family.py:227-246` 只验 z 与等高, 折翼外翻摊平仍在 z=0/H |
| rsc_hsc / rsc_lock / rsc_css | 0 | 4 / 6 / 4 | 同上 |
| 60/77 类含粘口者 | 0 | 粘口 | 判据只验落在墙平面 (`closure_variants.py:441`, `box_essentials.py:551`, `sundry_family.py:444`) |
| tray_4corner/6corner/domelid/lid_overfit, food_tray_liner | 0 | 4–6 片角片 | `on_host` 只验共面 (`tray_family.py:488`, `special_shapes.py:595`, `struct_ext.py:714`), 角片外翻不检出 |

- 恒真判据 (任何单折扰动都不变) 27/1343 条: 例 `gable_top.py:72-73` (铰链轴上的点比自己), `tray_family.py:530` 与 `struct_ext.py:515` 的 `lock.iso` (刚性边长), `struct_ext.py:378` 的 `hole.plane_y0` (根面板), `gable_variants.py:152` 的 `gfin.cover_depth_ok` (自身长度比自己参数).
- 直接后果 (快照实测): `rsc_rsc flap_ratio = 0.1 / 0.3 / 0.95 / 1.0` 全部 GREEN (底/顶不闭合); rsc_rsc 8 片折翼同时外翻 180°、rsc_hsc 4 片底翼外翻、gable_top 的粘口 + 双鳍 + 后底板同时外翻、prism_n4_open 与 tuck_top_box 的粘口外翻, QA 全部 GREEN (闭合残差 ≤ 3.4e-14).
修法: batch 每类跑通用扰动探针并计入 GREEN 条件; closure 补"折翼远缘 y 落位 + 指向盒内"与"粘口/角片与宿主板重叠面积"判据; 删除恒真项.

### P1-5 封闭性 (水密) 无判据, 默认参数即漏

26 方向射线奇偶探针 (共面叠层按一次穿越计) 的结果:

| 类 | 实测 | 代码位置 | 判断 |
|---|---|---|---|
| food_wrap_pocket | −z 方向 100% 透视, 无任何底板 | `food_packs.py:556-570` (只有 wF/gL/wB/gR/glue/t2) | 卷饼纸袋无底, P1 |
| food_noodle_pail | −z 100% 透视无底; 顶部小八边开口 1931 mm² 只盖 965.7 mm² (50%) | `food_packs.py:354-368` | 外卖粉盒无底, P1 |
| pillow_box | 两端各 514.5 mm² 开口 (端面 17%) | `odd_family.py:425-446` (端片只有 H×D/2 矩形, 鼓弧段无端板) | P2 |
| food_clamshell_burger | 两端各 1337.6 mm² 开口 (端面 32%) | `food_packs.py:163-186` | P2 |
| tray_domelid | 两端各 2268.4 mm² 开口 (端面 41%) | `struct_ext.py:642-694` | P2 |
| envelope_wedge | 前面 2 个孔共 3369.3 mm² (15.6%) | `odd_family.py:583-600` | P2 |
| clv_hinged_flap | 盖抬升 hs=8 后两侧各 8×60 mm² 开口 | `closure_variants.py:217-232` (活页条只有后缘一条) | P2 |
| tube_cap_end | 端盖只盖 4021.9 / 8043.8 mm² (50%) | `struct_ext.py:545-549` | 备注已自认 |

对照: rsc_rsc/css/lock, tuck_top_box, clv_glue_seal/tuck_insert, tray_lid_overfit, display_counter, aseptic_brick 等探针为 0.
修法: closure 增加水密判据 (按闭合体逐面求"轮廓 − 被面板覆盖面积", 或直接用射线奇偶); 上述类补底板/端板.

### P1-6 G06 穿插门实际只测 50.5% 的面板对 (e 项)

- 全园 17836 个面板对中: 共折线跳过 1597, `allowed_overlap` 跳过 4617, `roles 均为 flap` 一刀切跳过 2626 (`qa/pipeline.py:172-173`), 真正送入 `_intersect3d` 的只有 9000 对 (50.5%). envelope_square、envelope_wedge 为 0%, cup_sleeve 9.5%, tray_domelid 31.9%, prism_dust_n4 34.6%.
- `allowed_overlap` 按类累计 15546 条 (家族并集对每类重复计入), 其中 13960 条 (89.8%) 在该类自身折叠态里没有真实重叠 (空放行). 原因是家族并集写法: `odd_family.py:796`, `sundry_family.py:814`, `fan_net_ext.py:542`, `special_shapes.py:518`, `struct_ext.py:887`.
- `_intersect3d` 法线取首三角 (`qa/pipeline.py:283`), 目前靠各模板"首三元组非共线"的约定维持有效 (实测 100 类面板首三角均非退化), 是隐性耦合而非现行缺陷.
- 送到检测里的 9000 对, 用稳健探针未发现任何 G06 能报的真穿越; 而真实存在的两处穿越 (P1-2) 恰好检不出.
修法: 去掉 flap-flap 一刀切, 改为按平面分组后显式声明层叠对; `allowed_overlap` 改按类返回; 法线用 SVD; 增加边-三角形穿越检测.

## 4. P2

### P2-1 板厚是死参数, 瓦楞约束缺失 (f 项)
- `board_t` 在全部 100 类的几何里未被使用, 只出现在 DEFAULTS / PARAM_ORDER / validate (grep 全仓 parametric/tde/blender/scripts 仅此). `docs/tde-spec.md:50` 却写明"纸板厚度属结构真值: 改厚度必须重算折叠补偿/面板偏移/折痕位置, 否则 IR 标签错".
- 自称瓦楞的 `rsc_family.py:1` 默认 `board_t=0.45` mm (`:24-25`), 单瓦楞实为 3–7 mm.
- 无楞向/纹向参数 (DESIGN.md §6 把"纹理方向"列为 P1 待办); 无开槽宽度 (折翼在转角处零间隙相接, `rsc_family.py:100-104`); 压线为零宽线.
- `DESIGN.md:53` 称 edges 支持 CUT/PERFORATION, 但 `schemas/geometry-ir.schema.json:220-221` 的 `kind` 是常量 `FOLD`, `:246-250` 的 `mt_va` 只有 MOUNTAIN/VALLEY/SCORE, 模板中 SCORE 零使用. 撕拉线、拉链、透气孔、锁扣开缝都无法表达 (clv_glue_seal 的撕拉手、clv_tuck_insert 的插槽分别被建成折翼和顶缘缺口).
修法: IR 增加板厚/楞向与 CUT/PERFORATION 边类型, 粘口、折翼间隙、插槽按板厚派生.

### P2-2 插舌与锁扣零间隙, 卡扣不成立 (a 项)
- `rsc_family.py:66-67`, `:108-120`: 插舌宽 sl = 插槽宽 sl, 舌长 tw = 槽深 tw, 无板厚余量, 舌尖无倒角.
- `closure_variants.py:142`: 插舌宽 = slot_w.
- `closure_variants.py:181-215` (clv_snap_lock): 柄宽 = 喉宽, 卡点宽 = 口宽; 卡点 (pk_w=36) 比喉部 (slot_w=20) 宽 16 mm, 无法穿过喉部落到墙内侧, 只能停在口腔里, 不构成锁扣.
修法: 槽宽 = 舌宽 + k·board_t, 插舌加倒角; snap_lock 改为"卡点穿过喉部后落座"的几何并按板厚校核.

### P2-3 RSC 折翼无间隙、无收角, 粘口偏窄
`rsc_family.py:98-120`: 折翼是满宽矩形并在转角点相接 (FEFCO 0201 常规为翼间隙 ≥ 板厚, 内翼不到中线并收角); `glue_w=12` mm, 瓦楞箱搭接缝常规 ≥ 25 mm [INFERENCE].
修法: 折翼按 board_t 留间隙与收角, 粘口按料种给默认区间.

### P2-4 两件式以折线相连 (d 项)
`box_essentials.py:266-267` (two_piece), `:363-364` (slide_box), `food_packs.py:663-665` (food_sushi_tray): 两件之间用 web 条, 两侧都是折线而非切断/压孔线, 导出刀模不分离; food_sushi_tray 的"透明盖"与纸托同板连体 [INFERENCE: 材质不同无法同版].
修法: web 两侧改为可分离边类型 (依赖 P2-1 的边类型扩展).

### P2-5 折线 MOUNTAIN/VALLEY 相对图面不一致 (d 项)
标签语义统一为"从盒内看" (墙-墙 = VALLEY, 内折翼 = MOUNTAIN), 但各模板网面朝向相反: 76 类 (rsc/box_essentials/closure_variants/prism/tube 等) 的 VALLEY 折线子面板落在 net-up 的反面 (图面朝外), 14 类 (gable 全家与星形托盘) 落在 net-up 同面 (图面朝内). 同一种蓝/绿折线层, 在这两组里对读图者表示相反的折向 [INFERENCE: 按制版"印刷面朝上"惯例].
修法: 统一根框架使 net-up = 印刷面, 并加 `meta` 字段声明观察面.

### P2-6 窗框共面"零转折"被导出成折线 (d 项)
`box_essentials.py:217-222`, `struct_ext.py:105-120` (`_frame_parts`), `special_shapes.py:315-340`: 前墙被拆成 4 条, 条间用 MOUNTAIN 折线相连 (tdir 零转), SVG/PDF 因此在窗框内角画出 3 条折线; 实际应是同一面板, 只有窗口四周是 CUT. 影响 window_box, prism_tuck_window, gable_window_front, mailer_diecut.
修法: 窗框合并为单一带孔面板 (多边形带内环), 或给边增加"同面拼接"类型且不进折线层.

### P2-7 validate 边界与 closure 不自洽 (b 项)
默认参数全部合法, 但边界有以下缺口 (括号内为实测 QA 结果):
- `closure_variants.py:340-386`, `box_essentials.py:429` 起: 不验 W/D/H > 0 (`clv_tuck_insert W=-50` → ERROR 而非 validate 报错); 不验 `ins` (`ins=60` → 插舌宽 −10, GREEN); 不验 `clear` (`two_piece clear=0` 与 `clear=50` 均 GREEN).
- `gable_top.py:32-38`, `gable_variants.py:103`, `brick_family.py:687`, `generic_prism.py:38`, `prism_dust.py:64`: 不验 glue_w < 最短墙 (`gable_top glue_w=60 > D=45` → GREEN; `prism_n4_open glue_w=200` → GREEN); 也不验 fin_gap < 2·Ef (`gable_top fin_gap=40` → lean 被钳到 90°, 靠 G06 才拦住).
- `rsc_family.py:51-53` 允许 flap_ratio ∈ (0,1], closure 却默认 0.5 (见 P1-4).
- `sundry_family.py` 允许 flap_d ≤ S/2, 取 50 时信封前面出现 2 个孔, 仍 GREEN.
- 反向不一致 (validate 放行, QA 拒): `dust_r < 0.5` → G04 FAIL (dispenser_top/handle_box/hanger_box/tuck_top_box/window_box); prism_dust 的 `tuck_depth` 与 `side` 耦合, 改 `side` 必 G04 FAIL (`prism_dust.py:27-29`, `:75-78`); tube 三类 closure 把"粘口宽 = 墙宽"写死, `glue_w < side` 即 G04 FAIL.
修法: 各模块 validate 补齐正尺寸与相对约束; 可派生量 (tuck_depth、粘口宽) 改为按公式派生而不是自由参数.

### P2-8 星形托盘角缝无连接 (a 项)
以下类的墙与墙只在竖棱上相遇, 没有角片或粘口: display_counter (`sundry_family.py:484-491`), divided_tray_3comp, egg_tray_2x4, food_clamshell_burger (`food_packs.py:168-173`), food_bento_lid_box (`:490-506`), tray_wedge (4 角只粘 1 角, `tray_family.py:166-190`), food_fries_sleeve (`food_packs.py:440-461`).
另: pyramid_frustum 8 类没有任何粘口或搭接缝 (`odd_family.py:167`, `fan_net_ext.py:171` 的 features 为空), 侧缝只是棱对棱.
修法: 参照 tray_4corner (`tray_family.py:137-159`) 补角片或声明胶带/粘合.

### P2-9 mailer 插舌反贴自身盖板
`odd_family.py:538` (mailer_bookwrap), `special_shapes.py:315` (mailer_diecut), `struct_ext.py` 的 mailer_rigid_pad: 插舌 180° 折回右盖内面 (closure 判据 `odd_family.py:569` 即写此位), 左盖自由棱无任何连接, 封口不成立.
修法: 插舌改折入两盖之间并与左盖锁扣/粘合, 或缩短盖深使两盖对合.

### P2-10 六角盘角片高出盘沿
`tray_family.py:143-148` (tray_6corner), `food_packs.py:772-777` (food_tray_liner): 角片是 60° 平行四边形条, 折合后远缘比盘沿高出 glue_w·cos30° (实测 10.39 mm / 6.93 mm), 目的是规避 BLEED 圆角.
修法: 角片改为不超墙高的三角形/梯形, BLEED 的圆角问题在导出侧解决.

### P2-11 n ≥ 5 棱柱底/盖是矩形条叠层, "tuck" 无插舌
`generic_prism.py:78-90`, `prism_dust.py:130-137`: 折入片是宽 side、深 apothem 的矩形, n=4 时恰好 2 层, n=6 时 1/2/3 层各 1/3, n=12 时中心达 6 层 (实测 6 层占 7.3%); closure 只验远缘中点过轴 (`generic_prism.py:188-197`), 重叠全靠 flap-flap 豁免放行. `prism_n*_tuck` 9 类没有任何插舌, 名不副实.
修法: 改为斜接的三角形/梯形折入片; tuck 类补插舌或改名.

## 5. P3 / 清理项

- P3-1 `gable_variants.py:156-160`: `return res` 之后还有 5 行不可达代码 (flapL/flapR 的 far.x0 判据实际不存在).
- P3-2 `generic_prism.py:36`、`prism_dust.py:53` 的 `_APOTHEM_TOL` 未使用; `probe()` 6 处定义零调用 (见 P1-4).
- P3-3 相邻折翼的共点边各画一次, 且外轮廓与面板边重复, CUT 段成对重叠 (如 rsc_family 每个转角 2 条); 不影响切割, 但 PDF 流长翻倍.
- P3-4 防尘翼是 0.5·W × D 的矩形且前缘齐平前墙 (`box_essentials.py:126-134`), 插舌没有可进入的间隙 [INFERENCE: 应内缩 ≥ 板厚并收角].
- P3-5 clamp_shell 的"互扣"是两片共面重叠的唇 (`sundry_family.py:621-622`), 没有锁止几何; hanger_box/handle_box 的挂孔是顶缘缺口而非封闭孔.
- P3-6 [INFERENCE] aseptic_brick/brick_250ml 的顶底是向两侧错开的剪切式屋顶 (`brick_family.py:125-180`), 与无菌砖平封横缝的形态不同; hexagonal_flip 无底而名为"盒".

## 6. 六个审查点对照

| 审查点 | 结论 | 对应发现 |
|---|---|---|
| (a) 插舌/防尘翼/粘口/锁扣比例 | 插舌深度 10–12 mm 合理; 间隙与收角缺失, 锁扣不成立, 多处角缝无连接 | P2-2, P2-3, P2-8, P3-4 |
| (b) 默认值与 validate 边界 | 默认值全部合法; 边界有缺口, 与 QA 双向不一致 | P2-7 |
| (c) closure 恒真 | batch 无负探针; 145/1597 折线翻折不检出; 27/1343 判据恒真 | P1-1, P1-4 |
| (d) 面板数与边语义 | CUT 层切穿结构; 无 CUT/PERFORATION 类型; 假折线; 折向标注不一致 | P0-1, P2-1, P2-4, P2-5, P2-6 |
| (e) allowed_overlap 掩盖重叠 | 是: 89.8% 空放行, 加 flap-flap 豁免后 G06 只测 50.5% | P1-2, P1-6, P2-11 |
| (f) 瓦楞约束 | 楞向、开槽、压线宽均无; 板厚未用 | P2-1, P2-3 |

## 7. 附: 核心侧交叉核对线索 (非本审计范围, 供核心审计)

- `folding/engine.py:95-104`: 无 `target_dir_3d` 时的角度回退无法区分 VALLEY/MOUNTAIN (实测两种标签折出同一结果, 候选按 `d·pc` 排序恒并列).
- `core/ir.py:68`: `folds_from` 访问不存在的 `e.fold`, 一调用即 AttributeError; 当前无调用方.
- `cli.py:66-96`: `_layer_geo` 不产出 GLUE 与 REGISTRATION 图层内容 (SVG 有), 而 G08 (`qa/pipeline.py:205-234`) 只数 OCG 字典 ≥ 7, 因此通过.
- `render/twin.py:16-17`: 三角扇不处理共线/凹多边形顶点, 18 类出现零面积三角.

## 8. 证据文件 (全部钉定 HEAD 54b81ca)

- 快照: `git archive 54b81ca src/photo_dieline schemas | tar -x -C /tmp/pd_recheck/head_54b81ca`; 探针以 `PYTHONPATH=/tmp/pd_recheck/head_54b81ca/src` 运行, 运行时已核对 `photo_dieline.__file__` 指向快照.
- batch 产物: `/tmp/pd_recheck/zoo100/` (07:48, 当时工作区 = HEAD) 与 `/tmp/pd_recheck/zoo100_head/` (快照复跑), 均含 `batch_report.json`, `contact_sheet.png`, `thumbs/*.png`.
- 探针目录 `/tmp/pd_recheck/probe_head/` (首轮结果在 `/tmp/pd_recheck/probe/`, 08:18–08:32 生成, 早于工作区改动):
  - `common.py`: 折叠加载、共面/穿越/共线判定、26 方向水密探针.
  - `a1_structure.py` → `a1.json`: 粘口宿主、净图重叠、共面重叠、穿越.
  - `a2_cuts.py` → `a2.json`: CUT 落入他板内部、CUT 压折线、折线支撑率、并集孔.
  - `a3b_leak.py` → `a3b.json`: 水密探针; `a4_cover.py`: 端面/顶面覆盖率与叠层.
  - `a5_closure.py` → `a5.json`: 通用负探针 (1597 条折线) 与恒真判据.
  - `a6_validate.py` → `a6.json`: 参数 ×{0.25, 0.5, 2, 4} 扫描 (100 类, 2340 次试算).
  - `a7_misc.py` → `a7.json`: G06 覆盖率、allowed_overlap 空放行、折线标注朝向、SVG 铰链切断、底板合法性、validate 边界用例、模块 probe、核心交叉核对.
