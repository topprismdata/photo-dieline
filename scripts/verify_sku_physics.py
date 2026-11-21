#!/usr/bin/env python3
"""verify_sku_physics: MuJoCo 静置验证 (ESR Step B ③).

每个 SKU: 包围盒 geom + free joint + 5mm 初始间隙 (防深穿透弹飞), 仿真 1s:
- 最终 KE ≈ 0 (静止)
- 高度稳定 (无穿地/弹飞)
- 摩擦按材质 (plastic 0.4 / paperboard 0.6)
用法: python3 scripts/verify_sku_physics.py
"""
import json
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).parent.parent
MANIFEST = json.loads((ROOT / "data/shelf_twin/sku_manifest.json").read_text())
FRIC = MANIFEST["friction"]
GAP = 0.005  # 5mm 初始间隙


def verify(sku):
    w, d, h = [x / 1000 for x in sku["dims_mm"]]
    mass = sku["mass_g"] / 1000
    mu = FRIC[sku["material"]]
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
    for _ in range(500):  # 1s
        mujoco.mj_step(m, data)
    ke = 0.5 * mass * float(np.dot(data.qvel[:3], data.qvel[:3]))
    z = data.qpos[2]
    settled = z < z0 + GAP + 1e-3 and abs(z - (h / 2)) < GAP + 2e-3  # 落到贴地
    return ke < 1e-6, settled, ke, z, h / 2


def main():
    ok, fail = 0, 0
    for sku in MANIFEST["skus"]:
        stable, settled, ke, z, z_expect = verify(sku)
        passed = stable and settled
        ok += passed
        fail += not passed
        print(f"{'PASS' if passed else 'FAIL'} {sku['id']}: KE={ke:.2e} z={z:.4f} (expect~{z_expect:.4f})")
    print(f"PHYSICS_DONE ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
