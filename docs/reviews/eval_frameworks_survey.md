# "AI 生成图 vs 原图差异"评审框架与论文全景 (2026-11-21 调研)

目的: 为 ESR 渲染门的评审方法学找文献坐标与升级路径。按"与参照的关系"五问分类,
每问列代表框架/论文 + 对我方管线的映射。

## 0. 问题分类学 (评估问题的类型决定工具)

| 问 | 含义 | 我们对应 |
|---|---|---|
| Q1 分布级 | 一批生成图 vs 一批真图的集合统计 | 像素分布门 (单图简化版) |
| Q2 成对全参照 | 生成图 vs 逐像素对齐的真值原图 | 语义覆盖门 (光栅化逐 prim 归属) |
| Q3 单图无参照 | 单张图"真不真/好不好" | GPT 判别协议 |
| Q4 语义对齐 | 生成图 vs 文本/意图 | planogram 消费验证 |
| **Q5 结构对齐异内容** | **渲染 vs 同场景实拍 (内容不同)** | **D-排序协议 (主战场)** |

## 1. 分布级 (Q1)

- **FID** (Heusel et al., NeurIPS 2017) — Inception 特征空间高斯距离, 事实标准;
  已知缺陷: 样本量敏感、Inception 特征陈旧、对少数图无意义
- **KID** (Bińkowski et al., ICLR 2018) — 核 MMD, 小样本无偏
- **CMMD** (Shan et al., 2023) — CLIP 特征 + MMD, 与人类判断相关性优于 FID
- **cFreD** (arXiv 2503.21721, 2025) — 条件 Fréchet 距离, 报告与人类判断相关
  高于 FID/CMMD
- **Precision/Recall** (Kynkäänniemi, NeurIPS 2019) → **Density/Coverage**
  (Naeem et al., ICML 2020) → **Probabilistic P&R** (Park, ICCV 2023) →
  **FLD+** (2024, 数据高效) — 保真/多样性分解线
- 综述: arXiv 2403.11821 "A Survey on Quality Metrics for Text-to-Image Models"

## 2. 成对全参照 FR-IQA (Q2)

- **PSNR/SSIM** (Wang 2004) — 跨内容比对无效 (我们场景: 内容不同, SSIM 不适用)
- **LPIPS** (Zhang et al., CVPR 2018) — 深度特征感知距离, 生成评估最常用
- **DISTS** (2022, 纹理偏置鲁棒), **DreamSim** (2023), **NLPD** (Laparra 2017)
- **HDR-VDP-2 + LPIPS + DISTS + SSIM 用于计算机生成渲染的系统综述**
  (PMC, 2025) — 直接命中"渲染评估"场景的指标选择证据
- **"Toward Generalized IQA: Relaxing the Perfect Reference Assumption"**
  (CVPR 2025) — 参照图本身非完美质量时的泛化 (我们的参照是手机实拍!)
- **DeepSim** (Czolbe, MIDL 2021) — 语义相似度用于图像配准评估

## 3. 无参照 NR-IQA / 真实感评分 (Q3)

- **NIMA** (2018, MOS 预测) → **HyperIQA** (2020) → **TOPIQ** (TIP 2024) →
  **MANIQA**
- **Q-Align** (ICML 2024) — LMM 统一 IQA/IAA/VQA, 离散文本等级评分, 当前最强
  开源可本地部署 (one-align 权重)
- **Compare2Score** (2024), **Q-Eval-100K** (CVPR 2025)
- **GLIPS** (2024, arXiv 2405.09426 / IEEE) — 专评 AI 生成图照片级质量的
  全局+局部感知分
- 领域先例: **铁路驾驶模拟器 2D 帧照片级评分** (2024) — 与我们场景同构
  (仿真图 vs 真实感目标)

## 4. 频域/伪影物理臂 (Q3 的客观信号)

- **Dzanic et al., NeurIPS 2020** "Fourier Spectrum Discrepancies" — 生成图
  高频谱系统性缺口, 尺度/旋转不变判别
- **CVPR 2021 "A Closer Look"** — 谱峰判别不可全信 (反例)
- **SSD-GAN** (AAAI 2021) — 空间+谱域双 realness (可作统计而非训练)
- **"Beyond Spectral Peaks"** (2025) — 谱峰非根本伪影, 检测线索再解释
- **GenImage** (NeurIPS 2023, 百万级检测基准) + few-shot 泛化检测 (ICML 2025)
- 综述: arXiv 2502.15176 / ScienceDirect 2026; 中文: 复旦《人工智能生成图像
  检测技术综述》

## 5. 语义对齐与 LMM 判官 (Q4)

- **CLIPScore** (2021) → **ImageReward** (NeurIPS 2023) → **HPSv2** (2023) →
  **PickScore** (2023) — 人类偏好奖励模型族 (可本地打分, 权重开源)
- **TIFA** (ICCV 2023, VQA 计分) → **DSG / Davidsonian Scene Graph**
  (ICLR 2024) — 问题生成-作答协议加依赖图与唯一答案约束, 防评审幻觉
- **VQAScore** (ECCV 2024) → **GenAI-Bench** (2024)
- **VIEScore / GPT4-Eval** — GPT-4V 判官族
- **GenEval 2** (2025) — 基准漂移问题
- **"What makes a good metric?"** (2024), **"Who evaluates the evaluations?"**
  (NeurIPS 2024), **"Evaluating the Evaluators"** (2025) — 自动指标可靠性审计
- **A-Bench** (ICLR 2025) — LMM 作 AIGI 评审者的能力诊断: 语义评估可靠,
  **感知质量评估有偏** — 与我方"判别协议类别地板"发现一致
- **"Fooling the LVLM Judges"** (EMNLP 2025) — LVLM 评审的视觉偏置系统证据
- **"Mitigating Perception Bias"** (2024) — 免训练偏置缓解

## 6. 渲染真实感专项 (Q5 — 我方主战场)

- **McNamara et al. 2000** "Comparing Real & Synthetic Scenes using Human
  Judgements of Lightness" + **Rademacher 2001** "Measuring the Perception of
  Visual Realism" — 经典: 真实感由**相对关系** (亮度恒常/比较判断) 决定,
  非绝对像素; 我方 D-协议 (比较排序+锚分离) 是此脉络的 LMM 现代版
- **"Assessing Photorealism of Rendered Objects in Real-World Images"**
  (IEEE VRW 2025, arXiv 2407.01767) — 透明可复现用户研究协议模板
- **"Learning a Photorealism Score"** (2024, 铁路模拟器) — 同构场景的评分学习
- 我方协议缺口对照: 无第二评审员 (文献均多人)、无问题分解 (DSG 式)

## 7. 映射: ESR 验收链 → 文献坐标 → 升级路径

| 我方现有 | 文献坐标 | 升级路径 (性价比排序) |
|---|---|---|
| 像素分布门 (EMD/边缘/高光/对比) | Q1 分布级的单图手工简化 | ①加**频谱径向分布**臂 (numpy FFT, 零依赖, Dzanic 信号) ②多版本聚合可升级为 CMMD 式 |
| 语义覆盖 CPU 光栅门 | Q2 结构对齐 (逐 prim 归属, 已超常规 IoU) | 维持, 是我方独有 |
| GPT 判别协议 (渲染恒 3.8-4.0/真图 8.7-9.5) | A-Bench: LMM 感知评估有偏 — 结论一致 | 维持"只作信号不作判停" |
| GPT 排序 D-协议 + 真图锚 | McNamara 比较判断 + DSG 问题分解 + P&R 分解 | ①DSG 式**问题清单先行** (防幻觉) ②第二评审员 ③强制 2AFC |
| (缺) 人类偏好分 | HPSv2/ImageReward 开源权重 | 本地 MPS 部署, 给版本自动打偏好分, 减 relay 轮次 |
| (缺) 频谱臂 | Dzanic 2020 | FFT 径向平均谱对比, 最廉价的客观"真伪"信号 |

## 8. 结论

1. 我方"五问分离 + 比较判断 + 锚点校准 + 客观分布臂"的组合在文献中各支均有
   坐标, **没有现成单一框架覆盖 Q5 (结构对齐异内容)** — D-协议+像素门组合
   本身即贡献形态, 可按 DSG 模板形式化后作为 ESR Evidence 层的对外协议。
2. 三个立即可落地的强化: 频谱径向臂 (像素门 v1.1)、HPSv2 本地偏好分、
   DSG 式问题分解协议。
3. 文献一致警告: LMM 感知质量评估有偏 (A-Bench/EMNLP 2025) — 我方"判别
   协议不判停"的纪律与文献一致, 应继续坚持。
