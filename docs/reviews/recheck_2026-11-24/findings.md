# findings — 从头复查证据账 (2026-11-24)

规则: 每条带来源 (file:line / 命令输出 / URL)。未亲眼核实的标 [INFERENCE]。

## 1. 现状盘点 (HEAD 54b81ca)
- 143 提交 (立项 2026-11-18 → V60 2026-11-23); 316 tracked 文件; 本地 pack 720MiB, GitHub 240MB; 最大 tracked = assets/hdri/studio_small_09_2k.hdr 6.0MB
- pytest tests/ = 26 passed; CI (ci.yml + pd_guard.yml) 最近两次 push 均 success
- 密钥扫描 (sk-/Token/api key/Bearer) 0 命中
- README 北极星 = 照片→1:1 刀版; M1 VALIDATED / M2 设计冻结 / M3 规划
- 实际进度 (按提交史): M1 ✓ → 100 类动物园 ✓ → TDE v0.5-0.8 ✓ → T1 (合成 top1 71.1%) ✓ → E0/E1/E3 ✓ → PD-Guardrails ✓ → ABO/OID 数据 ✓ → frozen10-web ✓ → **2026-11-21 起 ~100 提交转入货架孪生渲染 + ESR/SimReady 对标**, 学习线 (T2/E2b/M3) 停在 11-21
- README 完全未提货架孪生线 / ESR / SimReady 对标 / T1 结果 / frozen10 结论

## 2. 学习线数字 (文档自述 → 复算)
复算脚本: /tmp/pd_recheck/{rel_baseline,err_vs_size,train_fit,scaling,t1_baselines}.py (只读, 不改仓)。口径: 变体级留出 (val 变体 16/18/23/25/28/29, n=1002; 训练 24 变体 n=4008), raw 比例单位。

### 2.1 gable 比例回归 (文档 "1.66%±0.06pp")
| 项 | raw MAE | 说明 |
|---|---|---|
| 常数基线 = 训练中位数 | 0.0495 | 相对误差(÷val均值) 14.8% |
| 模型 e0rel / e1_seed7 / 42 / 123 | 0.0167 / 0.0171 / 0.0157 / 0.0169 | **相对误差 5.7 / 5.8 / 5.4 / 5.8%** |
- F2-01 **单位口径**: 文档 "1.66%" 是比例值×100, 不是相对误差; 按真值量级折算为 **5.4–5.8%** (E0rel 文档对旧模型给过 4.1–6.7% 两列, E3 文档只留了 0.0166 的写法)。
- F2-02 **超中位数基线成立**: 0.0495→0.0157, 约 3.2× (≥20% 的 MVE 门槛通过)。但冻结规范的另一条 "合成验证 MAE ≤0.5mm" **不成立**: 派生绝对误差 W≈2.1mm, D≈3.1mm (Hb≈105mm), Hr≈0.87mm, Ef≈1.0mm — MVE 判定表从未按冻结判据逐条出具。
- F2-03 **几何留出存在泛化缺口 (REPRODUCED); "误差主因 = 几何覆盖稀疏"未获确认** (train_fit.py / scaling.py / knn_lookup.py): 训练集 (见过的 24 个几何) raw MAE 0.0032, 留出几何 0.0157 (4.9×); 留出误差随"到最近训练几何的归一化距离"上升。学习曲线 (双种子) 见 §2.5。**按 GPT 第 1 轮裁决降级**: 曲线同时改变"几何数"与"训练图像总数"两个变量, 且未排除变体记忆 / 渲染捷径 / 分辨率瓶颈 / 划分混杂 — 只能登记为"几何数量与留出误差存在初步关联", 不得写成已确认主因。(E3 原文标 UNKNOWN 过头; 本复查初稿写成主因也过头。)
- F2-04 **学习曲线** (scaling.py, 同配方 ResNet18/32ep): 训练几何 6 → 留出 raw MAE **0.0334**; 24 → 0.0157 (seed 11/23 全表见 §2.5)。
- F2-05 **取景两头条坏** (err_vs_size.py): 盒高在 384px 画面里 p5/50/95 = 27/48/165px; 误差 U 形 — 最小档 6.7%, 中段 4.3–4.5%, 最大档(近距广角/裁切) 6.0%。

### 2.2 TDE 数据与冻结规范的差距 (源码: blender/tde_driver.py, src/photo_dieline/tde/{engine,sampler}.py)
| 规范条目 | 实现 | 证据 |
|---|---|---|
| 1.4 印刷随机化 | **未实现**: 固定角色色 (蓝身/橙顶/灰鳍), 采样色相被丢弃 | driver `build_material`: `base = ROLE_PRINT.get(role)`; base_color 只取 `lum = sum(base_color)/3` |
| 1.6 ISP 退化链 | **未实现**: jpeg_q/gauss/motion_blur/wb_shift/distortion 只进标签 | driver 无任何后处理; sampler `material_env_iq` 仅返回数值 |
| 1.5 七类环境 | 纯色地面 + 纯色世界光, 无遮挡物 | driver `ground_col` 字典; occlusion_hint 未使用 |
| 1.1 主体占比 45–85% | **被钳位破坏**: 按占比算出的距离被钳回 [dist, 1.6×dist], 驱动再 ×1.35 | sampler `np.clip(d_mm, dist_cm*10, dist_cm*10*1.6)`; driver `eye = ctr + fwd*d*1.35` |
| 分辨率 720–4032px | 384px | `run_tde(res=384)`, 标签 `"res": 384` |
| 采样 40%分层+40%LHS+20%主动 | 全独立均匀采样 | `lhs_samples` 无调用 |
- F2-06 **可学性门失效**: `subject_area_frac` = 与四角均色的色距>60 的像素占比 → 中位数 0.833 (盒子实际只占画面 5–15%); 标着 area≥0.5 的样本里盒子只有几个像素 (贴板 /tmp/pd_recheck/tde_samples.png)。门实际只在测画面纹理量: 锐度门通过率 9.2%。
- F2-07 **拓扑门相机模型与驱动不一致**: 门用 `d*1.15` 且无 FOV 保底, 驱动用 `d*1.35` + `d_fit`; 像素映射 `px = 160 + x*160` (中心 160/半幅 160, 应为 192/192)。通过率 37.5% 不可信。
- F2-08 门禁 FAIL 样本未过滤即入训练/验证: G0(双门) 仅 391/5010 = 7.8% (dataset_report.json)。

### 2.3 盒型 (RSC) 比例回归
- raw val MAE 0.69 vs 常数基线 1.26 (仅好 45%), 比例跨度 16× 仅 24 训练几何 — 与 F2-03 同源 (frozen10 sim2real_report.json `box_ratio_model_v3`)。

### 2.4 T1 分类在真实照片上 (t1_baselines.py)
- 同一合成验证集 (留出变体 4, n=588): ResNet18 top1 **71.1%** / top5 96.1% / 家族级 93.5% (复现文档数字); DINOv2 ViT-S/14 零训练 kNN (训练变体 0–3 作图库, 336², CLS 余弦) top1 **54.8%** / top5 82.7% / 家族级 83.5% → 域内训练模型胜 16pp。
- ABO 37 张真实棚拍 (粗类: 瓦楞箱/折叠盒/瓶罐/屋顶包/其他; 真值=文件名关键词, 有噪声, 只看量级): ResNet18 粗类 top1 **21.6%** / top5 40.5% / 宽口径(纸容器|瓶|其他) 45.9%; DINOv2 零训练 **35.1%** / 51.4% / 64.9%。瓦楞箱 8 张两种方法 top5 都是 0/8。
- F2-10 **合成→真实落差**: 分类 71.1%(合成) → 21.6%(真实粗类; 5 类随机水平 20%); 回归在真实件上不可测 (frozen10: gable 模型套瓦楞箱 = 域错配)。仓内没有任何学习组件在真实照片上被证明可用。
- F2-09 **拒识机制不保护**: frozen10 报告 "T1 对域外真实照片 0 假阳性" 只在那 10 张成立。ABO 37 张实拍: 12 张被判 KNOWN_TYPE, 其中多张为高置信错判 (瓦楞纸箱→food 族 conf 0.80, 瓶→brick 族 conf 0.91)。阈值 (margin 1.0 logit / top5 质量 0.30) 是手拍的, 未经 OOD 校准。

### 2.5 学习曲线全表
| 训练几何数 k | seed 11 | seed 23 | 训练张数 |
|---|---|---|---|
| 6 | 0.0334 | 0.0333 | 1002 |
| 12 | 0.0240 | 0.0238 | 2004 |
| 24 | 0.0162 | 0.0168 | 4008 |

读法: 几何数翻倍, 留出误差降 28–31%; 端点幂指数 ≈ 0.51 (6→12 局部 0.48, 12→24 局部 0.61)。只能作粗略描述, 不能外推成"×10 几何即达毫米级"。种子间差 ≤ 0.0006 (关联可复现, 因果未立)。

**查表基线** (GPT 第 1 轮 §2.4 点名遗漏; `knn_lookup.py`, 留出集同上):

| 方法 | 留出 raw MAE |
|---|---|
| 猜训练集中位数 | 0.0495 |
| DINOv2 图像检索 → 取最近训练图的标签 | 0.0564 (劣于猜中位数) |
| 参数空间 oracle 查表 (取真值比例最近的训练变体 = 任何查表法的下界) | 0.0228 |
| CNN 回归 (3 种子) | **0.0166** |

- CNN 比最优查表还好 27% → 在合成域内它不是单纯"认变体", 有一定的连续映射能力 (对"变体记忆"假说的反证)。
- DINOv2 检索几乎与几何无关: 只有 5.9% 的留出图检索到"比例最近"的训练变体, 命中直方图在 24 个变体上近乎均匀 (29–63)。通用外观特征对这些图不敏感于几何 — 与"外观捷径"假说相容, 也解释了 T1 用 DINOv2 在真实集上的结果为何只能看量级。
- 仍未做 (GPT E4-A/B/C/D): 同几何异外观 / 同外观异几何 / 插值与外推 / 信息通道消融; 固定总图像数 vs 固定每几何图像数两种预算口径; ≥3 种子。

## 3. 文献对照
### 3.1 仓内已引论文核验 (TDE 规范 §6, GPT 深度研究产出)
| 引用 | 核验 | 来源 |
|---|---|---|
| Tobin 2017 DR; Borrego 2018; BlenderProc 2020; Hypersim 2021; Task2Sim CVPR 2022 | 存在 | 通识, 未逐一回查 |
| Geng et al. 2025 One View Many Worlds | 存在, CoRL 2025 | arxiv.org/abs/2509.07978 |
| Zhu et al. 2025 工业 DR 综合研究 | 存在 | arxiv.org/abs/2506.07539 |
| Abdul Hay et al. 事件相机 6D | 存在, IEEE RA-L 11(2) 2026 | ieeexplore 11299552 |
| Kamo & Ishizaka 2023 | 存在, JSAI2023 (富士胶片) | jstage JSAI2023_4T2GS1005 |
结论: 9 篇全部真实。但它们支撑的是"检测/位姿"任务的域随机化, 无一篇支撑"包装几何参数回归"; Print/ISP/环境三维度的数值本就是工程先验 (规范自己承认), 而实现连工程先验都没落地 (§2.2)。

### 3.2 各组件对照 (项目现状 → 文献/标准坐标 → 差距)
| 组件 | 项目现状 | 文献/标准坐标 | 差距 (可优化点编号) |
|---|---|---|---|
| 尺寸恢复 (T2) | ResNet18 直接回归比例; 合成域 5.4–5.8% 相对; 真实不可测 | **单视图度量学**: Criminisi/Reid/Zisserman Single View Metrology (IJCV 2000); Pears/Wright/Bailey Practical Single View Metrology for Cuboids (VISAPP 2007) — 长方体三消点即可解出相机焦距与三边比例, 闭式、无需训练 | O-01: 未做"关键点+消点闭式解"基线; 现路线用 CNN 去学一个有解析解的几何问题 |
| 多视角高精度模式 | 规范写"后续"; 仓内只有 E3 跨视角平均 (≈2.5%) | **前馈几何基础模型**: VGGT (CVPR 2025 best paper) → π³ (ICLR 2026) → MapAnything (Meta, arXiv 2509.13414: 1..N 张图+可选内参直接出度量三维) → VGGT-Ω / D4RT (CVPR 2026) | O-02: 2–3 张手机照+一条实测边即可走零训练路线, 仓内零实验 (PoC 见 §3.3) |
| 单图绝对尺度 | 判定"不可观测", 交给用户量尺 | UniDepthV2 (TPAMI), Depth Pro (ICLR 2025, 零样本度量深度); GeoCalib (ECCV 2024, 单图标定) | O-03: 可作"量尺合理性校验/先验", 不足以替代实测 (对 0.5mm 无望), 优先级低 |
| 箱型识别 (T1) | ResNet18 合成训练; 真实粗类 21.6% | LVLM 零样本细粒度分类 (EMNLP 2025 Findings, arXiv 2510.03903: 化为 VQA 框架); DINOv2 检索 | O-04: 真实照片上零训练 DINOv2 (35.1%) 已胜现役; VLM/VQA 零样本未试 |
| 模板命名与覆盖 | 自定义类名; 39/100 类是多边形边数变体; 源码 ECMA 出现 0 次 | **ECMA Code of Folding Carton Design Styles (2022): 206 个编码** (CL/FL/PL 线型, 纤维方向标注); FEFCO 瓦楞编码; 行业库按编码出参数化模板 | O-05: 动物园应对齐 ECMA/FEFCO 编码; 真实常见盒型覆盖率未度量 |
| 参数化内核 | 100 类 + 折叠 QA 十门; 零板厚 | PackBox Studio (MIT): 10 盒型, 同样零板厚, 有 artwork/DXF/拼版 PDF/GLB; Cartonist (CAD 2019) 非标纸盒自动合成; Folding Cartons (GMP 2018) 2D 版图交互折叠; Kyocera 专利 US11442430 (草图→CNN 分割折线/切线→驱动模切机) | O-06: 本仓盒型数与数值 QA 领先 PackBox; 缺 DXF、板厚补偿、版图↔照片反向分割。内外尺寸/score-to-score 定义未声明 (DielineMaker 行业指南) |
| 合成数据 (TDE) | 384px、固定角色色、无退化链、取景钳位坏 | DR 综述: The Reality Gap in Robotics (Annual Review of Control 2026, arXiv 2510.20808); Synthetic Data for Object Detection DR 综述 (ACM TOMM 2024); Task2Sim | O-07: 冻结规范六维里只落地了相机+光照+粗糙度; 见 §2.2 |
| 货架孪生 | 单张参照照 + GPT 盲评排序; 60+ 轮调参 | ShelfChange3D (arXiv 2610.01283, 145K 合成 RGB-D 货架对); Sari Sandbox (arXiv 2508.00400); TwinStore (arXiv 2610.30909); planogram 扩散合成 (arXiv 2601.00527) | O-08: 同行都以"下游任务/数据集"交付, 本线以单图盲评分为交付物; 没有可被第三方复用的数据或任务 |
| ESR / SimReady | 自建 10 项检查, 140/140 | **SimReady Foundation** (github.com/nvidia/simready-foundation): capabilities→features→profiles (Robotics-Prop 等), 机器可查 rules, feature adapters 跨 PhysX/Newton/MuJoCo; 官方校验器可直接跑 | O-09: 应直接跑官方校验器而不是自建子集; "140/140" 现已不成立 (§4) |
| 评审方法学 | GPT 判别+排序 | 仓内 eval_frameworks_survey 已覆盖 (A-Bench LMM 感知有偏等) | 一致; 但 GPT 盲评原始记录只有 4 份入库, 其余不可复核 |

### 3.3 多视角前馈几何 PoC (VGGT-1B × ABO 多视角)
- 协议: ABO bench30 中 ≥2 视角且带列表尺寸的 29 件 (主图 + ≤2 张目录附图, 均 256px); VGGT-1B (本机缓存权重, MPS fp32) 前馈出世界点; 白底阈值分割物体; PCA 主轴 1.5–98.5 分位取三边; 排序后与列表尺寸排序比。脚本 /tmp/pd_recheck/vggt_abo.py。
- 结果: 26 件跑通 (3 件形状不齐报错); **白底可分割的只有 5 件**, 边比平均绝对相对误差 **0.124** (中位 0.133), **劣于常数基线 0.064** (猜官方比例中位数)。
- 判读: **负结果, 且基准不可用** — 列表尺寸多为占位值 (多件 1×1×1 英寸)、图像 256px、目录附图常是不同场景/不同状态。不能据此否定"多视角前馈几何"路线, 也不能支持。要回答 O-02 必须先有带卡尺真值 + ≥5 张重叠视角的实物集 (即 2026-11-20 GPT 判决的 P0 "10 件实物冻结采集", 至今未做), 并把"分位包围盒"换成"模板拟合"。
- 受控补充 (vggt_syn.py): 用仓内 TDE 驱动对 3 个留出几何各渲 3 视角 (50mm 等效, 俯角 12–18°, 偏航 −45/5/65, 518px, 真值精确), VGGT 前馈 + 色度分割 + 分位包围盒: 边比误差 v16 = 6.2/6.5/14.9%, v23 = 15.7/10.4/10.2%, v25 = 11.7/10.3% (1/2/3 视角) — **不随视角数下降, 不优于 CNN 回归的 5.4–5.8%**。无纹理平涂面是前馈几何的已知弱项, 结论仍为"未证实"; O-02 降级为"真实带纹理数据到位后再测"。


## 4. 代码审计发现
三路只读审计 (reviewer 子代理): 核心管线 / 模板动物园 / 货架孪生+ESR。报告原文 /tmp/pd_recheck/{core,zoo,twin}_audit.md。

### 4.1 本人亲验 (金标样品实跑)
- F4-01 **P0 导出件被平移出画布, 95/100 类受影响**: `export/svg.py` 的 `T(x,y) → (x+MARGIN, y+MARGIN)` 与 `export/pdf.py` 的 `shift=12` 都只加边距、不减展开图包围盒原点; 模板的 `polygon_2d` 多数不以 (0,0) 为原点 (gable_top y0=−45, rsc 族 y0=−80, clv 族 y0=−55, 棱台/锥管族 y0≈−202)。金标样品实跑: 全部几何 y∈[−36.0, 208.5], 画布高 208.5 → 屋顶坡面+立鳍整段落在页外 (/tmp/pd_recheck/golden/dieline_render.jpg); 已入库的 `examples/gable_top/artifacts/dieline.svg` 同样越界 (元素 y∈[−45.1, 203.2])。PDF 同理 (MediaBox 216×208.5mm)。
- F4-02 **门与测试都没拦住**: G07/G08 只量画布尺寸与 50mm 校验条; `tests/test_m1.py::test_svg_physical_layers` 只断言 `width="..mm"` 与图层 id, `test_pdf_mediabox_and_bar` 只看 MediaBox。README 的 "M1 VALIDATED、十门全绿" 对导出件不成立。
- F4-03 **"100 类"的构成**: 39 类是同一家族按多边形边数刷出的变体 (棱柱开盖/插盖 n4–n12 共 18, 防尘翼棱柱 n4–n12 共 9, 棱台 n4–n10/n12 共 9, 锥管 n12/n20, 管 n8/n24); 源码 ECMA 出现 0 次。真实不同结构 ≤ 61 类。

### 4.2 货架孪生 / ESR 线 (twin_audit: P0×1 / P1×10 / P2×12 / P3×5)
- F4-04 **P0 ESR 资产层在 HEAD 失效** [本人复核]: 提交 0a03d31 重导出后, 18 个 `assets/sku_usd/*.usda` 全部丢失 `phys:dimensionsMM`/`wikidata_class`/材质标签/`kind`, `box_tp_00` 实为 1m 立方 (extent ±0.5, 声明 120×45×190mm; 根因 `export_sku_usd.py:95-101` 缩放/位置设在随后被 unlink 的临时对象上)。入库的 `esr_acceptance.json`(COMPLIANT) 与 `conformance_score.json`(140/140) 落盘于 11-21 11:00, 早于重导出 (11-22 00:35); 审计只读复跑一致性检查 = 126/180。
- F4-05 **三门无否决能力**: 语义门接受任意 `semantics:labels:*` (现盘只剩 qcode 仍 18/18 PASS); 物理门不读 USD、用 manifest 数字现搭 MJCF, 质量 1µg–10t × 摩擦 0–3 判决不变; 渲染门是 `render_gate.json` 里手写的 `"pass": true`, 指向 32 个版本前的 v28d; 像素门给白噪声图判 ALIGNED (0.2327 < 0.25)。
- F4-06 **资产层与场景断链**: `build_hxl_shelf.py` 不引用 sku_usd/sku_manifest; 三门验收的资产不在被渲染的场景里。
- F4-07 **合规**: `assets/food_patches/{chips_a,chips_b,chips_c,cookies}.png` 是第三方商业产品摄影 (薯片包装袋、带品牌包装的夹心饼干; 收敛日志自述来自京东在售图), 入公开仓无来源/许可记录 [本人目检确认]; HDRI (Poly Haven) 与 AI 印刷图也未入 THIRD_PARTY_NOTICES。违反 ADR-011 与仓自身"品牌素材零容忍"。
- F4-08 **证据强度**: manifest 标"实测单源"的尺寸实为占位默认参数 (12 个袋厚度全为默认 70mm); planogram 三份生成器写同一路径、互相覆盖, 已提交的 36 组无法由仓内脚本重放。
- F4-09 **工程**: 该线 0 pytest 覆盖; rule-enforcer 对 `scripts/**` 的保护由无关测试执行; `build_hxl_shelf.py` 2105 行、`main()` 1133 行 (其中 631 行是只打印不判定的探针分支); `ROOT` 硬编码绝对路径; 36 张设计图 = 12 张 AI 印刷 ×3 份字节相同副本 (38MB 冗余)。

### 4.3 核心管线 (core_audit)
core_audit: P0×2 / P1×10 / P2×15 / P3×13。对 IR 做 27 个单点破坏 (粘口折向盒外、底板未折、两鳍重合、非流形、M/V 全互换、SVG 缩半/清空、PDF 加缩放…), 12 个被拦, **15 个 (56%) 仍判 VALIDATED**。

| 编号 | 级别 | 发现 | 亲验 |
|---|---|---|---|
| F4-10 | P0 | 导出器丢弃净图原点 (同 F4-01) | ✓ 坐标解析 + 渲染目检, 95/100 类 |
| F4-11 | P0 | **手写 PDF 两处语法错误, PDF 在独立引擎下打不开/全白**: `export/pdf.py:85` `/Properties` 的键 `P{i}` 缺 `/`; `:90` `BDC` 缺 tag 操作数 (应为 `/OC /P{i} BDC`)。G08 只数前 4096 字节里的 OCG 字典个数, 从不打开文件 | ✓ poppler `pdftoppm` 报 "Dictionary key must be a name object" ×N, 渲染结果 min=max=255 |
| F4-12 | P1 | PDF 图层挂载错位 (下标用 `streams` 序号而非 `LAYERS` 序号): 出血线挂到 GLUE 层、校验条挂到 BLEED 层, REGISTRATION/INFO 空层; 全图无颜色; GLUE/REGISTRATION 无几何 | 审计静态核对, 未亲验 |
| F4-13 | P1 | 折线 MOUNTAIN/VALLEY 标注自相矛盾: 同为向盒内 90° 折, 墙\|墙标 VALLEY、墙\|底板标 MOUNTAIN; 不存在任何观察面使 12 条全部成立; 12 条全互换仍 VALIDATED | 审计探针 |
| F4-14 | P1 | G04 折叠闭合有 2 条恒真判据 (比较铰链交点, 残差恒 0), 对 4/13 面板零覆盖 (粘口没贴上/背底板没折都判过) — 与 README "恒等判据视为无效" 相反 | 审计探针 |
| F4-15 | P1 | **"实测优先" (ADR-003, 三条铁律之二) 未实现**: `core/ir.py:102-108` 只拷贝 status 字符串, `value_mm` 被丢弃 | ✓ params.W=50 + 实测 W=45 MEASURED → VALIDATED, 结果 W=50 且证据等级仍 "MEASURED" |
| F4-16 | P1 | **照片对输出零影响**: G01 照片门、G09 报告自检根本不存在, "十道门"实为 8 道; 照片只被读了尺寸 | ✓ 真实照片/纯色图/噪声图 → SVG md5 相同 (8636a8eed7), 全 VALIDATED |
| F4-17 | P1 | **CLI 只能构建 gable_top**: `cli.py:30` 硬编码 `gable_top.build_ir`, `spec.package` 被静默忽略; README 称可重建"屋顶包/瓦楞箱/纸盒", 其余 99 类只能经 batch 用默认参数跑 QA | ✓ package=不存在的类 → 仍产出 gable_top, VALIDATED |
| F4-18 | P1 | G07 (SVG) 恒真: 7 个 `<g id>` 无条件生成; SVG 缩半 (非 1:1)/清空几何/层互换/删校验条 全部 PASS; G08 不解析 CTM (加 `0.5 0 0 0.5 cm` 仍 PASS) | 审计探针 |
| F4-19 | P1 | G03 无非流形/悬空边/面积重叠检查 (三面板共边 → VALIDATED); G06 豁免面过大 (报 78 对实查 58 对), 漏检 1.15° 真穿插 | 审计探针 |
| F4-20 | P1 | 测试只有正例: 13 个用例仅 2 个负例, 没有一个"坏输入必须被某道门拒绝"的负探针 | ✓ 读 tests/test_m1.py |
| F4-21 | P2 | G05 "golden 尺寸" 是参数自洽检查 (期望值来自同一组参数的 `analytic_bbox`, 残差 3.5e-14mm), 不是独立基准; `board_t` 全仓零使用; SVG 与 PDF 关于水平轴互为镜像; CUT 层每条线画两遍 (重复切割实体); IR `features` 不驱动任何导出 (清空后输出不变); SCORE 被并入 VALLEY 层; schema `edges[].kind` 是常量 "FOLD" (与 DESIGN 的 MOUNTAIN/VALLEY/SCORE/CUT/PERFORATION 不符) | 审计探针 |
| F4-22 | P2 | release gate 的 `pd_guard_r3 dieline` 对真实输入是空检查 (spec 无 `polygons` 字段 + `--allow-missing-strip`); CI 把残缺产物当合格证据上传 | 审计读码 |

**小结**: "M1 VALIDATED、十门全绿" 这句话的三个成分都不成立 — 门是 8 道不是 10 道; 绿是因为多道门恒真或判据错位; 两个交付物 (SVG/PDF) 一个缺部件、一个打不开。

### 4.4 模板动物园 (zoo_audit)
zoo_audit: P0×1 / P1×6 / P2×11 / P3×6。全部探针在 HEAD 54b81ca 的 `git archive` 快照上重跑, 数字钉定在修复前; 模板目录至今未改。

| 编号 | 级别 | 发现 |
|---|---|---|
| F4-23 | P0 | **15 类默认参数下导出的 CUT 层切穿结构, batch 仍判 GREEN**: 14 类净图面板重叠 (egg_tray_2x4 重复面积 15680mm²、food_sushi_tray 26559mm²、pyramid_frustum_n4–n12 全部、cup_sleeve、gable_screw_cap…) + 6 类折线两缘顶点细分不一致 (rsc_handhole 顶翼与前墙的全部实际连接 130mm 被画成 CUT; egg_tray_2x4 860mm)。机制: `cut_segments` 只排除与折线端点完全相等的边; G03 只数并集环数, 不查面板重叠与 CUT 落点。 |
| F4-24 | P1 | **37 类粘口折回自身墙板, 筒体不闭合**: `tdir=(1,0,0)` 即沿首墙自身方向 (prism_n4–n12 open/tuck 18 类、prism_dust 9 类、tube_glue 3 类、hexagonal_flip、tube_double_seam、crashlock_divider、tube_cap_end、crashlock_rect/rect_tuck、lockbottom_123)。closure 只验"粘口落在 w0 平面"故恒真。同拓扑的正确写法仓内已有 (`rsc_family.py:132` 等)。 |
| F4-25 | P1 | **closure 覆盖不足且 batch 无负探针**: 通用扰动探针 (每条折线 ±35°/180° 扰动, 门限 0.2mm) — 1597 条折线中 145 条 180° 不检出、30 条 ±35° 不检出; 1343 条判据中 27 条恒真。实测: rsc_rsc 8 片折翼同时外翻、gable_top 粘口+双鳍+后底板同时外翻, QA 全 GREEN; `rsc_rsc flap_ratio=0.1` (底/顶不闭合) GREEN。模板自带的 `probe()` 只覆盖 40 类且全仓无调用方。 |
| F4-26 | P1 | 封闭性无判据: `food_wrap_pocket` (卷饼袋) 与 `food_noodle_pail` (粉盒) **没有底板**; pillow_box/clamshell/tray_domelid 端面开口 17–41%; divided_tray_3comp 底板多边形自交缺 1/3 面积; 2 类隔板十字无槽相穿且 G06 检不出垂直穿越。 |
| F4-27 | P1 | G06 实际只测 50.5% 的面板对 (flap–flap 一刀切豁免 2626 对; `allowed_overlap` 按类累计 15546 条中 89.8% 是空放行)。 |
| F4-28 | P2 | 板厚是死参数 (`board_t` 在 100 类几何中零使用), 瓦楞楞向/开槽/压线宽全无; 插舌与锁扣零间隙 (`clv_snap_lock` 卡点比喉部宽, 不构成锁扣); RSC 折翼无间隙无收角; 两件式 web 用折线相连; 折线 M/V 相对图面不一致 (76 类与 14 类网面朝向相反); 窗框共面"零转折"被导出成折线; validate 边界缺口。 |

**小结**: "100 类十门全绿" 只说明默认参数能过现有门; 至少 15 类的刀版不可切、37 类的筒体不闭合、2 类没有底。

## 5. 本轮整改

### 5.1 第一批 (GPT 评审前; 提交 0487e77 · 096c72a · c0b23de)

| 发现 | 修法 | 验证 |
|---|---|---|
| F4-10 导出越界 | 新增 `export/layout.py` 页面几何单源: 包围盒原点归一到页边距; SVG/PDF 共用同一份图层几何 | 100 类全量: SVG 几何全部在页内 (`G07.metrics.out_of_page_points=0`) |
| F4-11 PDF 语法 | `/Properties` 键补 `/`; `BDC` 补 `/OC` tag | pypdf 严格模式可解析; poppler 渲染非白像素 0 → 41070 (金标) |
| F4-12 图层错挂 | 按 `LAYERS` 下标挂载; 输出描边色; 补 GLUE/REGISTRATION | 七层全部真实挂载 (`test_pdf_opens_in_independent_parser`) |
| (P2-5) SVG/PDF 镜像 | SVG 翻 y, 两交付物同向 | 目检 compare.png |
| F4-15 实测优先 | `resolve_params`: MEASURED/VERIFIED_SOURCE 覆盖参数; `build()` 对冒充实测报错 | `test_measured_value_wins_and_faked_measurement_rejected` |
| F4-16 G01/G09 缺失 | 补 G01 照片证据门、G09 报告自检门; 照片格式白名单 | `test_qa_report_has_ten_gates` |
| F4-17 CLI 硬编码 | 按 `spec.package` 经注册表分发, 未注册类报错 | `test_build_dispatches_by_package` |
| F4-18 G07/G08 恒真 | 改为独立解析 (XML / pypdf) 后核对页尺寸、无 transform、逐层内容计数、几何在页内、外轮廓落位、校验条、图层挂载 | 负探针: 缩放/出页/删校验条/坏 PDF 四种全部被拒 |

### 5.2 第二批 (回应 GPT 第 1 轮的签署条件与修改意见; 提交 [tests 红] · 7e4aca2 · 以及其后的整改提交)

| GPT 意见 | 整改 | 验证 |
|---|---|---|
| A1–4 "暂不签署: 导出器与验证器共用坐标变换, 三者可以一致地错" | 手算金标: 页面坐标由 spec 参数独立推导 (勾股求坡面长; 粘口 + 四面墙; 底折页 + 墙 + 坡面 + 立鳍), 对 SVG 与 PDF 逐项对账 | `test_hand_computed_golden_page`: 页面 216×208.5; 竖折线 x = 24/69/114/159; 横折线 y = 57/157/182.5; 裁切极值 x = 12/204, y = 12/196.5; 校验条 (12, 200.5)→(62, 200.5) — 两个交付物全部一致 |
| A3 "新增门禁后必须用原来的破坏样本重新攻击" | 审计变异矩阵探针回放 (`audits/probes/probe5_replay_after_fix.py`) + 参数化测试 `test_golden_mutations_are_rejected` (9 种 IR 级破坏) | 修复前 12 拦 / 15 漏 → 第一批后回放仍漏 4 项 (粘口折向盒外 / 背底板未折 / 两鳍重合 / M/V 全互换) → 第二批后 9/9 被指定门拒绝 |
| B5 "顶点细分不一定是错误, 应先做共线归一" | `cut_segments` 改为 面板边 − 折线并集 (落在折线上的面板边是铰链材料, 不是裁切) | 6 类铰链被画成裁切的长度 → 0: rsc_handhole 130mm, egg_tray_2x4 860, divided_tray_3comp 440, crashlock_divider 136, gable_screw_cap 38, food_noodle_pail 18; `test_subdivided_hinge_stays_a_fold` |
| F4-14 G04 恒真判据 | 金标: 删 2 条恒真项, 补 粘口远缘落前脸 / 背底板远缘 / 双鳍顶缘距 三条 | `closure_sensitivity`: 12 条折线 ±35°/180° 扰动漏检 4 → 0; 各角度最小残差 2.5 / 8.2 / 24.8mm |
| F4-13 折线 M/V 矛盾 | 新增 `fold_semantics` (观察面约定 = 父面板 polygon_2d 逆时针法线一侧; 模板须声明 `mt_va_reference` 才有判定基准); 金标重标 5 条 (粘口 + 4 底板: MOUNTAIN → VALLEY) 并声明约定 | 金标 12/12 自洽。全园量化: **1591 条折线中 1066 条 (67%) 与约定不一致, 60 类内部两套约定混用, 仅 4 类整类自洽** |
| 4.2 "模板分级发布, 取消数量承诺" | `photo-dieline batch` 输出成熟度: L0 注册 / L1 展开几何有效 / L2 折叠有效 (L3 样件 / L4 签核须实物) | **L2 1 (gable_top) · L1 83 · L0 16**; 全园闭合灵敏度: 1591 条折线漏检 141 条 (9%) |
| 0.4 第三方素材 "提升为最先执行" | 4 张裁片自 HEAD 出库; 回退改仓内自绘占位图; NOTICES 补 HDRI / AI 印刷 / 出库记录 | 渲染脚本无渲染校验通过 |
| 0.5 ESR "立即撤销未经现行验证的声明" | `simready_benchmark.md` 加撤回横幅; `data/shelf_twin/STATUS_REVOKED.md` | — |
| 0.6 README "先撤回过度声明" | README 改为成熟度表 + 学习线仅合成域 + 货架线标实验性 | — |
| 0.7 冻结旧证据 | 三份审计原文 + 探针入 `audits/`; 全量批量报告入 `zoo100_batch_report.json` | — |
| 0.8 禁止关键字段静默默认 | 导出入口拒绝自交/退化面板 (ARError 并列出面板 id); 未知折线语义报错; 未注册类报错; 冒充实测报错 | divided_tray_3comp 导出被拒, 且 G03 报出原因 (不允许"拒了但说不出为什么") |

### 5.3 整改后仍未闭合 (按 GPT 裁决的优先级)
1. 真实实物黄金集 (24 件 × 6 结构族, 三层真值 GT-A/B/C) — 须仓库所有者亲自采集。
2. 参数化逆向拟合基线 (B0 人工关键点 → B1 自动关键点 → B2 多视角) — **B0 完成 (见 5.4); B1 自动关键点 / B2 多视角未开始**。
3. 15 类面板重叠 / 37 类粘口方向 / 65 类闭合判据漏检 / 1066 条折线语义重标 — 模板层, 未动。
4. 货架孪生线迁出 — 须仓库所有者裁决目标仓。
5. 公开仓 git 历史中的第三方产品照 — 清除须改写历史, 须裁决。

测试: 26 → 49 passed (含 9 个参数化变异回放) → 第三批后 **70 passed** (含 10 变异回放 + 4 域边界 + 3 测量合同)。

### 5.4 第三批 (B0 参数化测量求解器 + 门禁合同补漏; 本轮)

| 项 | 内容 | 验证 |
|---|---|---|
| B0 求解器 (5.3-2 首段落地) | `src/photo_dieline/measurement/solve.py`: 单视角标注关键点 + 已知内参 + 可选实测尺寸 → 参数/相机联合拟合 (scipy 多起点; extras `measure`)。三条合同: 生成/求解双投影实现、尺度锚定与待估严格分开、可辨识性 = 参数子空间 Schur 补 (位姿 7 参数含一个冗余方向) | 双投影对账: 16 帧 × 14 点最大差 0.004px (`evidence/b0/camera_verify.json`, Blender 内 bpy world_to_camera_view vs 本模块 numpy)。实验矩阵 (120 长方体 + 120 gable × 3 尺度信息 × 6 噪声档, 8 进程): σ=0 全部精确 (远优于 0.01mm/0.001px 判据); **σ=1px + 一条实测边: 比例 MAE 0.0046 (gable) / 0.0057 (cuboid)**; 无锚点: 长方体 114/114 判不可辨识 (尺度偏差均值 29%, 重投影近完美 — 低重投影 ≠ 尺寸正确, 已如实上报); gable 靠 fin_gap=3mm 模板先验弱可辨识 (条件数 3×10⁵, σ=2px 时 W/D 误差 ±11mm → 不可信); 多解 0 / 求解失败 0 / 重投影超标 0。汇总 `evidence/b0/b0_summary.json`, 全行 `b0_rows.json.gz` |
| 同帧 CNN 对照 | e1_seed42 在同 120 帧 (全留出变体, 渲染图直出): 比例 MAE **0.0314** (`evidence/b0/cnn_rows.json`) | B0 (一条实测边, σ=1px) ≈ CNN 的 1/7, 且给出绝对 mm; CNN 优势: 不需内参/关键点标注。口径提示: B0 的噪声模型是 i.i.d. 像素高斯, 真实点选有偏且相关; 双方都在合成域 |
| 门禁合同补漏 | 修正 probe5 两处失效串 (PDF 校验条坐标写错 → PDF 篡改从未命中; flapL 方向写成正确值 → no-op) + 重压缩同步 /Length 后, 回放暴露两个真漏洞: ① 折向带铰链轴分量 VALIDATED → 新增 `qa.pipeline.hinge_orthogonality` (G04: 单位向量 ⊥ 铰链, 容差 1e-3); ② Hr=0.001 近退化 VALIDATED → 模板声明适用域 `gable_top.param_domain_violations` (G02: 正参数 / fin_gap_mm < 2·Ef / 屋脊坡角 ≥ 5°, 域外不出 VALIDATED) | 回放矩阵最终: 26 DRAFT / 3 BUILD-EXC / 1 ARError / baseline VALIDATED (`evidence/gate_v2_replay.log`, 探针固化 `audits/probes/probe12_gate_contract.py`)。回归: +1 折向变异 (G04), +4 域边界 (3 拒 + 坡角 5.5° 过拒控制); `pytest: 70 passed` |

## 6. GPT 复查评审
- 第 1 轮: 会话 `6b04e20e-6b54-83ea-9404-cce4e946424f`, 判决原文 `gpt/round1_verdict.md`。要点: 技术主干保留; 撤回 100/100 声明改分级验证; **"几何覆盖稀疏是误差主因" 不予确认** (接受现象、拒绝归因); CNN 回归暂停扩张; 解析几何升 P0 并升级为参数化逆向拟合; 多视角前馈模型降级; 真实数据集 P0; 货架线迁出。
- 第 2 轮: (见 `gpt/round2_verdict.md`)
