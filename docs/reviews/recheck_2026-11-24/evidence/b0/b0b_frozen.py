"""B0-B 冻结矩阵执行器 (协议: docs/reviews/recheck_2026-11-24/evidence/b0/b0b_frozen_protocol.md)。
种子组级: sha1("B0B|group|variant|rep") — 同组各条件共享噪声底 (配对观测)。
d0 策略: 首视角真值 d_eye × 1.1 (确定性起点提示, 无额外随机源; 协议未冻结项, 如实入 findings)。
"""
import hashlib
import json
import math
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, "/Users/guohongbin/photo-dieline/src")
from photo_dieline.measurement import MODELS, observe, solve

RES = 768
FX = 50.0 / 36.0 * RES
TOL_MM = 1.0
REPS = 5
GAB, CUB = MODELS["gable_top"], MODELS["cuboid"]
FREE_DIMS = {"gable_top": ("W", "D", "Hr", "Ef"), "cuboid": ("W", "D", "H")}

GABLE_VARS = {
    "g_regular": {"W": 45.0, "D": 45.0, "Hb": 100.0, "Hr": 12.0, "Ef": 14.0, "fin_gap_mm": 3.0},
    "g_wide": {"W": 60.0, "D": 28.0, "Hb": 90.0, "Hr": 10.0, "Ef": 12.0, "fin_gap_mm": 3.0},
    "g_tall": {"W": 32.0, "D": 32.0, "Hb": 160.0, "Hr": 14.0, "Ef": 16.0, "fin_gap_mm": 3.0},
    "g_deep": {"W": 50.0, "D": 70.0, "Hb": 80.0, "Hr": 9.0, "Ef": 11.0, "fin_gap_mm": 3.0},
}
CUB_VARS = {
    "c_regular": {"W": 80.0, "D": 50.0, "H": 120.0},
    "c_extreme": {"W": 100.0, "D": 25.0, "H": 80.0},
}
ALL_VARS = dict(GABLE_VARS, **CUB_VARS)

def cam(az, el, roll, d):
    return {"az": math.radians(az), "el": math.radians(el), "roll": math.radians(roll), "d_eye": d}

V_TQ = cam(35, 18, -4, 0.81)
V_FRONT = cam(0, 2, 0, 0.90)
V_NEAR = cam(8, 6, -2, 0.85)
V3_COMP = [cam(35, 18, -4, 0.81), cam(140, 10, 3, 0.75), cam(270, 30, 0, 0.90)]
V3_DUP = [cam(30, 16, -3, 0.80), cam(40, 20, -5, 0.82), cam(35, 14, -2, 0.79)]
VIEW_SPECS = {"1tq": [V_TQ], "front": [V_FRONT], "near": [V_NEAR], "tq": [V_TQ],
              "v3comp": V3_COMP, "v3dup": V3_DUP}

def seed_rng(group, variant, rep):
    h = hashlib.sha1(("B0B|%s|%s|%d" % (group, variant, rep)).encode()).hexdigest()
    return np.random.default_rng(int(h[:16], 16))

def add_noise(model_key, idx, uv, rng, noise):
    if noise == "iid":
        return uv + rng.normal(0, 1.0, uv.shape)
    if noise.startswith("bias"):
        m = float(noise[4:])
        c = uv.mean(0)
        d = c - uv
        d = d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9)
        return uv + d * m + rng.normal(0, 0.3, uv.shape)
    if noise == "corr":
        groups = ([0, 1, 4, 5], [2, 3, 6, 7], [8, 9, 10, 11, 12, 13]) if model_key == "gable_top" else ([0, 1, 4, 5], [2, 3, 6, 7])
        pos = {int(k): i for i, k in enumerate(idx)}
        out = uv + rng.normal(0, 0.5, uv.shape)
        for g in groups:
            rows = [pos[k] for k in g if k in pos]
            if rows:
                out[rows] += rng.normal(0, 2.0, 2)
        return out
    if noise == "miscorr":
        pos = {int(k): i for i, k in enumerate(idx)}
        out = uv + rng.normal(0, 0.3, uv.shape)
        if 10 in pos and 11 in pos:
            out[[pos[10], pos[11]]] = out[[pos[11], pos[10]]]
        return out
    raise ValueError(noise)

def make_views(model_key, P, view_list, rng, noise="iid", render_fx=1.0, drop=(), swap=None):
    model = MODELS[model_key]
    obs = []
    fxr = FX * render_fx
    for c in view_list:
        idx, uv, _ = observe(model, P, c, fxr)
        uv = add_noise(model_key, idx, uv, rng, noise)
        if swap:
            pos = {int(k): i for i, k in enumerate(idx)}
            a, b = swap
            if a in pos and b in pos:
                uv[[pos[a], pos[b]]] = uv[[pos[b], pos[a]]]
        keep = [i for i, k in enumerate(idx) if int(k) not in set(drop)]
        obs.append((idx[keep], uv[keep], FX))
    return obs

def run_cell(c):
    mk, P = c["model"], ALL_VARS[c["variant"]]
    rng = seed_rng(c["group"], c["variant"], c["rep"])
    obs = make_views(mk, P, VIEW_SPECS[c["views"]], rng, noise=c["noise"],
                     render_fx=c.get("render_fx", 1.0), drop=c.get("drop", ()), swap=c.get("swap"))
    anchors = {}
    if c["anchor"] == "one_edge":
        anchors = {"Hb": P["Hb"]} if mk == "gable_top" else {"H": P["H"]}
    d0 = VIEW_SPECS[c["views"]][0]["d_eye"] * 1.1
    f = FX * c.get("fx_factor", 1.0)
    row = {"group": c["group"], "cond": c["cond"], "model": mk, "variant": c["variant"],
           "rep": c["rep"], "anchor": c["anchor"], "noise": c["noise"], "views": c["views"],
           "n_pts": int(len(obs[0][0])), "n_views": len(obs)}
    try:
        r = solve(MODELS[mk], obs[0][0], obs[0][1], f, anchors, d0,
                  extra_views=[(o[0], o[1], f) for o in obs[1:]], free_fx=c.get("free_fx", False))
    except Exception as exc:
        row["status"] = "solver_exc:%s" % exc
        return row
    if not r.get("ok"):
        row["status"] = "solver_fail:" + str(r.get("reason"))
        return row
    th = {**r["anchors"], **r["theta"]}
    for k in FREE_DIMS[mk]:
        row["err_" + k] = float(abs(th[k] - P[k]))
        row["sigma_" + k] = float(r["sigma_mm"].get(k, float("nan")))
    row.update({"delivery": r["delivery"], "ident": r["identifiability"], "scale_source": r["scale_source"],
                "rms_px": float(r["rms_px"]), "n_min": int(r["n_distinct_minima"]),
                "cond_theta": float(r["cond_theta"]) if math.isfinite(r["cond_theta"]) else 1e30,
                "s_hat": float(r["cam"]["fx_scale"]), "status": "done"})
    row["alarm"] = bool(row["delivery"] != "MANUFACTURING_DIMENSIONS" or row["rms_px"] > 3.0 or row["n_min"] >= 2)
    row["over_tol"] = bool(row["err_W"] > TOL_MM or row["err_D"] > TOL_MM)
    return row

def build_cells():
    cells = []
    # B01 尺度先验
    for v in GABLE_VARS:
        for anchor in ("none", "one_edge"):
            cells.append(dict(group="B01", cond="b01_%s" % anchor, model="gable_top", variant=v,
                              anchor=anchor, views="tq", noise="iid"))
        for gap in (2.5, 3.5):
            cells.append(dict(group="B01", cond="b01_prior_gap%.1f" % gap, model="gable_top", variant=v,
                              anchor="none", views="tq", noise="iid", params_gap=gap))
    for v in CUB_VARS:
        for anchor in ("none", "one_edge"):
            cells.append(dict(group="B01", cond="b01cub_%s" % anchor, model="cuboid", variant=v,
                              anchor=anchor, views="tq", noise="iid"))
    # B02 观测退化
    for views in ("front", "near", "tq"):
        for anchor in ("none", "one_edge"):
            for v in ALL_VARS:
                cells.append(dict(group="B02", cond="b02_%s_%s" % (views, anchor),
                                  model="cuboid" if v.startswith("c_") else "gable_top",
                                  variant=v, anchor=anchor, views=views, noise="iid"))
    # B03 噪声结构 (gable, one_edge)
    for noise in ("iid", "bias0.5", "bias1.0", "bias2.0", "corr", "miscorr"):
        for v in GABLE_VARS:
            cells.append(dict(group="B03", cond="b03_%s" % noise, model="gable_top", variant=v,
                              anchor="one_edge", views="tq", noise=noise))
    for v in GABLE_VARS:
        cells.append(dict(group="B03", cond="b03_misspts", model="gable_top", variant=v,
                          anchor="one_edge", views="tq", noise="iid", drop=(8, 9)))
    # B04 内参 (配对) + 部分未知
    for fx_factor in (0.95, 0.98, 1.02, 1.05):
        for v in ALL_VARS:
            mk = "cuboid" if v.startswith("c_") else "gable_top"
            cells.append(dict(group="B04", cond="b04_fx%.2f" % fx_factor, model=mk, variant=v,
                              anchor="one_edge", views="tq", noise="iid", fx_factor=fx_factor))
    for render_fx in (0.97, 1.05):
        for v in ALL_VARS:
            mk = "cuboid" if v.startswith("c_") else "gable_top"
            cells.append(dict(group="B04", cond="b04_freep%.2f" % render_fx, model=mk, variant=v,
                              anchor="one_edge", views="tq", noise="iid", render_fx=render_fx, free_fx=True))
    # B05 视角数量
    for views in ("1tq", "v3comp", "v3dup"):
        for anchor in ("none", "one_edge"):
            for v in ALL_VARS:
                mk = "cuboid" if v.startswith("c_") else "gable_top"
                cells.append(dict(group="B05", cond="b05_%s_%s" % (views, anchor), model=mk, variant=v,
                                  anchor=anchor, views=views, noise="iid"))
    # B06 组合压力
    for anchor in ("none", "one_edge"):
        for v in ALL_VARS:
            mk = "cuboid" if v.startswith("c_") else "gable_top"
            cells.append(dict(group="B06", cond="b06_%s" % anchor, model=mk, variant=v,
                              anchor=anchor, views="v3dup", noise="corr", render_fx=1.05, free_fx=True))
    # 展开 rep
    out = []
    for c in cells:
        for rep in range(REPS):
            cc = dict(c)
            cc["rep"] = rep
            if "params_gap" in cc:
                cc = dict(cc)
                out.append(("gap", cc))
            else:
                out.append(("", cc))
    # gap 变体参数在 run_cell 里取 ALL_VARS — 需要覆盖: 直接改 params 不方便, 换成 variant 专用键
    final = []
    for _, cc in out:
        if "params_gap" in cc:
            cc = dict(cc)
            cc["gap_override"] = cc.pop("params_gap")
        final.append(cc)
    return final

# gap_override 支持: run_cell 里读
_orig_run_cell = run_cell
def run_cell(c):  # noqa: F811
    if "gap_override" in c:
        import photo_dieline.measurement as _m
        # ALL_VARS 不可变共享 — 在本 worker 进程内安全覆盖后再还原
        key = c["variant"]
        old = dict(ALL_VARS[key])
        ALL_VARS[key] = {**old, "fin_gap_mm": c["gap_override"]}
        try:
            return _orig_run_cell({k: v for k, v in c.items() if k != "gap_override"})
        finally:
            ALL_VARS[key] = old
    return _orig_run_cell(c)

def agg(rows):
    acc = [r for r in rows if r.get("delivery") == "MANUFACTURING_DIMENSIONS"]
    out = {"n": len(rows), "n_acc": len(acc), "alarm_rate": float(np.mean([r.get("alarm", True) for r in rows])) if rows else None}
    if acc:
        for k in ("W", "D"):
            errs = np.array([r["err_" + k] for r in acc])
            out["mae_" + k] = float(errs.mean())
            out["p95_" + k] = float(np.percentile(errs, 95))
            out["max_" + k] = float(errs.max())
        out["over_tol"] = float(np.mean([r["over_tol"] for r in acc]))
        tot = cov = 0
        for r in acc:
            for k in FREE_DIMS[r["model"]]:
                s, e = r["sigma_" + k], r["err_" + k]
                if math.isfinite(s):
                    tot += 1
                    cov += e <= 2 * s
        out["sig2_cov"] = float(cov / tot) if tot else None
    return out

if __name__ == "__main__":
    cells = build_cells()
    print("cells=%d (含 rep)" % len(cells), flush=True)
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=6) as ex:
        for i, row in enumerate(ex.map(run_cell, cells, chunksize=4)):
            rows.append(row)
            if (i + 1) % 100 == 0:
                print("%4d/%d %.0fs" % (i + 1, len(cells), time.time() - t0), flush=True)
    print("done %.0fs" % (time.time() - t0), flush=True)

    json.dump(rows, open("/tmp/pd_recheck/b0/b0b_frozen_rows.json", "w"), indent=0)

    # 汇总
    summary = {}
    for grp in ("B01", "B02", "B03", "B04", "B05", "B06"):
        conds = sorted({r["cond"] for r in rows if r["group"] == grp})
        for cond in conds:
            summary["%s/%s" % (grp, cond)] = agg([r for r in rows if r["cond"] == cond])

    # 不可辨识召回 (预期退化格) / 误拒率 (合法格)
    deg = [r for r in rows if r["cond"] in ("b02_front_none", "b02_near_none", "b06_none")]
    summary["_recall_degenerate"] = float(np.mean([r.get("delivery") == "REFUSED" or r.get("ident") in ("WEAK", "UNIDENTIFIABLE") for r in deg]))
    valid = [r for r in rows if r["anchor"] == "one_edge" and r["noise"] in ("iid",) and r["views"] in ("tq", "v3comp") and "b04" not in r["cond"]]
    summary["_false_refusal"] = float(np.mean([r.get("delivery") != "MANUFACTURING_DIMENSIONS" for r in valid]))
    # 高置信错误 (B06): 未报警且超容差
    b6 = [r for r in rows if r["group"] == "B06"]
    summary["_b06_silent_wrong"] = int(sum(1 for r in b6 if not r.get("alarm", True) and r.get("over_tol")))

    # 风险-覆盖率曲线 (one_edge 池)
    pool = [r for r in rows if r["anchor"] == "one_edge" and r.get("status") == "done" and math.isfinite(r["sigma_W"])]
    sig = np.array([r["sigma_W"] for r in pool])
    curve = []
    for q in range(0, 101, 10):
        tau = float(np.percentile(sig, q))
        acc = [r for r in pool if r["delivery"] == "MANUFACTURING_DIMENSIONS" and r["sigma_W"] <= tau]
        cov = len(acc) / len(pool)
        risk = float(np.mean([r["over_tol"] for r in acc])) if acc else 0.0
        curve.append({"tau": tau, "coverage": cov, "risk_over_tol": risk})
    summary["_risk_coverage"] = curve

    meta = {"solver_commit": subprocess.run(["git", "-C", "/Users/guohongbin/photo-dieline", "rev-parse", "--short", "HEAD"],
                                            capture_output=True, text=True).stdout.strip(),
            "protocol": "evidence/b0/b0b_frozen_protocol.md", "reps": REPS, "tol_mm": TOL_MM, "fx": FX,
            "d0_policy": "first-view true d_eye x 1.1 (deterministic)"}
    json.dump({"meta": meta, "summary": summary}, open("/tmp/pd_recheck/b0/b0b_frozen_summary.json", "w"), indent=1)

    print("\n=== B0-B 冻结矩阵汇总 (节选) ===")
    for key, s in summary.items():
        if key.startswith("_"):
            print("%-24s %s" % (key, json.dumps(s) if not isinstance(s, list) else "curve[%d]" % len(s)))
        elif s["n_acc"]:
            print("%-24s n=%3d acc=%3d maeW=%6.2f p95W=%6.2f overTol=%4.2f sig2cov=%s alarm=%.2f" % (
                key, s["n"], s["n_acc"], s["mae_W"], s["p95_W"], s["over_tol"],
                ("%.2f" % s["sig2_cov"]) if s.get("sig2_cov") is not None else "-", s["alarm_rate"]))
        else:
            print("%-24s n=%3d acc=  0 (全部拒绝/弱) alarm=%.2f" % (key, s["n"], s["alarm_rate"]))
    print("B0B_FROZEN_DONE")
