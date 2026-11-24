# 产能评估: 达到并超越 USDCraft-10K 的生产路线 (2026-11-25)

> 问题: 咱们能否达到 USDCraft-10K 的水平, 甚至超越 — 从生产角度。
> 结论先行: **在零售包装域, 能, 且是生产架构上的代差优势; 不在其铰链家电域对标关节多样性。**
> 依据: 本文全部数字来自本仓实测 (批跑计时) 与 NVlabs/USDCraft 公开材料 (arXiv 2610.11322, README)。
> 配套: `scripts/usdcraft_gate.py` (兼容门), `docs/usdcraft_study.md` (思路研究, openusd-retail-twin)。

## 一、两种生产架构的本质差异

| 维度 | USDCraft 生产 | 我们 (参数化模板家族) |
|---|---|---|
| 单件成本 | LLM 写 `model.py` 5–10 分钟 + 修复回路 (非确定) | 参数采样→build_ir→折叠→门禁→USD: **秒级, 零 API** |
| 10K 总成本 (估算) | ~830–1700 agent·小时 + API 费用 (NVIDIA 级算力预算) | 家族冻结 (一次性) + 机器天级, **~$0 API** |
| 可复现性 | LLM 非确定; 每件是孤儿程序, 产物即唯一凭证 | 种子+SHA → **bit 级可再生**, 参数即凭证 |
| 拓扑来源 | LLM 逐件发明 (开放式拓扑是强项) | 拓扑**封閉式**于家族 (包装拓扑本来封闭 — LLM 用在家族级) |
| LLM 的位置 | 每件一次 (摊薄=1) | **每家族一次** (摊薄=∞): 新家族由 agent 按契约写, 门禁冻结后无限变体 |
| 制造真实性 | 视觉玩具 (无制造约束) | **刀版可折可印可量产**: PDF/SVG 刀版+压线+纸板物理 |
| 证据层 | 无 (记 extents 但无对账/无不确定度) | **ESR 测量有效性链**: 声明 vs 折叠 vs USD 三方对账 + 容差门 + 可辨识性标签 + 双率 |

关键洞察: 包装拓扑是**封闭集合** (16 个家族模块已覆盖主流零售形态), USDCraft 用 LLM 逐件
写程序解决的是"拓扑开放"问题 — 我们域内这个问题不存在。把 LLM 挪到**家族级** (一次性冻结),
单件生产就是纯确定性计算。这是成本结构上的代差, 不是追赶。

## 二、现有底座 (已实测)

- 16 个家族模块 (`parametric/`): gable_top/gable_variants (脊线胶条/无鳍/螺盖/宽鳍缝)、
  aseptic_brick、brick_250ml、RSC、tray、box_essentials (天地盖+web 条)、generic_prism
  (**含参数化 n 边锥台 — 单模块无限拓扑变体**)、food_packs、sundry、odd/fan 链、closure 变体…
- 每家族自带: G03 网单环 / G04 闭合 ≤0.2mm / G05 bbox 对账 ≤0.5mm / G06 零重叠 +
  **负探针强制** (Rodrigues 绕真实铰链轴扰动, 残差须从 1e-14 爆到 mm 级) + M1 金样合同 (13 测试)。
- 批跑器 `batch.run_batch` (单类失败不杀批), TDE 渲染域随机化管线, pd-guard 硬门禁,
  测量层 (参数化求解 + delivery_policy + 双率), usdcraft_gate 兼容门。
- 真实尺寸分布台账 (coldcase dimension audit: 零售各品类实测值) — 变体采样可**证据接地**,
  不造幻想尺寸。

## 三、产能数学 (2026-11-25 本机实测, 单 Mac, 无 GPU 集群)

**实测批跑** (`batch.run_batch`, 全 100 注册类, 含 Blender 缩略图): 总 67.2s,
**单件 672ms 全链路**; 状态 84 GREEN / 15 QA_FAIL / 1 ERROR。

失败解剖 (生产成本模型佐证 — 门禁 fail-closed 工作正常):
- 15 QA_FAIL 全部 = **G03 折线端点违例** (折线端点须为面板多边形顶点): pyramid_frustum_n4–n12
  全族 9 件 + gable_screw_cap + crashlock_divider + food/egg/cup_sleeve 等托盘食品族 —
  均为契约已记载坑位, 每族一次性修 (family-level cost);
- 1 ERROR = divided_tray_3comp 默认参数 floor 自交 (真模板 bug, 待修)。

产能推演:
- 路径: 16 家族 (100 类) → 修绿 16 件 → agent 按契约扩至 50–100 家族 (每族 ≈1 天, 一次性)
  → 每族参数采样 100–200 SKU (尺寸×克重×版面×封口) = **10K–20K**;
- 单件: 编译+门禁+缩略图 **0.7s 实测**; 生产级渲染加 TDE 品质贴图后估 5–15s →
  10K ≈ **机器 14h–42h (1–2 天), API 成本 ≈ 0**;
- 对照: USDCraft 生成一件 5–10 分钟 (GPT-6 Astra), 10K 需 NVIDIA 级预算且不可复现。

## 四、"超越"的可主张清单 (每条可验证, 非口号)

1. **SimReady Package 1.0.0 合规** (结构门已探明, defaultPrim 一行修; FET conformance 记录
   基建待建) — 打平;
2. **+ESR 证据层** (他们为零): 每件携带 声明尺寸+来源 vs 折叠实测 vs USD stage 三方对账
   + 容差门 `max(tol,k·u)` + 交付状态 (AUTO/MANUAL/REFUSED) + 可辨识性标签;
3. **+拒绝样本集**: R03 类近退化参数**主动生成并打 REFUSED/OUT_OF_DOMAIN 标签入 manifest**
   — 没有公开数据集发布"系统知道自己不知道"的标签; 这是超越的最硬一条;
4. **+制造真值**: 刀版可折可印 (PDF/SVG + 压线/粘口/鳍位), 纸板克重→质量/质心物理可导
   (对应他们 mass_inertia_or_collision_derivation 检查, 我们是**真推导**不是 LLM 拍数);
5. **+确定性再生**: 种子+参数+模板 SHA → bit 级复现; 数据集整体可再生;
6. **+域独占**: 零售包装 + 货架场景资产 — 他们 1000 类中为零。

## 五、诚实边界 (不对标项)

- **关节多样性**: 他们 8222 件带关节 (服务机器人操作)。包装的关节本来就少 (瓶盖/嘴/翻盖,
  少量 revolute/prismatic), 我们不追这个数, 也不需要;
- **类别广度**: 1000 类 vs 我们 100 家族 — 轴不同: 他们"类别"=prompt 多样性, 我们=制造真实
  模板族 × 深参数空间。可以借鉴其思路用 agent 扩家族, 但不为凑数造不可制造的拓扑;
- **渲染/材质丰富度**: 他们有视觉反馈回路修外观; 我们材质来自印刷工艺真值 (克重/涂层) 而非
  视觉拟合 — 外观多样性是后续可借其思路补的轴。

## 六、生产线 P0 建设清单 (达到 10K 前必须落齐)

| # | 项 | 依据 |
|---|---|---|
| 1 | USD 导出补 defaultPrim=/Asset + Z-up/meters/kg + PhysX collision/mass/COM (纸板克重推导) | usdcraft_gate 缺口; 包结构约定 |
| 2 | 尺寸证据门: 声明(params) vs 折叠 bbox vs stage bbox, max(tol,k·u) 容差, 入 manifest | ESR 定义域; 已有 R5 compare 语义 |
| 3 | 变体采样器: 真实零售尺寸分布 × 纸板克重表 × 印刷版面 × 种子纪律 (失败留痕/批中禁改) | coldcase 台账; TDE 跑批纪律 |
| 4 | SimReady 包基建: packaging.json (id/许可/sha256) + model.json 侧车 (qcode/extents/mass) + FET conformance 记录 + 双缩略图 (az45/el30 朝 −Y) | USDCraft 包结构约定 |
| 5 | manifest.csv + ESR 标签列 (delivery/identifiability/u_ref) | 拒绝样本集 |
| 6 | 家族扩容节奏: agent 按契约 (pack-zoo-template-authoring) 逐族写+冻, 每族验收四步 | 现行契约 |

**试点 (P0 收口判据)**: 4 家族 × 125 变体 = 500 件全链路批 → 全绿 + manifest + conformance +
ESR 标签 + usdcraft_gate 通过率 → 通过后放开 10K。

## 七、10K 实测战报 (2026-11-25 终版, 上节推演全部兑现)

上节 P0 建设清单 6 项全部落地并实测。10K 生产构建 (`output/pack10k_scale10k`, 证据
`docs/reviews/pack10k_scale10k_{vsr,yield}.json`):

| 维度 | USDCraft-10K | Pack10K 实测 |
|---|---|---|
| 10K 总耗时 | 830–1700 agent·小时 (估算) | **16.4 分钟** (984s, 单 Mac) |
| 单件 | 5–10 分钟 + 修复回路 | **0.098s** (qa 48.1ms/fold 0.9/export 27.4/validate 3.2) |
| API 成本 | $0.851/件 → 10K ≈ $8,510+ | **$0** |
| 合格产出 | 10,000 (含 LLM 修复回路不可复现件) | **9,386 GREEN + 614 门禁拒绝** (fail-closed) |
| 独立验收 | 自带验证器 (10 命名检查) | **VSR = 1.0** (9386/9386, 验收器异源, 10 检查) |
| 产率诚实度 | 未披露逐类产率 | 逐族产率谱入档 (hexagonal 78%/prism 41%/tube 15%) |
| 可复现 | 非确定 (孤儿程序) | 种子+SHA bit 级再生 |
| 产线进化实证 | — | 验收器三轮战果: 抓未焊接→焊接→抓退化/重复面 1125+371→三角过滤+片材复杂体判据 |

与第五节边界一致的不变项: 不追关节数/类别广度/渲染多样性; 域独占 (零售包装) + 证据层 +
拒绝样本集 + 制造真值四条超越主张全部在 10K 实测件中兑现。
