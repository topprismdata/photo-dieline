#!/usr/bin/env python3
"""bench_simready_physics: 官方 SimReady 资产过我方物理静置门 (对标实验).

协议与 verify_sku_physics 完全镜像: bbox + 质量 + 材质摩擦, free joint,
5mm 初始间隙, 1s 仿真, KE≈0 + 贴地稳定.
数据来源为官方元数据: asset_extents (m) / mass (kg) / semantics:labels:material.
任一字段缺失 → FAIL (ESR 证据完备性本身就是被测对象).
用法: python3 scripts/bench_simready_physics.py [--dir assets/simready_official]
"""
import argparse
import json
from pathlib import Path

import mujoco
import numpy as np
from pxr import Usd

ROOT = Path(__file__).parent.parent
GAP = 0.005
FRIC = {"glass": 0.4, "clear_glass": 0.4, "plastic": 0.4, "paperboard": 0.6,
        "plant": 0.7, "organic": 0.7, "metal": 0.4}


def resolve_material(stage):
    # 材质 prim 可能藏在实例代理内 (同嵌套代理遍历缺口) — 先解除
    for prim in stage.TraverseAll():
        if prim.IsInstance():
            prim.SetInstanceable(False)
    for prim in stage.TraverseAll():
        for attr in prim.GetAttributes():
            n = attr.GetName()
            if n.startswith("semantics:labels:material") and attr.Get() is not None:
                return str(attr.Get())
    return None


def settle(dims_m, mass, mu):
    w, d, h = dims_m
    mjcf = f"""
<mujoco>
  <option timestep="0.002" gravity="0 0 -9.81"/>
  <worldbody>
    <geom name="floor" type="plane" size="1 1 0.1" friction="1 1 1"/>
    <body name="sku" pos="0 0 {h / 2 + GAP}">
      <freejoint/>
      <geom name="g" type="box" size="{w / 2} {d / 2} {h / 2}" mass="{mass}"
            friction="{mu} {mu} 1" condim="3"/>
    </body>
  </worldbody>
</mujoco>"""
    m = mujoco.MjModel.from_xml_string(mjcf)
    data = mujoco.MjData(m)
    z0 = data.qpos[2]
    for _ in range(500):
        mujoco.mj_step(m, data)
    ke = 0.5 * mass * float(np.dot(data.qvel[:3], data.qvel[:3]))
    z = data.qpos[2]
    stable = ke < 1e-6
    settled = z < z0 + GAP + 1e-3 and abs(z - (h / 2)) < GAP + 2e-3
    return stable, settled, ke, z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "assets/simready_official"))
    args = ap.parse_args()
    results = []
    for d in sorted(Path(args.dir).iterdir()):
        if not d.is_dir():
            continue
        mains = sorted(d.glob("sm_*.usd*"))
        if not mains:
            continue
        stage = Usd.Stage.Open(str(mains[0]))
        cld = dict(stage.GetRootLayer().customLayerData or {})
        cld.update(cld.get("SimReady_Metadata") or {})  # 官方字段在 SimReady_Metadata 内层
        ext = cld.get("asset_extents")
        mass = cld.get("mass")
        mat = resolve_material(stage)
        row = {"asset": d.name}
        if ext is None or mass is None or mat is None:
            row.update({"pass": False,
                        "err": f"missing metadata: ext={ext} mass={mass} mat={mat}"})
        else:
            mu = FRIC.get(mat, 0.5)
            stable, settled, ke, z = settle([float(x) for x in ext], float(mass), mu)
            row.update({"pass": bool(stable and settled),
                        "dims_mm": [round(x * 1000, 1) for x in ext],
                        "mass_kg": round(float(mass), 4),
                        "material": mat, "friction": mu,
                        "ke": float(f"{ke:.2e}"), "z": round(z, 4)})
        results.append(row)
        print(f"{'PASS' if row['pass'] else 'FAIL'} {d.name}: {row.get('err') or ''}"
              f"{row.get('dims_mm','')} {row.get('mass_kg','')}kg {row.get('material','')} "
              f"KE={row.get('ke','')} z={row.get('z','')}")
    ok = sum(r["pass"] for r in results)
    (ROOT / "data/shelf_twin/bench_simready_physics.json").write_text(
        json.dumps({"schema": "simready-bench-physics/1.0", "results": results,
                    "ok": ok, "fail": len(results) - ok}, ensure_ascii=False, indent=1))
    print(f"BENCH_PHYSICS_DONE ok={ok} fail={len(results) - ok}")


if __name__ == "__main__":
    main()
