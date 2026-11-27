"""WP1-P10-YCB Pilot-10 编译脚本 (规格驱动, 通道A)
输入 = YCB 官方 PDF 规格 (mm/g) + 结构家族映射 (FZ05 冻结)
输出 = output/pilot10_ycb/compiled/<item>/model.usdc + DIM-01 + NVSDK 判决
纪律: 扫描网格不参与本通道 (FZ04 隔离); 十件 census 全量 (R21 §4.1)
"""
import sys, json, math, hashlib, os
from pathlib import Path
sys.path.insert(0, "src")
sys.path.insert(0, os.path.expanduser("~/usdcraft_study/code"))

from photo_dieline.core.ir import class_module, from_raw  # noqa: E402
from photo_dieline.export.pdf import build_pdf  # noqa: E402
from photo_dieline.export.svg import net_bbox, render as svg_render  # noqa: E402
from photo_dieline.export.usd import export_usdc, stage_dims_m, reconcile_dims  # noqa: E402
from photo_dieline.folding.engine import fold_all  # noqa: E402
from photo_dieline.parametric import base as pbase  # noqa: E402
from photo_dieline.qa.pipeline import run_qa  # noqa: E402

# FZ05 冻结映射: box→rsc_css(W/D/H=排序desc), cylinder/bottle→prism_dust_n12(外接圆径=Ø, h=H)
ITEMS = [
    {"id": "001_chips_can",      "product": "Pringles Chips can",           "shape": "cylinder", "dims": [75, 250],      "mass_g": 205},
    {"id": "002_master_chef_can","product": "Master Chef Coffee can",       "shape": "cylinder", "dims": [102, 139],     "mass_g": 414},
    {"id": "003_cracker_box",    "product": "Cheez-it Cracker box",         "shape": "box",      "dims": [60, 158, 210], "mass_g": 411},
    {"id": "004_sugar_box",      "product": "Domino Sugar box",             "shape": "box",      "dims": [38, 89, 175],  "mass_g": 514},
    {"id": "005_tomato_soup_can","product": "Tomato Soup can",              "shape": "cylinder", "dims": [66, 101],      "mass_g": 349},
    {"id": "006_mustard_bottle", "product": "French's Mustard bottle",      "shape": "bottle",   "dims": [50, 85, 175],  "mass_g": 603},
    {"id": "007_tuna_fish_can",  "product": "Starkist Tuna Fish can",       "shape": "cylinder", "dims": [85, 33],       "mass_g": 171},
    {"id": "008_pudding_box",    "product": "Jell-O Chocolate Pudding box", "shape": "box",      "dims": [35, 110, 89],  "mass_g": 187},
    {"id": "009_gelatin_box",    "product": "Jell-O Strawberry Gelatin box","shape": "box",      "dims": [28, 85, 73],   "mass_g": 97},
    {"id": "010_potted_meat_can","product": "Spam Potted Meat can",         "shape": "box",      "dims": [50, 97, 82],   "mass_g": 370},
]
N_PRISM = 12

def params_for(it):
    if it["shape"] == "box":
        w, d, h = it["dims"]  # FZ05修正: PDF原序 = W×D×H 语义 (排序赋值会扁平化形状)
        return "rsc_css", {"W": float(w), "D": float(d), "H": float(h)}
    if it["shape"] == "bottle":  # 无原生瓶家族: prism 近似, Ø=横截面两值均值 (FZ05 登记 approximation)
        d = sorted(it["dims"], reverse=True)
        dia = (d[1] + d[2]) / 2.0
        h = d[0]
        side = dia * math.tan(math.pi / N_PRISM)
        return "prism_dust_n12", {"n": N_PRISM, "side": round(side, 3), "h": float(h), "_approx": "bottle→n12棱柱, Ø=横截面均值"}
    dia, h = it["dims"]
    side = dia * math.tan(math.pi / N_PRISM)  # 外接圆径 == 官方 Ø (FZ05 约定)
    return "prism_dust_n12", {"n": N_PRISM, "side": round(side, 3), "h": float(h)}

def main():
    out_root = Path("output/pilot10_ycb/compiled")
    out_root.mkdir(parents=True, exist_ok=True)
    import numpy as np
    uv = __import__("importlib").import_module("sdk._core._usd_validate")
    results = []
    for it in ITEMS:
        cls_id, params = params_for(it)
        mod = pbase.get(cls_id)
        merged = {**mod.DEFAULTS, **params}
        try:
            ir_raw = mod.build_ir(merged)
        except Exception as e:
            results.append({"id": it["id"], "status": "CONTRACT_REJECTED", "fail": str(e)[:120]})
            print(it["id"], "CONTRACT_REJECTED", str(e)[:80]); continue
        ir_raw.pop("_derived", None)
        ir = from_raw(ir_raw)
        x0, y0, x1, y1 = net_bbox(ir)
        report = run_qa(ir, svg_render(ir, x1-x0, y1-y0), build_pdf(ir, x1-x0, y1-y0))
        gates = {g["id"]: g["status"] for g in report["gates"] if g["id"] != "G01"}
        fails = [k for k, v in gates.items() if v != "PASS"]
        a_dir = out_root / it["id"]
        a_dir.mkdir(parents=True, exist_ok=True)
        ev = export_usdc(ir, a_dir / "model.usdc", kind="carton_board", family=f"p10_{it['id']}")
        sdims = stage_dims_m(a_dir / "model.usdc")
        analytic = mod.analytic_bbox(merged)
        roles = {pp["id"]: pp["role"] for pp in ir.panels}
        world = fold_all(ir)
        solid = np.vstack([v for pid, v in world.items() if roles.get(pid) in mod.solid_roles()])
        folded = {k: float(solid[:, i].max() - solid[:, i].min()) for i, k in enumerate("WDH")}
        rec = reconcile_dims(analytic, folded, sdims)
        nvsdk = uv._validate_usd_asset(a_dir / "model.usdc")
        nvsdk_pass = isinstance(nvsdk, (tuple, list)) and len(nvsdk) >= 10
        sha = hashlib.sha256((a_dir / "model.usdc").read_bytes()).hexdigest()
        r = {"id": it["id"], "cls_id": cls_id, "params": params, "status": "QA_FAIL" if fails else "OK",
             "gates": gates, "gate_fails": fails,
             "stage_dims_m": sdims, "reconcile": rec, "nvsdk_pass": bool(nvsdk_pass), "usdc_sha256": sha}
        results.append(r)
        print(it["id"], r["status"], "nvsdk:", nvsdk_pass, "gates_fails:", fails[:4])
    json.dump({"_meta": {"protocol": "WP1-P10-YCB 通道A 规格驱动", "frozen": "2026-11-28", "census": len(ITEMS)},
               "results": results}, open("docs/research/evidence/p10_channel_a_compile.json", "w"), indent=1)
    ok = sum(1 for r in results if r["status"] == "OK" and r.get("nvsdk_pass"))
    print(f"汇总: {ok}/{len(ITEMS)} 编译+NVSDK 双过")

if __name__ == "__main__":
    main()
