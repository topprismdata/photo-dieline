"""probe14 — R3-A4 专项: 冲突实测 / 派生重算 / 约束传播 (非 gable 分发已由 probe13(c) 覆盖)。

(a) 锚-观测冲突: 锚值与观测几何矛盾 (Hb/D 偏 +5/-5mm) → 测量层是否浮出冲突?
(b) 锚-域冲突 / 拟合值域冲突: 拟合参数违反模板声明域 (坡角<5°) → 是否交付?
(c) 派生重算: 独立实现关键点几何 (从文档化数学重抄, 防共因失效) + 像素回程 + 派生尺寸独立公式。
(d) 无效锚: 锚键名拼写错误/模型不消费的参数 → 静默接受?
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))
from photo_dieline.measurement import MODELS, observe, solve  # noqa: E402

FX = 50.0 / 36.0 * 768.0
TRUTH = {"W": 45.0, "D": 45.0, "Hb": 100.0, "Hr": 12.0, "Ef": 14.0, "fin_gap_mm": 3.0}


def ccam(az, el, roll, d):
    return {"az": math.radians(az), "el": math.radians(el), "roll": math.radians(roll), "d_eye": d}


CAM = ccam(35, 18, -4, 0.81)


def clean_obs():
    idx, uv, _ = observe(MODELS["gable_top"], TRUTH, CAM, FX)
    return idx, uv


print("=== (a) 锚-观测冲突: 锚与观测几何矛盾, 静默吸收量化 ===")
idx, uv = clean_obs()
for tag, anchors in (("无冲突(对照)", {"Hb": 100.0}),
                     ("Hb 锚错 +5mm", {"Hb": 105.0}),
                     ("D 锚错 -5mm", {"D": 40.0})):
    r = solve(MODELS["gable_top"], idx, uv, FX, anchors, 0.85)
    th = {**r["anchors"], **r["theta"]}
    print(f" {tag:<14} delivery={r['delivery']:<24} W={th['W']:.2f} D={th['D']:.2f} Hr={th['Hr']:.2f} "
          f"rms={r['rms_px']:.3f}px σW={r['sigma_mm']['W']:.2f}")

print("\n=== (b) 拟合参数违反模板声明域 (坡角 atan(2Hr/D) < 5°) ===")
P_ILL = {**TRUTH, "Hr": 1.5}                      # slope = 3.81° < 5°, gable 模板域外
idx_i, uv_i, _ = observe(MODELS["gable_top"], P_ILL, CAM, FX)
r = solve(MODELS["gable_top"], idx_i, uv_i, FX, {"Hb": 100.0}, 0.85, noise_px=0.2)  # 合成干净观测: 声明 0.2px 标注噪声
th = {**r["anchors"], **r["theta"], "fin_gap_mm": 3.0}
slope = math.degrees(math.atan2(2.0 * th["Hr"], th["D"]))
print(f" truth Hr=1.5 → 拟合 Hr={th['Hr']:.2f} 坡角={slope:.2f}° delivery={r['delivery']}")
print(f" rms={r['rms_px']:.3f}px cond_theta={r['cond_theta']:.1f} ident={r['identifiability']} "
      f"distinct_minima={r['n_distinct_minima']} (域声明: <5° 不得交付; 解跑飞到域内高置信错误=更严重)")

print("\n=== (c) 派生重算: 独立实现关键点几何 + 像素回程 + 派生尺寸 ===")


def kp_independent(p):
    """从 gable_keypoints 文档化数学独立重抄 (防共因失效; 捕捉转写/单位/约定漂移, 不防规格本身错)。"""
    W, D, Hb, Hr, Ef, gap = (p[k] for k in ("W", "D", "Hb", "Hr", "Ef", "fin_gap_mm"))
    lean = math.asin(min(1.0, (gap / 2.0) / Ef))
    top = Hb + Hr + Ef * math.cos(lean)
    pts = [(sx * W / 2, y, z) for sx in (-1, 1) for y in (0.0, D) for z in (0.0, Hb)]
    pts += [(-W / 2, D / 2, Hb + Hr), (W / 2, D / 2, Hb + Hr)]
    pts += [(sx * W / 2, D / 2 + sy * Ef * math.sin(lean), top) for sx in (-1, 1) for sy in (-1, 1)]
    return np.array(pts), np.array([0.0, D / 2, top / 2])


r = solve(MODELS["gable_top"], idx, uv, FX, {"Hb": 100.0}, 0.85)
th = {**r["anchors"], **r["theta"], "fin_gap_mm": 3.0}
P_lib, c_lib = MODELS["gable_top"]["kp"](th)
P_ind, c_ind = kp_independent(th)
d_kp = float(np.abs(P_lib - P_ind).max())
d_c = float(np.abs(c_lib - c_ind).max())
lean = math.asin(min(1.0, (th["fin_gap_mm"] / 2.0) / th["Ef"]))
top = th["Hb"] + th["Hr"] + th["Ef"] * math.cos(lean)
y_tot = th["D"] + 2.0 * th["Ef"] * math.sin(lean)
print(f" 关键点独立实现 vs 库: max|ΔP|={d_kp:.2e}mm max|Δc|={d_c:.2e}mm")
print(f" 派生尺寸 (独立公式): 总高 Z_top={top:.3f}mm 含鳍 Y_total={y_tot:.3f}mm (lean={math.degrees(lean):.2f}°)")

# 像素回程: 独立 kp + 解出的位姿 → 重投影, 与干净观测比
from photo_dieline.measurement import eye_pos, project, to_world  # noqa: E402

Pw = to_world(P_ind, c_ind)
cam = r["cam"]
eye = eye_pos(np.array(cam["T"]), cam["az"], cam["el"], cam["d_eye"])
uv_rt = project(Pw[idx], eye, cam["az"], cam["el"], cam["roll"], FX * cam["fx_scale"])
err = float(np.abs(uv_rt - uv).max())
print(f" 像素回程 (独立几何+解位姿 → 重投影 vs 观测): max|Δuv|={err:.2e}px")

print("\n=== (d) 无效锚: 模型不消费的参数 / 键名拼错 ===")
for tag, anchors in (("未注册参数 H", {"H": 120.0}), ("键名拼错 Ww", {"Ww": 45.0})):
    try:
        r = solve(MODELS["gable_top"], idx, uv, FX, anchors, 0.85)
        print(f" {tag:<12} → ok={r.get('ok')} delivery={r.get('delivery')} reason={r.get('reason')} (静默接受=缺陷)")
    except Exception as exc:
        print(f" {tag:<12} → 异常: {type(exc).__name__}: {exc}")

print("\nPROBE14_DONE")
