# PhotoDieline

**实物包装照片 → 印刷级 1:1 刀版图。** From physical packaging to manufacturing geometry.

开源工具链：输入手机照片 + 少量实测尺寸，重建折叠纸包装（屋顶包/瓦楞箱/纸盒）的参数化制造几何，输出分层 1:1 刀版 SVG/PDF（裁切/压线/粘口/出血/套准），并用纯数值折叠仿真验证回包闭合。

> 姊妹仓：[openusd-retail-twin](https://github.com/topprismdata/openusd-retail-twin)（零售商品数字孪生与视觉 AI 管线）。本仓与其完全独立。

## 架构一图

```
照片 + 实测尺寸 ─► 箱型识别 ─► 参数化模板 ─► Geometry IR ─►┬─► 1:1 分层 SVG/PDF
                (T1分类/T2回归, M2)   (唯一制造几何协议)      └─► 折叠数值验证 + QA 报告
```

三条铁律：

1. **参数化主干**：制造几何永远由模板+几何内核生成，模型只提供"类型+参数"建议（ADR-001/009）。
2. **证据分级**：实测 > 可信来源 > 约束推导 > 模型推断 > 默认值；模型值永不覆盖实测（ADR-003）。
3. **三态交付**：DRAFT → VALIDATED（数值 QA 全过）→ PRINT-READY（印厂人工签核）；系统不得自动升级（ADR-008）。

## 模板动物园（100 类注册：L2 折叠运动学有效 1 · L1 展开几何有效 83 · L0 仅已注册 16）

| 家族（29） | 类数 | 代表拓扑 |
|---|---|---|
| 棱柱系（prism/prism_dust/tube/cone/hexagonal/two/slide…） | 40 | n 棱柱开盖/插盖/防尘翼、圆管、锥管、两件套、抽屉套筒 |
| 盖型与商务盒（clv/box_essentials/tuck/window/hanger/dispenser/handle…） | 17 | 插舌入槽/T 形卡扣/活页/半盖/双层/胶封撕手/开窗框/挂舌/抽取/提手 |
| 屋顶包系（gable/brick/window_front） | 6 | 经典/无鳍胶条/开窗前墙/旋盖座/宽鳍 V 张 |
| 瓦楞与锁底（rsc/crashlock/lockbottom） | 6 | RSC/HSC/CSS/锁合/顺央底±插盖/1-2-3 |
| 托盘食品系（tray/food/egg/divided/cup/sushi…） | 17 | 四角/六角/楔形/汉堡铰链/粉盒/薯条套/便当/卷饼袋/寿司托/蛋托/三分格/杯套 |
| 异形展示（pyramid/pillow/pyramid_ext/mailer/envelope/display…） | 14 | 棱台×8/锥管×3/枕形/书封/信封×2/陈列台/扣夹盒/硬衬 |

验收现状（2026-11-24 从头复查）：`photo-dieline batch` 给每个类定**成熟度**（机器可判定的前三档；逐类明细在 `output/zoo100/batch_report.json`，根因见 [docs/reviews/recheck_2026-11-24/findings.md](docs/reviews/recheck_2026-11-24/findings.md)）。

| 级别 | 类数 | 判据 | 现状 |
|---|---|---|---|
| **L2 折叠有效** | **1** | L1 + 折叠闭合/尺寸/穿插全过 + 折线语义已声明观察面约定且自洽 + 每条折线的 ±35°/180° 扰动都被闭合判据检出 | 仅 `gable_top` 金标 |
| **L1 展开几何有效** | 83 | schema + 展开拓扑 + 两个导出件独立解析全过 | 都未声明折线语义约定；其中 65 类的闭合判据存在扰动漏检 |
| **L0 仅已注册** | 16 | 模板能构建 | 15 类展开图面板重叠/裁切缝切穿结构，1 类底板自交、导出被拒 |
| L3 样件验证 / L4 生产签核 | 0 | 实物裁切、折叠、尺寸回测 / 指定工艺人工签核 | 尚无任何类做过实物试制 |

**过门不等于可制造。** 全园 1591 条折线中 1066 条（67%）的 MOUNTAIN/VALLEY 标注与"以父面板正面为观察面"的约定不一致——除金标外，现有导出的两个压线图层语义不可信；另有 37 类粘口折回自身墙板（筒体不闭合）、2 类无底板，现有门检不出（findings F4-24…F4-28）。100 类中 39 类是同一家族按多边形边数派生的变体，尚未对齐 ECMA/FEFCO 编码。contact sheet 见 `docs/images/zoo100_contact_sheet.png`（绿 L2 / 橙 L1 / 红 L0）。

## Pack10K-Retail：零售包装 simulation-ready OpenUSD 数据集产线（10K 生产构建完成）

模板动物园之上的一条**数据集产线**（对标 NVIDIA USDCraft-10K，垂直域差异化）：
参数化模板 × 种子化采样 → USD 导出（`/Asset`、Z-up、米制、PhysX 刚体+克重推导质量、净图 UV 印刷层）
→ 逐件跑 [NVlabs/USDCraft 官方验证器](https://github.com/NVlabs/USDCraft)（Apache-2.0，10 项命名检查）
→ SimReady 侧车（model.json / packaging.json / conformance / build.json 再生凭证）→ 深浅双缩略图。

- **10K 生产构建实测**（2026-11-25）：10,000 次尝试 → **9,386 件 GREEN（产率 93.9%），
  全程 16.4 分钟（单 Mac，全链 98ms/件），API 成本 $0**；614 件门禁拒绝（fail-closed 逐族入账）
- **独立验收 VSR = 1.0**（9386/9386 零失败；验收器异源于生产门禁：水密性/退化/尺寸核账/
  物理字段/接触结判据，`scripts/packbench_validator.py` — 三轮战果：抓未焊接→焊接→抓退化/重复面→三角过滤）
- **对标 USDCraft**：单件 $0.851/4.9min（LLM 逐件+修复回路）vs 我们 $0/0.098s（家族冻结+确定性采样），
  10K 约当 $8,510+ agent·小时 vs 16.4 分钟；实测对比表见 `docs/production_capacity.md` §七
- **一对一类别审计**（`docs/usdcraft_1v1_audit.md`）：拉取对方 31 个包装/零售容器类 277 件与我方
  310 件同判据电池对跑 — 我方 100% 全过 vs 对方 25.6%（对方唯一系统性失配：自报尺寸与
  自家渲染几何 >2%，人工复核坐实）；新家族 pizza_box 实证家族级 LLM 成本 ~35 分钟会话
- **五域合规台账**（[docs/nvidia_compliance_ledger.md](docs/nvidia_compliance_ledger.md)）：170 usdc
  （酒饮 11 / legacy 4 / 零售设备 20 / 参数变体 35 / TDE 纸包装试点 100）逐件 NVIDIA 原版验证器
  15 项检查 **170/170 PASS**；打包契约 8 文件同构（meta / 包清单哈希链 / BOM / 双 conformance
  fail-closed 实跑判决）+ usdc 伴生 model.json 快照 + 双缩略图，单命令审计
  `scripts/nvidia_audit_all.py`（时间戳证据 JSON；曾自纠 meta COM 缺失 0→170/170）
- **方言对照实验**：NVIDIA 自家带关节件在 generic/newton 后端同样 FAIL（同款冲突错误）→
  按后端分目录、单文件单方言 = 其发行模型；我方 PhysX 方言选择逐字同构
  （控制实验记录见姊妹仓 `docs/usdcraft_study.md` §〇e）
- **全链非 CUDA**：CPU/Metal 可复现，种子+SHA bit 级再生
- **拒收先验集**入账（近退化参数 + 拓扑拒绝记录）+ 逐族产率谱（hexagonal 78%/prism 41%/tube 15%）
- HF 预览包 358MB 就绪（498 件，cc-by-4.0）；证据链：`docs/reviews/pack10k_r1_verdict.md`、
  `docs/reviews/pack10k_scale10k_{vsr,yield}.json`、`docs/pack10k_coverage_matrix.md`

## 视觉对标战役：十三轮 GPT 对抗评审 → 终局签署 VISUAL PARITY — PASS

四组代表资产（瓦楞箱/玻璃酒瓶/拉环罐/铰盖保鲜盒）与 NVIDIA USDCraft 参照渲染的对抗性视觉对标，
经 **十三轮独立评审 + 作者回注循环** 达成：终局签署 **平均 7.575 vs 7.950（差 −0.375），四行全部进入 ±0.5 打平区间**。

| 行 | R1 起点 | 终局 | NVIDIA | 差 | 提升 |
|---|---|---|---|---|---|
| R422 瓦楞箱 | 4.5 | 7.4 | 7.8 | −0.4 | +2.9 |
| R091 玻璃酒瓶 | 1.5 | 7.8 | 8.3 | −0.5 | **+6.3** |
| R043 拉环罐 | 2.0 | 7.3 | 7.5 | −0.2 | +5.3 |
| R037 铰盖保鲜盒 | 3.0 | 7.8 | 8.2 | −0.4 | +4.8 |

方法论（详见 [docs/CAMPAIGN.md](docs/CAMPAIGN.md)）：**六层闭环** = 作者合同(G-F1..F7) → LLM Author 回注循环 → 编译门禁 → usdc 物理验证（NVIDIA 官方验证器 physx PASS 15 同判）→ 合同渲染（黑棚/确定性取景/材质库）→ 双轨评审（G-F8/G-F8b 图像门禁 + 像素级 6 指标框架 + GPT 主观打分）。

GPT 终局沉淀五条研究认识：结构语义优先于渲染精修 · 工程正确性≠视觉正确性 · 几何存在≠几何可见 · 材质语义本身就是资产能力 · 视觉门禁必须接受反例挑战。评审全文与对照板见 `docs/reviews/` 与 `hfpackage/docs/`。

## 里程碑

| 阶段 | 内容 | 状态 |
|---|---|---|
| **M1** | gable-top 屋顶包垂直切片：照片+三尺寸 → Geometry IR → 自研 2D 布局 → 1:1 分层 SVG/PDF → 纯 Python 折叠 QA（十门） | ✅ **VALIDATED**（2026-11-24 复查修复后重验：十门为独立解析核对 + 手算金标对账 + 70 项测试含变异矩阵回放；模板成熟度 L2_KINEMATIC） |
| M2 | 模板库扩展（FEFCO 0201）＋ **Twins Data Engine**（合成孪生数据飞轮）＋ T1 箱型分类 / T2 参数回归 | 模板动物园 100 类（成熟度 L2 1 / L1 83 / L0 16）；TDE v0.8；T1/T2 **仅合成域结果**（分类 top-1 71.1%；比例回归相对误差 5.4–5.8%），真实照片上未达可用（findings F2-01…F2-10） |
| M2.5 | 货架孪生渲染 + ESR 资产样例（`scripts/build_hxl_shelf.py` 与三门脚本） | **实验性，建议迁出本仓**：资产层与验收报告在复查中发现失效（findings F4-04…F4-09） |
| M3 | TRELLIS.2 视觉辅证 · 智能补参交互 · 端到端候选 IR 研究 | 规划 |

## 快速开始（M1 垂直切片）

```bash
pip install -e ".[dev]"

# 一条命令: 规格 (+可选照片证据) → IR / 1:1 分层 SVG / 分层 PDF / QA 报告
# 尺寸全部来自 spec (实测/可信来源优先于参数, 矛盾即拒绝); 照片只作证据存证 (qa-report input_usage 如实声明)
# 仓内自带公版参照照 (USDA PD): 也可换成你自己的实拍
photo-dieline build --spec examples/gable_top/spec.json \
  --photo examples/gable_top/reference_photo.jpg --out examples/gable_top/artifacts

# 逆向闭环: 实拍 → 逆向刀版/CAD → 折叠孪生渲染 → 与实拍并排对比
photo-dieline build --spec examples/gable_top/spec_usda_halfpint.json \
  --photo examples/gable_top/reference_photo.jpg --out examples/gable_top/artifacts
photo-dieline render --ir examples/gable_top/artifacts/geometry-ir.json \
  --photo examples/gable_top/reference_photo.jpg \
  --out examples/gable_top/artifacts/compare_usda.png

pytest tests/   # 70 项机器验收 (含负探针、变异矩阵回放、模板适用域边界、测量合同)

# 可选: B0 参数化测量 (单视角标注关键点 + 内参 + 一条实测边 → 绝对尺寸, 比例 MAE ≈ CNN 的 1/7)
pip install -e ".[measure]"; 详见 src/photo_dieline/measurement/solve.py 与 docs/reviews/recheck_2026-11-24/findings.md §5.4
```

输出 `artifacts/`：`geometry-ir.json`（五对象协议）· `dieline.svg` · `dieline.pdf`（7 图层 OCGroups）·
`qa-report.json`（G01-G10 门禁）。照片门 ≥1000px；折叠闭合残差 ≤0.2mm；golden 尺寸 ≤0.5mm。

## 设计文档

- [DESIGN.md](DESIGN.md) — 架构方案 V1.0（GPT 三轮评审冻结版）
- [docs/adr/README.md](docs/adr/README.md) — 11 项架构决策台账
- [docs/reviews/gpt_design_all_rounds.md](docs/reviews/gpt_design_all_rounds.md) — GPT 评审原始判决全文

## License

MIT（见 [LICENSE](LICENSE)）。第三方依赖与数据来源许可见 `THIRD_PARTY_NOTICES.md`（随 M1 交付）。
