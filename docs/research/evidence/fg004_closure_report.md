# FG-004 结案报告: prism n12 "家族闭合缺陷" 根因反转 (调用方契约违反, 无家族缺陷)

日期: 2026-11-28 | 状态: ROOT_CAUSED (R23-A 主体) | 结论: **无家族缺陷; 全部异常由调用方两处参数遗漏导致**

## 根因 (S2 交付)

**缺陷 1 (Pilot-10 编译脚本, 产生 5 件 QA_FAIL)**: `p10_ycb_compile.py` 圆柱/瓶映射只传 `{n, side, h}`, 漏传 `tuck_depth` → merge 后 tuck_depth=30 (n=4 模块默认) ≠ apothem(12, side) → 盖片折深不达轴线 → **G04 如实 FAIL (设计内契约执行, 非 bug)**。源码 prism_dust.py 头注 27-29 行明文契约: "用户自定义 side 时须同步给出一致的 tuck_depth, 否则 G04 如实 FAIL"。

**缺陷 2 (边界扫描诊断, 产生 "side≈60 幻影窄带")**: 诊断脚本传参漏 `n` → 模块 DEFAULTS n=4 生效 → 所谓 prism_dust_n12 扫描实际全部是 **n=4 棱柱**。apothem(4, side)=side/2; 默认 tuck_depth=30 → 闭合当且仅当 side/2≈30 (±TOL 0.2mm) → **[59.9, 60.1] 窄带 = n=4 幻影**, 与 n12 无关。tuck/open 类的异常带同理。

**验证 (决定性实验)**: n=12 + side=Ø·tan(π/12) + tuck_depth=÷2 (契约一致) → closure_checks 全残差 0.0 (t{i}.far_to_axis 实测 0.0, 直接读折叠坐标复核)。

## 修复与回归 (S4/S5 交付)

- `p10_ycb_compile.py` 补传 `tuck_depth=Ø/2`
- **P10-RUN-03 census: 10/10 编译+NVSDK 双过** (RUN-01 5/10 → RUN-02 形状修正 → RUN-03 契约修正; 三版台账均保留)
- DIM-01 RUN-03: 9/10 严格 PASS + 006 PASS_VS_INPUT_APPROX (Ø 近似已声明, 另行登记)

## 影响范围更正 (S3)

- 原 prism_n12_family_defect.json 的 "家族级潜伏缺陷" 结论 **作废** — 7×5 网格、合法样本域失败、五件外部候选失败全部由上述两处调用方 bug 解释, 无一需要修改编译器/折叠引擎
- 冻结发行集 9,386 件不含 prism_dust SKU 的调用方 bug (pack10k 管线经 sample_variant 生成完整参数域, 含一致 tuck_depth) — 无需任何重编译
- "内部 QA 失败件仍过 NVSDK" 观察 (R22 §2.1) 结论不变且更有力: 结构合法性与折叠闭合 QA 是独立评价层

## 参数域契约试点 (Family Parameter Domain Contract, R22 §七)

prism_dust 家族契约字段首次落档:

| 字段 | 值 |
|---|---|
| parameter_schema | n∈{4..12}整数 / side mm / h mm / tuck_depth mm / glue_w / board_t |
| valid_domain | side>0, h>0, glue_w>0, board_t>0; **tuck_depth=apothem(n,side) (闭合契约)** |
| geometric_invariants | 合法域内: 盖/底星远缘中点落轴心, 防尘翼贴宿主墙平面 (closure_checks 五判据 ≤0.2mm) |
| topology_contract | 闭壳 (dust 变体) |
| boundary_cases | 侧 35 点网格 (RUN-03 口径重跑待执行) |
| invalid_cases | tuck_depth≠apothem → G04 如实 FAIL (契约拒绝语义, 非缺陷) |
| known_limitations | bottle 无原生家族 (近似通道另立); d_i 防尘翼深 df=min(15, 0.3·side) |
| verified_domain | n=4 全域(历史 pack10k) + n=12@契约一致(本轮十件罐体实测) |

## 教训登记

1. **类注册共享模块 + 参数默认值 = 调用方易漏参数**: prism_dust.py 一个模块服务 n 个类, cls_id 由参数 n 推导 — 调用方漏传 n 静默降级为 n=4 且 cls_id 跟着变, 诊断时极具迷惑性。建议: build_ir 对 "模块名含 nN 但参数 n≠N" 的情况显式告警 (待 GPT 授权后实施)
2. 负结果的负结果也要归档: 本报告与 prism_n12_family_defect.json 并存, 前者更正后者
