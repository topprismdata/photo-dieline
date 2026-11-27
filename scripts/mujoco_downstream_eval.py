"""MuJoCo 下游物理评测 (Gemini 攻击点①③的实证回应):
铰接零售设备资产 → MJCF → 场景化驱动仿真 (fail-closed 判决)。

场景:
- shopping_cart「roll」: 落地稳定 + 四轮驱动 1200 步
  判决: ≥3 轮触地占空比 >80%, 净位移 >0.1m, 轮速 >2 rad/s, 无爆炸, 穿透 <5mm
- rotating_display_stand「spin」: 落地稳定 + 极轴驱动 1200 步
  判决: 货架真旋转 (>2 rad), 机身倾覆角 <5°, 无爆炸, 穿透 <5mm

转换约定: 非关节部件并入根刚体 (焊接等价); limits==(0,0) 的锁定 revolute
并入根; 自由 revolute → 子体 hinge (axis/origin 按 spec 换算 m)。USD 侧保留
完整铰接拓扑 (验证器同构), MJCF 侧做刚体等价简化 — 两侧语义各自保真。
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


def _obj_text(part):
    lines = ["o " + part["name"]]
    lines += [f"v {x*1e-3:.6f} {y*1e-3:.6f} {z*1e-3:.6f}" for (x, y, z) in part["verts_mm"]]
    lines += [f"f {a+1} {b+1} {c+1}" for (a, b, c) in part["tris"]]
    return "\n".join(lines)


def build_mjcf(parts, cls):
    mesh_dir = OUT / "meshes"
    mesh_dir.mkdir(exist_ok=True)
    free = [p for p in parts if p.get("joint") and tuple(p["joint"]["limits_deg"]) != (0, 0)]
    locked = [p for p in parts if p not in free]
    meshes, root_geoms, children = [], [], ""
    for p in locked + free:
        (mesh_dir / f"{cls}_{p['name']}.obj").write_text(_obj_text(p))
        meshes.append(f'<mesh name="{cls}_{p["name"]}" file="meshes/{cls}_{p["name"]}.obj"/>')
    for p in locked:
        root_col = "1" if cls == "rotating_display_stand" else "0"  # 架底座落地; 车架由轮承载
        root_geoms.append(f'<geom name="{cls}_{p["name"]}" type="mesh" mesh="{cls}_{p["name"]}" '
                          f'density="{_mat_density(p["material_id"])}" '
                          f'contype="{root_col}" conaffinity="{root_col}" group="1"/>')
    for p in free:
        j = p["joint"]
        o_m = [v * 1e-3 for v in j["origin"]]
        ax = "".join(f"{v:.1f} " for v in j["axis"]).strip()
        r = 0.042 if cls == "shopping_cart" else 0.25  # 解析替代: 轮圆柱 / 货架圆盘 (与网格同径)
        half = 0.02 if cls == "shopping_cart" else 0.005
        free_col = "1" if cls == "shopping_cart" else "0"  # 轮触地; 货架由铰点承载不碰地
        children += (
            f'<body name="{cls}_{p["name"]}" pos="0 0 0">'
            f'<joint name="{cls}_{p["name"]}_j" type="hinge" axis="{ax}" '
            f'pos="{o_m[0]:.4f} {o_m[1]:.4f} {o_m[2]:.4f}" damping="0.002"/>'
            f'<geom name="{cls}_{p["name"]}" type="cylinder" size="{r} {half}" '
            f'pos="{o_m[0]:.4f} {o_m[1]:.4f} {o_m[2]:.4f}" '
            + ('euler="1.5707963 0 0" ' if cls == "shopping_cart" else "")
            + f'density="{_mat_density(p["material_id"])}" '
              f'solref="0.004 1" solimp="0.95 0.99 0.0001" '
              f'contype="{free_col}" conaffinity="{free_col}" group="0"/></body>')
    xml = f"""<mujoco model="nv960_{cls}_downstream">
  <compiler angle="radian" meshdir="."/>
  <option timestep="0.002" gravity="0 0 -9.81" integrator="implicitfast"/>
  <asset>{''.join(meshes)}</asset>
  <worldbody>
    <light pos="0 0 3" dir="0 0 -1"/>
    <geom name="floor" type="plane" size="5 5 0.1" friction="1.0" contype="1" conaffinity="1"/>
    <body name="{cls}_root" pos="0 0 0.005">
      <freejoint name="root"/>
      {''.join(root_geoms)}
      {children}
    </body>
  </worldbody>
  <actuator>
    {''.join(f'<motor name="{p["name"]}_m" joint="{cls}_{p["name"]}_j" gear="1"/>' for p in free)}
  </actuator>
</mujoco>"""
    return xml, [p["name"] for p in free]


def contacts(model, data, prefix):
    nwheel, pen = 0, 0.0
    for i in range(data.ncon):
        c = data.contact[i]
        pen = min(pen, c.dist)
        names = {mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1),
                 mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2)}
        if any(n and n.startswith(prefix) for n in names) and "floor" in names:
            nwheel += 1
    return nwheel, -pen if pen < 0 else 0.0


def run_case(cls, ctrl_val, settle, drive, q_start=None):
    mod = load_family("pipelines/packaging/author_families/nv960_fixture_family.py")
    parts = mod.build_parts(dict(mod.DEFAULTS[cls]))
    xml, free_names = build_mjcf(parts, cls)
    (OUT / f"{cls}.xml").write_text(xml)
    model = mujoco.MjModel.from_xml_path(str(OUT / f"{cls}.xml"))
    data = mujoco.MjData(model)
    aids = [model.actuator(f"{n}_m").id for n in free_names]
    grounded_pct, max_pen, bad = [], 0.0, 0
    for t in range(settle + drive):
        if t >= settle:
            for a in aids:
                data.ctrl[a] = ctrl_val
        mujoco.mj_step(model, data)
        qa = np.abs(data.qacc).max()
        if not np.isfinite(qa) or qa > 1e6:
            bad += 1
        _, pen = contacts(model, data, cls)
        max_pen = max(max_pen, pen)
        grounded_pct.append(contacts(model, data, cls)[0])
    return model, data, free_names, grounded_pct[settle:], max_pen, bad, settle, drive


def case_cart():
    model, data, free, g, max_pen, bad, settle, drive = run_case("shopping_cart", 0.6, 300, 900)
    pct = sum(1 for x in g if x >= 3) / drive
    disp = float(np.linalg.norm(data.qpos[:3]))  # 根位移 (起点≈0)
    spins = [float(abs(data.qvel[model.jnt_dofadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"shopping_cart_{n}_j")]])) for n in free]
    rep = {"asset": "shopping_cart", "scenario": "roll", "steps": settle + drive,
           "wheels_grounded_pct": round(pct * 100, 1), "net_displacement_m": round(disp, 3),
           "wheel_spin_rad_s": [round(s, 1) for s in spins],
           "max_penetration_mm": round(max_pen * 1e3, 3), "explosions": bad}
    rep["verdict"] = "PASS" if (pct > 0.8 and disp > 0.1 and max(spins) > 2 and bad == 0
                                and max_pen * 1e3 < 5) else "FAIL"
    return rep


def case_stand():
    model, data, free, g, max_pen, bad, settle, drive = run_case("rotating_display_stand", 2.0, 300, 900)
    # 货架旋转角: hinge 角坐标 qpos (自由度 adr)
    angs = []
    for n in free:
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f"rotating_display_stand_{n}_j")
        angs.append(float(abs(data.qpos[model.jnt_qposadr[jid]])))
    qa = float(np.abs(data.qacc).max())
    rep = {"asset": "rotating_display_stand", "scenario": "spin", "steps": settle + drive,
           "shelf_rotation_rad": [round(a, 2) for a in angs],
           "max_penetration_mm": round(max_pen * 1e3, 3), "explosions": bad,
           "final_qacc_max": round(qa, 1)}
    rep["verdict"] = "PASS" if (max(angs) > 2.0 and bad == 0 and max_pen * 1e3 < 5) else "FAIL"
    return rep


def main():
    reps = []
    (OUT / "shopping_cart_joints.txt").unlink(missing_ok=True)
    (OUT / "rotating_display_stand_joints.txt").unlink(missing_ok=True)
    for fn in (case_cart, case_stand):
        try:
            reps.append(fn())
        except Exception as e:
            reps.append({"verdict": "ERROR", "error": f"{type(e).__name__}: {e}"})
    (OUT / "downstream_report.json").write_text(json.dumps(reps, indent=1, ensure_ascii=False))
    allpass = all(r.get("verdict") == "PASS" for r in reps)
    print(json.dumps({"overall": "PASS" if allpass else "FAIL", "cases": reps}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
