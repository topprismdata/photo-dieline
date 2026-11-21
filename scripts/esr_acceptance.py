#!/usr/bin/env python3
"""esr_acceptance: 三门合一验收 (ESR Step D).

门① 物理: MuJoCo 静置 (verify_sku_physics)
门② 语义: 分割覆盖 (gate_semantic_coverage.json)
门③ 渲染对齐: 参照对齐协议最新判决 (docs/reviews/shelf_convergence.md D6b)
全过 → ESR COMPLIANT, 报告落盘 docs/shelf_twin/esr_acceptance.json
用法: python3 scripts/esr_acceptance.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify_sku_physics import MANIFEST, verify  # noqa: E402

ROOT = Path(__file__).parent.parent


def gate_physics():
    ok, fails = 0, []
    for sku in MANIFEST["skus"]:
        stable, settled, ke, z, z_exp = verify(sku)
        if stable and settled:
            ok += 1
        else:
            fails.append(sku["id"])
    return ok, len(MANIFEST["skus"]), fails


def gate_semantics():
    j = json.loads((ROOT / "data/shelf_twin/gate_semantic_coverage.json").read_text())
    return j["ok"], j["ok"] + j["fail"], [r["sku"] for r in j["results"] if not r["pass"]]


def gate_render():
    # 渲染对齐门: 参照对齐协议最新判决 (人工会话存证于收敛报告, 此处引用其落盘结论)
    j = json.loads((ROOT / "data/shelf_twin/render_gate.json").read_text())
    return 1 if j.get("pass") else 0, 1, [j.get("protocol", "?") if not j.get("pass") else ""]


def main():
    p_ok, p_n, p_fail = gate_physics()
    s_ok, s_n, s_fail = gate_semantics()
    r_ok, r_n, r_fail = gate_render()
    compliant = (p_ok == p_n) and (s_ok == s_n) and (r_ok == r_n)
    report = {
        "schema": "esr-acceptance/1.0",
        "gates": {
            "physics": {"ok": p_ok, "total": p_n, "fails": p_fail},
            "semantic_coverage": {"ok": s_ok, "total": s_n, "fails": s_fail},
            "render_alignment": {"ok": r_ok, "total": r_n,
                                 "protocol": "参照对齐 D6b (v28d 4.8 > v26b 4.2)"},
        },
        "compliant": compliant,
    }
    (ROOT / "data/shelf_twin/esr_acceptance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1))
    print(f"物理门 {p_ok}/{p_n} 语义门 {s_ok}/{s_n} 渲染对齐门 {r_ok}/{r_n}")
    print("ESR COMPLIANT" if compliant else "ESR NOT COMPLIANT")


if __name__ == "__main__":
    main()
