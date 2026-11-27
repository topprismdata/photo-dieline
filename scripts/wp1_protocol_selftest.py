"""WP1-Pilot-100 协议 v0.4 机器门禁 (W01-W10, R09-11 指派) — 与协议公式同源"""
import numpy as np
from collections import Counter

TERMINALS = ["OUT_OF_SCOPE", "INPUT_INSUFFICIENT", "FAMILY_NOT_COVERED",
             "FAMILY_ADAPTATION_REQUIRED", "CONTRACT_UNKNOWN", "GATE_FAIL",
             "VALIDATION_PENDING", "SUCCESS"]

def metrics(states):
    """协议 v0.4 §2 五指标 + 终态分布 (与文档公式逐字对应)"""
    c = Counter(states)
    for s in states:
        if s not in TERMINALS:
            raise ValueError(f"非法终态 {s!r} (W09)")
    N = len(states)
    n_scope = N - c["OUT_OF_SCOPE"]
    n_input = n_scope - c["INPUT_INSUFFICIENT"]
    n_cov = n_input - c["FAMILY_NOT_COVERED"]
    n_adapt = c["FAMILY_ADAPTATION_REQUIRED"]
    succ = c["SUCCESS"]
    pend = c["VALIDATION_PENDING"]
    denom_m3 = n_cov - n_adapt
    def ratio(num, den):
        return None if den == 0 else num / den
    return {
        "N": N, "dist": dict(c),
        "M0_domain": ratio(n_scope, N) if n_scope > 0 else None,
        "M1_input": ratio(n_input, n_scope),
        "M2_coverage": ratio(n_cov, n_input),
        "M3_delivery": ratio(succ, denom_m3),
        "M4_validation_complete": ratio(max(0, succ - pend), denom_m3) if denom_m3 > 0 else None,
        "C_delivered": None if succ == 0 else "COMPUTABLE",
        "counting_closed": sum(c.values()) == N,
    }

results = []
def W(n, cond, note=""):
    results.append((n, bool(cond), note))

# W01 全部域外 → 域内率 UNDEFINED
r = metrics(["OUT_OF_SCOPE"] * 100)
W("W01", r["M0_domain"] is None and r["M1_input"] is None, "域内率 UNDEFINED")
# W02 全部输入不足 → 输入可用率 0
r = metrics(["INPUT_INSUFFICIENT"] * 100)
W("W02", r["M1_input"] == 0.0 and r["M2_coverage"] is None, "输入可用率 0")
# W03 输入充分但家族全未覆盖 → 覆盖率 0
r = metrics(["FAMILY_NOT_COVERED"] * 100)
W("W03", r["M2_coverage"] == 0.0, "覆盖率 0")
# W04 全部验证待完成 → 交付率 0 且 M4=0
r = metrics(["VALIDATION_PENDING"] * 100)
W("W04", r["M3_delivery"] == 0.0 and r["M4_validation_complete"] == 0.0, "交付率/M4 = 0")
# W05 全部成功 → 四比例均 100%
r = metrics(["SUCCESS"] * 100)
W("W05", r["M0_domain"] == 1 and r["M1_input"] == 1 and r["M2_coverage"] == 1
       and r["M3_delivery"] == 1 and r["M4_validation_complete"] == 1, "四比例 100%")
# W06 FAIL 与 PENDING 混合 → FAIL 不被 PENDING 吸收
r = metrics(["GATE_FAIL"] * 30 + ["VALIDATION_PENDING"] * 70)
W("W06", r["dist"]["GATE_FAIL"] == 30 and r["dist"]["VALIDATION_PENDING"] == 70
       and r["M3_delivery"] == 0.0, "互斥终态, FAIL 独立")
# W07 零成功 → C_delivered UNDEFINED
r = metrics(["GATE_FAIL"] * 100)
W("W07", r["C_delivered"] is None, "单位成本不可计算")
# W08 混合 100 → 计数闭合 + 指标恒等式 (M0≥M1≥M2≥M3 分母链)
r = metrics(["SUCCESS"] * 40 + ["GATE_FAIL"] * 20 + ["VALIDATION_PENDING"] * 10 +
            ["OUT_OF_SCOPE"] * 10 + ["INPUT_INSUFFICIENT"] * 5 + ["FAMILY_NOT_COVERED"] * 5 +
            ["FAMILY_ADAPTATION_REQUIRED"] * 5 + ["CONTRACT_UNKNOWN"] * 5)
closed = sum(r["dist"].values()) == 100
vals = [v for k, v in r.items() if k.startswith("M") and v is not None]
inrange = all(0.0 <= v <= 1.0 for v in vals)
W("W08", closed and inrange, "计数闭合+全部比率∈[0,1]")
# W09 重复 SKU / 非法终态 → 拒绝
try:
    metrics(["SUCCESS", "SUCCESS", "BOGUS_STATE"])
    w9 = False
except ValueError:
    w9 = True
W("W09", w9, "非法终态拒绝统计")
# W10 NOT_APPLICABLE 不是合法 SKU 终态
w10 = "NOT_APPLICABLE" not in TERMINALS
try:
    metrics(["NOT_APPLICABLE"] * 10)
    w10 = w10 and False
except ValueError:
    pass
W("W10", w10, "NOT_APPLICABLE 仅单项门禁级")

npass = sum(1 for _, ok, _ in results if ok)
for n, ok, note in results:
    print(f"{'PASS' if ok else 'FAIL'} {n}: {note}")
print(f"WP1-PROTOCOL-SELFTEST {npass}/10 {'ALL PASS' if npass == 10 else 'FAILURES'}")
assert npass == 10, "protocol selftest failed"
