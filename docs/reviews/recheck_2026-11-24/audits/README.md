# 审计证据 (冻结于 HEAD 54b81ca)

三份只读审计原文与探针脚本, 数字全部钉定在修复前的提交 `54b81ca` (ZooAudit 用 `git archive` 快照重跑过)。
修复过程中这些缺陷会逐个消失 — 保留原文与探针, 是为了让"每个修复对应哪个破坏样本"可回溯 (GPT R1 T0.7)。

| 文件 | 内容 | 规模 |
|---|---|---|
| `core_audit.md` | 核心管线 (IR/折叠/QA/导出/CLI/测试) | P0×2 / P1×10 / P2×15 / P3×13; 含 27 项变异矩阵 (12 拦 / 15 漏) |
| `zoo_audit.md` | 100 类模板动物园的制造合理性 | P0×1 / P1×6 / P2×11 / P3×6 |
| `twin_audit.md` | 货架孪生渲染 + ESR 线 | P0×1 / P1×10 / P2×12 / P3×5 |
| `probes/probe*.py` | CoreAudit 的 11 个探针 (引擎/QA 变异矩阵/导出偏移/渲染等) | 可复跑 |
| `probes/probe5_replay_after_fix.py` | QA 变异矩阵探针适配到修复后接口的回放版 | 见 `findings.md` §5 |
| `probes/zoo_probe_head/` | ZooAudit 探针与 JSON 输出 | — |

注意: 审计里的行号指向 `54b81ca`; 其后的修复提交 (0487e77 起) 已移动这些行。
