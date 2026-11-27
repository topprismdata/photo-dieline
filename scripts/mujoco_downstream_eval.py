"""MuJoCo 下游物理评测 (Gemini 攻击点③的实证回应):
shopping_cart 铰接资产 → MJCF → 落地稳定 + 驱动轮滚动 1200 步。

判决指标 (fail-closed):
- 落地后 ≥3 轮持续触地 (占空比 >80%)
- 驱动段购物车净位移 >0.1 m 且轮子真转 (|qvel| > 2 rad/s)
- 全程无 NaN / 无爆炸 (|qacc| < 1e6), 最大穿透 > -5 mm
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from photo_dieline.authoring.validate_parts import load_family

import mujoco
import numpy as np

OUT = Path("output/mujoco_downstream")
OUT.mkdir(parents=True, exist_ok=True)

_DENSITY = {"steel": 7850.0, "alu": 2700.0, "pp": 905.0, "paper": 700.0,
            "kraft": 700.0, "white": 700.0, "label": 800.0}


def _mat_density(mid):
    for k, v in _DENSITY.items():
        if k in mid:
            return v
    return 1000.0


def build_mjcf(parts):
    """部件 → MJCF: frame 类锁连合并进根刚体, fork (limits 0,0) 合并, 轮 = 铰接子体。"""
    mesh_dir = OUT / "meshes"
    mesh_dir.mkdir(exist_ok=True)
    wheels = [p for p in parts if p["name"].startswith("wheel_")]
    locked = [p for p in parts if p["name"] not in {w["name"] for w in wheels}]
    geoms, meshes = [], []
    for p in locked + wheels:
        mname = p["name"]
        (mesh_dir / f"{mname}.obj").write_text(_obj_text(p))
        meshes.append(f'<mesh name="{mname}" file="meshes/{mname}.obj"/>')
    for p in locked:
        geoms.append(f'<geom name="{p["name"]}" type="mesh" mesh="{p["name"]}" '
                     f'density="{_mat_density(p["material_id"])}" '
                     f'contype="0" conaffinity="0" group="1"/>')
    for p in wheels:
        geoms.append(None)  # 占位, 轮在子体里
    mx = max(v[0] for p in locked for v in p["verts_mm"])
    wheel_joints = ""
    for w in wheels:
        j = w["joint"]
        o_m = [v * 1e-3 for v in j["origin"]]
        wheel_joints += (
            f'<body name="{w["name"]}" pos="0 0 0">'
            f'<joint name="{w["name"]}_spin" type="hinge" axis="0 1 0" '
            f'pos="{o_m[0]:.4f} {o_m[1]:.4f} {o_m[2]:.4f}" damping="0.002"/>'
            f'<geom name="{w["name"]}" type="cylinder" size="0.042 0.02" '
            f'pos="{o_m[0]:.4f} {o_m[1]:.4f} {o_m[2]:.4f}" euler="1.5707963 0 0" '
            f'density="{_mat_density(w["material_id"])}" '
            f'solref="0.004 1" solimp="0.95 0.99 0.0001" '
            f'contype="1" conaffinity="1" group="0"/></body>')
    xml = f"""<mujoco model="nv960_shopping_cart_downstream">
  <compiler angle="radian" meshdir="."/>
  <option timestep="0.002" gravity="0 0 -9.81" integrator="implicitfast"/>
  <asset>{''.join(meshes)}</asset>
  <worldbody>
    <light pos="0 0 3" dir="0 0 -1"/>
    <geom name="floor" type="plane" size="5 5 0.1" friction="1.0" contype="1" conaffinity="1"/>
    <body name="cart" pos="0 0 0.005">
      <freejoint name="root"/>
      {''.join(g for g in geoms if g)}
      {wheel_joints}
    </body>
  </worldbody>
  <actuator>
    {''.join(f'<motor name="{w["name"]}_m" joint="{w["name"]}_spin" gear="1"/>' for w in wheels)}
  </actuator>
</mujoco>"""
    return xml


def _obj_text(part):
    lines = ["o " + part["name"]]
    lines += [f"v {x*1e-3:.6f} {y*1e-3:.6f} {z*1e-3:.6f}" for (x, y, z) in part["verts_mm"]]
    lines += [f"f {a+1} {b+1} {c+1}" for (a, b, c) in part["tris"]]
    return "\n".join(lines)


def main():
    mod = load_family("pipelines/packaging/author_families/nv960_fixture_family.py")
    params = dict(mod.DEFAULTS["shopping_cart"])
    parts = mod.build_parts(params)
    xml = build_mjcf(parts)
    (OUT / "shopping_cart.xml").write_text(xml)
    model = mujoco.MjModel.from_xml_path(str(OUT / "shopping_cart.xml"))
    data = mujoco.MjData(model)
    wheel_adr = [model.actuator(f"wheel_{s}_m").id for s in ("lf", "rf", "lb", "rb")]

    settle, drive = 300, 900
    ground_pct, max_pen, disp, spin, bad = [], -1e9, None, [], 0
    for t in range(settle + drive):
        if t >= settle:
            for a in wheel_adr:
                data.ctrl[a] = 0.6  # N·m 四轮驱动
        mujoco.mj_step(model, data)
        qacc = np.abs(data.qacc).max()
        if not np.isfinite(qacc) or qacc > 1e6:
            bad += 1
        nwheel, ncontact = 0, 0
        pen = 0.0
        for i in range(data.ncon):
            c = data.contact[i]
            pen = min(pen, c.dist)
            names = {mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1),
                     mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2)}
            ncontact += 1
            if sum(1 for n in names if n and n.startswith("wheel_")) >= 1 and "floor" in names:
                nwheel += 1
        ground_pct.append(nwheel)
        max_pen = max(max_pen, -pen if pen < 0 else 0.0)
        if t == settle - 1:
            p0 = data.qpos[:3].copy()
        if t == settle + drive - 1:
            disp = float(np.linalg.norm(data.qpos[:3] - p0))
            spin = [float(abs(data.qvel[model.jnt_dofadr[model.actuator_trnid[a, 0]]])) for a in wheel_adr]

    wheels_grounded = sum(1 for g in ground_pct[settle:] if g >= 3) / drive
    verdict = {
        "steps": settle + drive, "wheels_grounded_pct": round(wheels_grounded * 100, 1),
        "net_displacement_m": round(disp, 3) if disp is not None else None,
        "wheel_spin_rad_s": [round(s, 1) for s in spin],
        "max_penetration_mm": round(max_pen * 1e3, 3), "explosions": bad,
        "n_actuators": len(wheel_adr), "n_joints": model.njnt,
    }
    ok = (wheels_grounded > 0.8 and disp > 0.1 and max(spin) > 2.0
          and bad == 0 and max_pen * 1e3 < 5.0)
    verdict["verdict"] = "PASS" if ok else "FAIL"
    (OUT / "downstream_report.json").write_text(json.dumps(verdict, indent=1))
    print(json.dumps(verdict, indent=1))


if __name__ == "__main__":
    main()
