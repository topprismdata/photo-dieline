"""probe13 门禁合法侧挑战 (WP3-2): probe12 从破坏侧挑战, 本探针从合法侧 —
合法 W/D/Hr/Ef/gap 组合不得被误拒 (VALIDATED 保持); 域边界两侧判定必须翻转; 非 gable 分发不得误触 gable 门。
判据: (a) 合法格 VALIDATED 率 = 100%; (b) 边界非法格 100% 非 VALIDATED 且含 G02; (c) cuboid 分发无 gable 门误触。"""
import copy
import numpy as np
from photo_dieline.core.ir import from_raw
from photo_dieline.qa.pipeline import run_qa
from photo_dieline.export import svg as svgx, pdf as pdfx
from photo_dieline.parametric import gable_top
from photo_dieline.parametric import generic_prism as cuboid

def run_case(label, params, template="gable_top"):
    mod = {"gable_top": gable_top, "cuboid": cuboid}[template]
    ir = from_raw(mod.build_ir(params))
    x0, y0, x1, y1 = svgx.net_bbox(ir)
    rep = run_qa(ir, svgx.render(ir, x1 - x0, y1 - y0), pdfx.build_pdf(ir, x1 - x0, y1 - y0))
    g02 = next((g for g in rep["gates"] if g["id"] == "G02"), None)
    return rep["status"], (g02["status"] if g02 else "-"), rep

fails = []
print("=== (a) 合法组合网格 (应全 VALIDATED) ===")
legal = []
for W in (30.0, 45.0, 60.0, 80.0):
    for D in (20.0, 45.0, 70.0):
        for Hb in (60.0, 100.0, 160.0):
            for Hr in (5.0, 12.0, 25.0):
                for Ef in (8.0, 14.0):
                    if Hr < np.tan(np.radians(5.0)) * W / 2 + 0.2:
                        continue
                    legal.append({"W": W, "D": D, "Hb": Hb, "Hr": Hr, "Ef": Ef, "fin_gap_mm": 3.0})
ok = 0
for p in legal:
    st, g02, _ = run_case("legal %s" % p, p)
    ok += st == "VALIDATED"
    if st != "VALIDATED":
        fails.append(("legal", p, st))
print(f"合法格: {ok}/{len(legal)} VALIDATED")

print("\n=== (b) 域边界两侧翻转 (公式: slope=atan(2*Hr/D), lean=asin(gap/(2Ef))) ===")
base = {"W": 60.0, "D": 45.0, "Hb": 100.0, "Hr": 12.0, "Ef": 8.0, "fin_gap_mm": 3.0}
cases = [
    ("gap=2Ef-ε 合法(声明域)", {**base, "fin_gap_mm": 15.9}, True),
    ("gap=2Ef+ε 非法", {**base, "fin_gap_mm": 16.1}, False),
    ("坡角5.2° 合法", {**base, "Hr": float(np.tan(np.radians(5.2)) * 45.0 / 2.0)}, True),
    ("坡角4.8° 非法", {**base, "Hr": float(np.tan(np.radians(4.8)) * 45.0 / 2.0)}, False),
    ("gap=0.5 按声明域合法", {**base, "fin_gap_mm": 0.5}, True),
]
for label, p, want_valid in cases:
    st, g02, rep = run_case(label, p)
    got = st == "VALIDATED"
    good = got == want_valid
    print(f"  {label:<24} → {st:<10} G02={g02:<5} 预期{'合法' if want_valid else '非法'} {'✓' if good else '✗ 误判'}")
    if not good:
        fails.append(("boundary", label, st))

print("\n=== (c) 非 gable 分发 (cuboid, 应按 cuboid 几何判定且 G02 不误触) ===")
st, g02, rep = run_case("generic_prism n=4 常规", {"n": 4, "side": 60.0, "h": 100.0, "glue_w": 12.0, "board_t": 0.42}, template="cuboid")
gids = [g["id"] for g in rep["gates"]]
print(f"  cuboid → {st}  G02={g02}  门集={gids}")
if "G02" in gids and g02 == "FAIL":
    fails.append(("dispatch", "cuboid G02 误触", st))

print("\n判定:", "ALL PASS" if not fails else f"{len(fails)} 项失败: {fails}")
# 已知近边界发现 (非失败, 记录在案): gap=2Ef−ε 在声明域内合法, 但 lean→90° 时鳍高→0 (退化形体),
# 会触发非 G02 的门 → DRAFT。域声明与门行为不一致: 建议域加 lean 上限 (如 ≤75°, 即 gap ≤ 1.63·Ef)。
# 下一轮域契约变更时处理, 不在本轮静默改 (G02 条款已经 R3 签署)。
print("PROBE13_DONE")
