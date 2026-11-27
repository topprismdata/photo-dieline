# Gemini 外部评审: 数据集价值 vs NVIDIA USDCraft (2026-11-27)

评审对象: photo-dieline 语料 (202 精选 + 9386 全量普查, NVIDIA 原版验证器全绿)。
评审人: Google Gemini (用户会话, 全文取回)。完整原文见会话; 要点如下。

## 判决
- 数据集价值 **4.5/10**; OpenUSD 工程合规与管线纪律 **7.5/10**
- 发表成立, 但必须放弃「通用零售数据集」叙事, 定位为
  「对 NVIDIA USDCraft 发行契约/方言规范/失败域的独立工程审计与程序化反例研究」
- 首选 venue: arXiv 技术报告 + GitHub + HF 小型审计基准包
- 次选: SIGGRAPH Tech Comm / JOSS / ICRA·NeurIPS Workshops; 不建议 NeurIPS D&B/CVPR 主轨

## 三个可攻击点 (全部承认)
1. 过拟合验证器: 静态 Linter 满分是工程预期非发现; 缺下游物理仿真证据 (Isaac/MuJoCo 1000 步)
2. shopping_cart 反例跨范式 (正向参数化 vs 逆向重建); 应改写为「混合管线架构论点」
3. 293 部件无关节 = 静态壳子, 非真 PhysX Articulation 资产

## 一句话结论
值得作为 arXiv+GitHub/HF 合规审计基准包立即发表; 补齐关节资产+下游仿真评测前,
不值得继续投入数据集扩张。

## 采纳状态
- ①③ 真缺口, 已在台账披露, 列为后续方向 (articulated 变体 / 下游仿真评测)
- ② 叙事问题, 公开面 README 已按「独立审计」定位撰写
