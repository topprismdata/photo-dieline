"""批量刚体动力学体检 (Gemini 复判 P0 第一梯队):
nv960 域全量 (20 正典 + 60 参数变体) — 50cm 自由落体 + 300 步静置。

统计契约 (fail-closed): 最大穿透 (mm, 分位数) / 静置残余 |v| (mm/s) 与 |ω| (rad/s)
/ 爆炸率 / 质量合法性。把 sim-ready 从 2 个特例升级为域级 80/80 统计判决。
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from photo_dieline.authoring.validate_parts import load_family, validate_parts

import mujoco
import numpy as np

OUT = Path("output/mujoco_downstream/batch")
(OUT / "meshes").mkdir(parents=True, exist_ok=True)
DROP_H = 0.5
SETTLE = 300

_DENSITY = {"steel": 7850.0, "alu": 2700.0, "pp": 905.0, "paper": 700.0,
            "kraft": 700.0, "white": 700.0, "label": 800.0, "hdpe": 950.0,
            "pet": 1380.0, "glass": 2500.0}


def _density(mid):
    for k, v in _DENSITY.items():
        if k in mid:
            return v
    return 1000.0


def _obj_text(part):
    lines = ["o g"]
    lines += [f"v {x*1e-3:.6f} {y*1e-3:.6f} {z*1e-3:.6f}" for (x, y, z) in part["verts_mm"]]
    lines += [f"f {a+1} {b+1} {c+1}" for (a, b, c) in part["tris"]]
    return "\n".join(lines)


def rigid_drop_mjcf(parts, name):
    """全部件合并为单刚体 (刚体资产动力学等价), freejoint 落体。"""
    meshes = []
    geoms = []
    for i, p in enumerate(parts):
        f = OUT / "meshes" / f"{name}_{i}.obj"
        f.write_text(_obj_text(p))
        rel = f.relative_to(OUT)
        meshes.append(f'<mesh name="{name}_{i}" file="{rel}"/>')
        geoms.append(f'<geom name="{name}_{i}" type="mesh" mesh="{name}_{i}" '
                     f'density="{_density(p["material_id"])}" '
                     f'contype="1" conaffinity="1" solref="0.004 1" '
                     f'solimp="0.95 0.99 0.0001"/>')
    return f"""<mujoco model="drop_{name}">
  <compiler angle="radian" meshdir="."/>
  <option timestep="0.002" gravity="0 0 -9.81" integrator="implicitfast"/>
  <asset>{''.join(meshes)}</asset>
  <worldbody>
    <geom name="floor" type="plane" size="5 5 0.1" friction="1.0" contype="1" conaffinity="1"/>
    <body name="obj" pos="0 0 {DROP_H}">
      <freejoint name="root"/>
      {''.join(geoms)}
    </body>
  </worldbody>
</mujoco>"""


def drop_one(parts, name):
    xml = rigid_drop_mjcf(parts, name)
    xmlp = OUT / f"{name}.xml"
    xmlp.write_text(xml)
    try:
        model = mujoco.MjModel.from_xml_path(str(xmlp))
    except Exception as e:
        return {"asset": name, "verdict": "COMPILE_ERROR", "error": str(e)[:120]}
    data = mujoco.MjData(model)
    mass = float(model.body_mass[1])  # obj body
    bad = 0
    peak_pen = 0.0   # 撞击瞬态峰值 (全程)
    ss_pen = 0.0     # 静置窗口 (末 100 步) 穿透 — 稳态判决口径
    SS = 100
    for t in range(SETTLE):
        mujoco.mj_step(model, data)
        qa = float(np.abs(data.qacc).max())
        if not np.isfinite(qa) or qa > 1e6:
            bad += 1
        step_pen = 0.0
        for i in range(data.ncon):
            step_pen = max(step_pen, -data.contact[i].dist if data.contact[i].dist < 0 else 0.0)
        peak_pen = max(peak_pen, step_pen)
        if t >= SETTLE - SS:
            ss_pen = max(ss_pen, step_pen)
    resid_v = float(np.linalg.norm(data.qvel[0:3])) * 1e3          # mm/s
    resid_w = float(np.linalg.norm(data.qvel[3:6]))                # rad/s
    z = float(data.qpos[2])
    return {"asset": name, "mass_kg": round(mass, 3), "rest_z_m": round(z, 4),
            "residual_v_mm_s": round(resid_v, 2), "residual_w_rad_s": round(resid_w, 3),
            "ss_penetration_mm": round(ss_pen * 1e3, 3),
            "impact_peak_mm": round(peak_pen * 1e3, 2), "explosions": bad,
            "verdict": "PASS" if (bad == 0 and ss_pen * 1e3 < 2.0 and resid_v < 1.0
                                  and resid_w < 0.01 and mass > 0.001) else "FAIL"}


def main():
    mod = load_family("pipelines/packaging/author_families/nv960_fixture_family.py")
    cases = []
    for cid, base in mod.DEFAULTS.items():
        for hi, di in [(0.8, 1.0), (1.0, 1.0), (1.0, 1.25)]:
            p = dict(base)
            p["H"] = round(base["H"] * hi, 1)
            p["D"] = round(base["D"] * di, 1)
            p["class_id"] = cid
            cases.append((f"{cid}_h{int(hi*100)}_d{int(di*100)}", p))
    t0 = time.time()
    rows = []
    for name, p in cases:
        parts = mod.build_parts(p)
        rows.append(drop_one(parts, name))
        if len(rows) % 20 == 0:
            print(f"... {len(rows)}/{len(cases)} ({time.time()-t0:.0f}s)", flush=True)
    ok = [r for r in rows if r["verdict"] == "PASS"]
    pens = sorted(r["ss_penetration_mm"] for r in rows)
    peaks = sorted(r["impact_peak_mm"] for r in rows)
    n = len(pens)
    summary = {
        "domain": "nv960 fixtures (20 classes x 3 variants)",
        "n": n, "n_pass": len(ok), "pass_rate": round(len(ok) / n * 100, 1),
        "explosion_rate_pct": round(sum(r.get("explosions", 1) for r in rows) / n * 100, 2),
        "steady_state_penetration_mm": {"p50": pens[n // 2], "p90": pens[int(n * 0.9)], "max": pens[-1]},
        "impact_peak_mm": {"p50": peaks[n // 2], "max": peaks[-1]},
        "max_residual_v_mm_s": max(r["residual_v_mm_s"] for r in rows),
        "max_residual_w_rad_s": max(r["residual_w_rad_s"] for r in rows),
        "fails": [r["asset"] for r in rows if r["verdict"] != "PASS"],
        "wall_time_s": round(time.time() - t0, 1),
    }
    (OUT / "batch_drop_report.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
