"""E3: gable_top closure_checks 哪些判据对 tdir 扰动敏感 (恒真探针)."""
import copy, numpy as np
from photo_dieline.core.ir import from_raw
from photo_dieline.folding.engine import fold_all
from photo_dieline.parametric import gable_top

base = gable_top.build_ir(None)
names = list(gable_top.closure_checks(from_raw(copy.deepcopy(base)), fold_all(from_raw(copy.deepcopy(base)))).keys())
print("closure criteria:", len(names))
hdr = "mutation".ljust(34) + "".join(f"{i:>3d}" for i in range(len(names))) + "   worst"
print(hdr)
for i, n in enumerate(names):
    print(f"  [{i}] {n}")

def row(label, mut):
    raw = copy.deepcopy(base); mut(raw)
    try:
        ir = from_raw(raw); res = gable_top.closure_checks(ir, fold_all(ir))
    except Exception as exc:
        print(label.ljust(34) + "  EXC " + type(exc).__name__ + ": " + str(exc)[:90]); return
    vals = [res[n] for n in names]
    flag = "".join("  #" if v > 0.2 else "  ." for v in vals)
    print(label.ljust(34) + flag + f"   {max(vals):.4f}")

def set_tdir(eid, v):
    def m(raw):
        for e in raw["edges"]:
            if e["id"] == eid: e["fold"]["target_dir_3d"] = list(v)
    return m
def set_poly(pid, idx, pt):
    def m(raw):
        for p in raw["panels"]:
            if p["id"] == pid: p["polygon_2d"][idx] = list(pt)
    return m

row("baseline (no mutation)", lambda r: None)
print("-- 单边 tdir 扰动 --")
row("e_glue tdir -> (-1,0,0) [粘口折向盒外]", set_tdir("e_glue", (-1, 0, 0)))
row("e_wl_bk tdir -> (0,-1,0)", set_tdir("e_wl_bk", (0, -1, 0)))
row("e_bk_wr tdir -> (0,1,0)", set_tdir("e_bk_wr", (0, 1, 0)))
row("e_wr_ft tdir -> (0,-1,0)", set_tdir("e_wr_ft", (0, -1, 0)))
row("e_bk_sl tdir -> (0,0,1) [坡面竖直]", set_tdir("e_bk_sl", (0, 0, 1)))
row("e_ft_sl tdir -> (0,0,1) [坡面竖直]", set_tdir("e_ft_sl", (0, 0, 1)))
row("e_sl_fb tdir -> (0,0,1)", set_tdir("e_sl_fb", (0, 0, 1)))
row("e_sl_fb tdir -> (0,-1,0) [鳍倒伏]", set_tdir("e_sl_fb", (0, -1, 0)))
row("e_sl_fb == e_sl_ff tdir [两鳍重合]", set_tdir("e_sl_fb", (0, 0.107, 0.994)))
row("e_ft_fl tdir -> (0,0,-1) [底板下垂]", set_tdir("e_ft_fl", (0, 0, -1)))
row("e_bk_fl tdir -> (0,0,-1)", set_tdir("e_bk_fl", (0, 0, -1)))
row("e_wl_fl tdir -> (0,0,-1)", set_tdir("e_wl_fl", (0, 0, -1)))
row("e_wr_fl tdir -> (0,0,-1)", set_tdir("e_wr_fl", (0, 0, -1)))
print("-- 2D 轮廓扰动 --")
# flapF 高度 D -> D/2 (真实工艺常见: 前翻板半深)
row("flapF 高 D -> D/2", lambda r: [p["polygon_2d"].__setitem__(i, [x, y/2]) for p in r["panels"] if p["id"]=="flapF" for i,(x,y) in enumerate(list(p["polygon_2d"])) if y < 0])
row("flapB 高 D -> D/2", lambda r: [p["polygon_2d"].__setitem__(i, [x, y/2]) for p in r["panels"] if p["id"]=="flapB" for i,(x,y) in enumerate(list(p["polygon_2d"])) if y < 0])
row("flapL 高 W/2 -> W", lambda r: [p["polygon_2d"].__setitem__(i, [x, y*2]) for p in r["panels"] if p["id"]=="flapL" for i,(x,y) in enumerate(list(p["polygon_2d"])) if y < 0])
row("glue 宽 gw -> gw/2", lambda r: [p["polygon_2d"].__setitem__(i, [x/2, y]) for p in r["panels"] if p["id"]=="glue" for i,(x,y) in enumerate(list(p["polygon_2d"])) if x == 0.0])
