"""B0-B 多视角与内参扰动 (R2 §6.4 冻结矩阵的"视角数量 1/3/6" + "带扰动内参" 维度; 单变量首轮)。
核心问题: 无锚点时多视角能否恢复尺度可辨识 (尺度跨视角共享、距离逐视角独立 → 简并消失)?
条件: 6 个留出变体 × 视角数 {1,3,6} × 尺度信息 {无锚点, 一条实测边} × 内参 {已知, ±10% 扰动}, σ=1px。
"""
import json
import math
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, "/tmp/pd_recheck")
from b0_solver import MODELS, observe, solve_multi, ratio_mae  # noqa: E402

B0 = "/tmp/pd_recheck/b0"
RES = 768
rng = np.random.default_rng(20261225)

views_all = json.load(open(f"{B0}/views.json"))
by_variant = defaultdict(list)
for v in views_all:
    by_variant[v["sid"].rsplit("_", 1)[0]].append(v)
variants = sorted(by_variant)[:6]          # v16, v18, v23, v25, v28, v29
MODEL = MODELS["gable_top"]

rows = []
for vi, var in enumerate(variants):
    frames = by_variant[var]
    truth = dict(frames[0]["params"])
    for n_views in (1, 3, 6):
        # 确定性抽视角 (帧序均匀取样)
        step = max(1, len(frames) // n_views)
        picked = [frames[(i * step) % len(frames)] for i in range(n_views)]
        obs = []
        for fr in picked:
            cam = fr["camera"]
            c = {"az": math.radians(cam["yaw_deg"]), "el": math.radians(cam["pitch_deg"]),
                 "roll": math.radians(cam["roll_deg"]), "d_eye": fr["distance_m_eff"] * 1.35}
            fx_true = cam["equiv_focal_mm"] / 36.0 * RES
            idx, uv, _ = observe(MODEL, truth, c, fx_true)
            if len(idx) < 6:
                break
            uv = uv + rng.normal(0, 1.0, uv.shape)
            fx_used = fx_true * float(rng.uniform(0.9, 1.1))     # 内参 ±10% 扰动 (求解用错内参)
            obs.append((idx, uv, fx_used))
        if len(obs) != n_views:
            rows.append({"variant": var, "n_views": n_views, "status": "too_few_points"})
            continue
        d0 = picked[0]["distance_m_eff"] * 1.35 * float(rng.uniform(0.8, 1.25))
        for mode, anchors in (("none", {}), ("one_edge", {"Hb": truth["Hb"]})):
            res = solve_multi(MODEL, obs, anchors, d0)
            rec = {"variant": var, "n_views": n_views, "mode": mode, "fx": "perturbed"}
            if not res.get("ok"):
                rec["status"] = "solver_failed"
            else:
                th = {**anchors, **res["theta"]}
                rec.update({"status": "accepted" if res["identifiable"] else "unidentifiable",
                            "ratio_mae": ratio_mae(MODEL, th, truth),
                            "err_mm": {t: abs(th[t] - truth[t]) for t in ("W", "D", "Hr", "Ef")},
                            "rms_px": res["rms_px"], "cond_theta": res["cond_theta"]})
            rows.append(rec)
            print("B0B %s views=%d %s %s" % (var, n_views, mode, rec.get("status")), flush=True)

print("\n=== B0-B 汇总 (σ=1px, 内参 ±10% 扰动; 6 留出变体) ===")
print("%-6s %5s %9s %7s %9s %9s | %s" % ("视角", "锚点", "可辨识", "比例MAE", "W误差mm", "D误差mm", "条件数中位"))
summary = {}
for n_views in (1, 3, 6):
    for mode in ("none", "one_edge"):
        rs = [r for r in rows if r.get("n_views") == n_views and r.get("mode") == mode and r.get("status") in ("accepted", "unidentifiable")]
        acc = [r for r in rs if r["status"] == "accepted"]
        if acc:
            m = float(np.mean([r["ratio_mae"] for r in acc]))
            w = float(np.mean([r["err_mm"]["W"] for r in acc]))
            d = float(np.mean([r["err_mm"]["D"] for r in acc]))
            ct = float(np.median([r["cond_theta"] for r in acc]))
            summary["%dv_%s" % (n_views, mode)] = {"n": len(rs), "identifiable": len(acc), "ratio_mae": m, "w_err": w, "d_err": d, "cond_median": ct}
            print("%-6d %5s %9s %7.4f %9.2f %9.2f | %.1e" % (n_views, mode, "%d/%d" % (len(acc), len(rs)), m, w, d, ct))
        else:
            summary["%dv_%s" % (n_views, mode)] = {"n": len(rs), "identifiable": 0}
            print("%-6d %5s %9s %7s %9s %9s | 全部不可辨识" % (n_views, mode, "0/%d" % len(rs), "-", "-", "-"))
json.dump({"rows": rows, "summary": summary}, open(f"{B0}/b0b_rows.json", "w"), indent=1)
print("B0B_DONE")
