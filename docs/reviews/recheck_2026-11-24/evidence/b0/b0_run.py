"""B0 实验矩阵 (GPT R2 §6.4 的首轮单变量版):
族 = gable_top (120 帧真实渲染的相机参数) + cuboid (解析生成 120 组);
尺度信息 = 无锚点 / 一条实测边 / 两条实测边; 关键点噪声 σ ∈ {0, 0.25, 0.5, 1, 2, 4} px; 单视角; 多起点。
评价: 参数误差 (mm)、比例 MAE (与 CNN 同口径)、重投影 RMS、可辨识性 (参数子空间 Schur 补)、多解数、失败数。
每帧独立随机种子 (2026 + 帧序号), 按帧多进程并行, 结果与进程数无关。用法: python3 b0_run.py
"""
import json
import math
import multiprocessing as mp
import sys

import numpy as np

sys.path.insert(0, "/tmp/pd_recheck")
from b0_solver import MODELS, observe, solve, ratio_mae  # noqa: E402

B0 = "/tmp/pd_recheck/b0"
SIGMAS = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0)
MODES = ("none", "one_edge", "two_edges")
ANCHORS = {"gable_top": {"none": [], "one_edge": ["Hb"], "two_edges": ["Hb", "W"]},
           "cuboid": {"none": [], "one_edge": ["H"], "two_edges": ["H", "W"]}}


def gable_frames():
    out = []
    for v in json.load(open(f"{B0}/views.json")):
        cam = v["camera"]
        out.append({"sid": v["sid"], "p": dict(v["params"]),
                    "cam": {"az": math.radians(cam["yaw_deg"]), "el": math.radians(cam["pitch_deg"]),
                            "roll": math.radians(cam["roll_deg"]), "d_eye": v["distance_m_eff"] * 1.35},
                    "fx": cam["equiv_focal_mm"] / 36.0 * 768.0})
    return out


def cuboid_frames(n=120):
    rng = np.random.default_rng(20261124)
    out = []
    for k in range(n):
        p = {"W": float(rng.uniform(30, 120)), "D": float(rng.uniform(30, 120)), "H": float(rng.uniform(40, 260))}
        focal = float(rng.choice([24, 28, 35, 50, 65, 70]))
        r = float(np.linalg.norm([p["W"], p["D"], p["H"]]) / 2000.0)
        out.append({"sid": f"cube_{k:03d}", "p": p,
                    "cam": {"az": float(rng.uniform(-math.pi, math.pi)), "el": math.radians(float(rng.uniform(5, 60))),
                            "roll": math.radians(float(rng.normal(0, 3))),
                            "d_eye": r / (float(rng.uniform(0.55, 0.8)) * 18.0 / focal)},
                    "fx": focal / 36.0 * 768.0})
    return out


def run_frame(job):
    kind, seed, fr = job
    model = MODELS[kind]
    target = model["target"]
    rng = np.random.default_rng(2026 + seed)
    idx, uv, _eye = observe(model, fr["p"], fr["cam"], fr["fx"])
    if len(idx) < 6:
        return [{"kind": kind, "sid": fr["sid"], "mode": "too_few_points", "n_visible": int(len(idx))}]
    d0 = fr["cam"]["d_eye"] * float(rng.uniform(0.8, 1.25))       # 初始化: 粗略的距离估计 (不知道真值)
    truth = dict(fr["p"])
    rows = []
    for mode in MODES:
        anchors = {n: truth[n] for n in ANCHORS[kind][mode]}
        for sig in SIGMAS:
            uv_obs = uv + rng.normal(0, sig, uv.shape)
            try:
                res = solve(model, idx, uv_obs, fr["fx"], anchors, d0)
            except Exception as e:  # 求解器自身异常也计入失败, 不吞掉
                res = {"ok": False, "reason": "exception:%s" % type(e).__name__}
            rec = {"kind": kind, "sid": fr["sid"], "mode": mode, "sigma": sig, "n_visible": int(len(idx))}
            if not res.get("ok"):
                rec.update({"status": "solver_failed", "reason": res.get("reason", "")})
            else:
                th = {**anchors, **res["theta"]}
                err = {t: abs(th[t] - truth[t]) for t in target}
                accept = res["rms_px"] <= max(3 * sig, 0.5) and res["identifiable"]
                rec.update({"status": "accepted" if accept else ("ill_conditioned" if not res["identifiable"] else "high_reproj"),
                            "err_mm": err, "ratio_mae": ratio_mae(model, th, truth), "rms_px": res["rms_px"],
                            "cond": res["cond"], "cond_theta": res["cond_theta"], "n_distinct_minima": res["n_distinct_minima"],
                            "scale_err": {t: (th[t] / truth[t] - 1.0) for t in target}})
            rows.append(rec)
    return rows


def summarize(rows, target, label):
    print("\n=== %s ===" % label)
    print("%-10s %5s %5s %5s %9s %9s | %s | %s" % ("尺度信息", "σpx", "样本", "接受", "比例MAE", "p90", " ".join("%s误差mm" % t for t in target), "多解/帧 不可辨识 重投影超标"))
    out = {}
    for mode in MODES:
        for sig in SIGMAS:
            rs = [r for r in rows if r.get("mode") == mode and r.get("sigma") == sig]
            if not rs:
                continue
            ok = [r for r in rs if r["status"] == "accepted"]
            ill = sum(1 for r in rs if r["status"] == "ill_conditioned")
            hr = sum(1 for r in rs if r["status"] == "high_reproj")
            sf = sum(1 for r in rs if r["status"] == "solver_failed")
            key = (mode, sig)
            if ok:
                m = float(np.mean([r["ratio_mae"] for r in ok]))
                p90 = float(np.percentile([r["ratio_mae"] for r in ok], 90))
                errs = [float(np.mean([r["err_mm"][t] for r in ok])) for t in target]
                multi = float(np.mean([r["n_distinct_minima"] for r in ok]))
                med_ct = float(np.median([r["cond_theta"] for r in ok]))
                out[key] = {"n": len(rs), "accepted": len(ok), "ill_conditioned": ill, "high_reproj": hr, "solver_failed": sf,
                            "ratio_mae": m, "ratio_mae_p90": p90, "err_mm_mean": dict(zip(target, errs)),
                            "distinct_minima_per_frame": multi, "cond_theta_median": med_ct}
                print("%-10s %5.2f %5d %5d %9.5f %9.5f | %s | %6.2f  %8d %8d  (参数条件数中位 %.1e)" % (
                    mode, sig, len(rs), len(ok), m, p90, " ".join("%9.3f" % e for e in errs), multi, ill, hr, med_ct))
            else:
                out[key] = {"n": len(rs), "accepted": 0, "ill_conditioned": ill, "high_reproj": hr, "solver_failed": sf}
                sc = [np.mean([abs(r["scale_err"][t]) for t in target]) for r in rs if "scale_err" in r]
                print("%-10s %5.2f %5d %5d %9s %9s | 全部不可接受: 不可辨识 %d, 重投影超标 %d, 求解失败 %d; 其中相对尺度偏差均值 %s" % (
                    mode, sig, len(rs), 0, "-", "-", ill, hr, sf, ("%.1f%%" % (100 * float(np.mean(sc)))) if sc else "-"))
    return out


if __name__ == "__main__":
    nproc = max(1, min(mp.cpu_count() - 2, 12))
    jobs = [("cuboid", i, fr) for i, fr in enumerate(cuboid_frames())]
    jobs += [("gable_top", 1000 + i, fr) for i, fr in enumerate(gable_frames())]
    rows = []
    with mp.Pool(nproc) as pool:
        for i, rs in enumerate(pool.imap_unordered(run_frame, jobs)):
            rows.extend(rs)
            if (i + 1) % 20 == 0:
                print("B0RUN 进度 %d/%d" % (i + 1, len(jobs)), flush=True)
    json.dump(rows, open(f"{B0}/b0_rows.json", "w"))
    rc = [r for r in rows if r["kind"] == "cuboid"]
    rg = [r for r in rows if r["kind"] == "gable_top"]
    sum_c = summarize(rc, ("W", "D", "H"), "B0 长方体 (解析关键点, 120 组随机尺寸/视角; %d 进程)" % nproc)
    sum_g = summarize(rg, ("W", "D", "Hr", "Ef"), "B0 gable_top (120 帧真实渲染的相机参数; 投影模型已与 Blender 对账)")
    tf = [r for r in rows if r.get("mode") == "too_few_points"]
    print("\n可见关键点不足 6 个而跳过的帧: %d" % len(tf))
    json.dump({"nproc": nproc, "skipped_frames": len(tf),
               "cuboid": {"%s|%.2f" % k: v for k, v in sum_c.items()}, "gable": {"%s|%.2f" % k: v for k, v in sum_g.items()}},
              open(f"{B0}/b0_summary.json", "w"), indent=1)
    print("B0RUN_DONE")
