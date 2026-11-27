"""批量刚体动力学体检 — 通用 USD 域版 (Gemini P0 全量收口):
六域精选 202 件 (hfpackage liquor/dairy/legacy + nv960 canonical/variants + TDE pilot)
逐件 usdc → 提取 Links 网格合并单刚体 → 50cm 落体 + 300 步静置 → 统计契约。

口径与 nv960 版一致: 静置窗口 (末100步) 穿透 <2mm + 残余 |v| <1mm/s + 零爆炸
判 PASS; 撞击瞬态峰值单列不计入判决。
"""
import json
import sys
import time
from pathlib import Path

import mujoco
import numpy as np
from pxr import Usd, UsdGeom

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
OUT = Path("output/mujoco_downstream/batch_usd")
(OUT / "meshes").mkdir(parents=True, exist_ok=True)
DROP_H = 0.5
SETTLE = 300

_DOMAINS = {
    "hfpackage_liquor": ("hfpackage/assets_liquor", "**/simready_usd/*.usdc"),
    "hfpackage_dairy": ("hfpackage/assets_dairy", "**/simready_usd/*.usdc"),
    "hfpackage_legacy": ("hfpackage/families", "*.usdc"),
    "nv960_canonical": ("output/nv960_usd", "*.usdc"),
    "nv960_variants": ("output/nv960_variants", "*.usdc"),
    "tde_pilot": ("output/pack10k_pilot", "**/model.usdc"),
}

_DENSITY = {"steel": 7850.0, "alu": 2700.0, "pp": 905.0, "paper": 700.0,
            "kraft": 700.0, "white": 700.0, "label": 800.0, "hdpe": 950.0,
            "pet": 1380.0, "glass": 2500.0, "foil": 2700.0, "ceramic": 2400.0,
            "wood": 600.0, "tape": 800.0}


def _density_from_asset(stage):
    """读资产 PhysicsMaterial density; 缺省 1000。"""
    for prim in stage.Traverse():
        if prim.HasAPI("UsdPhysics.MaterialAPI"):
            d = prim.GetAttribute("physics:density")
            if d.HasValue():
                return float(d.Get())
    return 1000.0


def usdc_meshes(path):
    """提取全部 Links 网格 → 合并 OBJ 文本 (单刚体)。"""
    stage = Usd.Stage.Open(str(path))
    density = _density_from_asset(stage)
    chunks, offset = [], 0
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh):
            mesh = UsdGeom.Mesh(prim)
            pts = np.array(mesh.GetPointsAttr().Get(), dtype=float)
            idx = np.array(mesh.GetFaceVertexIndicesAttr().Get(), dtype=int)
            cnt = np.array(mesh.GetFaceVertexCountsAttr().Get(), dtype=int)
            if len(pts) == 0 or len(idx) == 0:
                continue
            # 重组三角形 (导出器只写 tris; 保险起见按 count 展开)
            tris, start = [], 0
            for c in cnt:
                c = int(c)
                if c == 3:
                    tris.append(idx[start:start + 3])
                start += c
            if not tris:
                continue
            tris = np.array(tris, dtype=int) + offset
            offset += len(pts)
            chunks.append((pts, tris))
    if not chunks:
        return None, density
    lines = ["o merged"]
    for pts, _ in chunks:
        lines += [f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in pts]
    for _, tris in chunks:
        lines += [f"f {a+1} {b+1} {c+1}" for a, b, c in tris]
    return "\n".join(lines), density


def drop_one(name, obj_text, density):
    f = OUT / "meshes" / f"{name}.obj"
    f.write_text(obj_text)
    rel = f.relative_to(OUT)
    xml = f"""<mujoco model="drop_{name}">
  <compiler angle="radian" meshdir="."/>
  <option timestep="0.002" gravity="0 0 -9.81" integrator="implicitfast"/>
  <asset><mesh name="{name}" file="{rel}"/></asset>
  <worldbody>
    <geom name="floor" type="plane" size="5 5 0.1" friction="1.0" contype="1" conaffinity="1"/>
    <body name="obj" pos="0 0 {DROP_H}">
      <freejoint name="root"/>
      <geom name="g" type="mesh" mesh="{name}" density="{density}"
            solref="0.004 1" solimp="0.95 0.99 0.0001" contype="1" conaffinity="1"/>
    </body>
  </worldbody>
</mujoco>"""
    xmlp = OUT / f"{name}.xml"
    xmlp.write_text(xml)
    try:
        model = mujoco.MjModel.from_xml_path(str(xmlp))
    except Exception as e:
        return {"asset": name, "verdict": "COMPILE_ERROR", "error": str(e)[:120]}
    data = mujoco.MjData(model)
    mass = float(model.body_mass[1])
    bad = 0
    peak_pen = 0.0
    ss_pen = 0.0
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
    resid_v = float(np.linalg.norm(data.qvel[0:3])) * 1e3
    resid_w = float(np.linalg.norm(data.qvel[3:6]))
    ok = (bad == 0 and ss_pen * 1e3 < 2.0 and resid_v < 1.0 and resid_w < 0.01 and mass > 0.001)
    return {"asset": name, "mass_kg": round(mass, 3),
            "residual_v_mm_s": round(resid_v, 2), "residual_w_rad_s": round(resid_w, 3),
            "ss_penetration_mm": round(ss_pen * 1e3, 3),
            "impact_peak_mm": round(peak_pen * 1e3, 2), "explosions": bad,
            "verdict": "PASS" if ok else "FAIL"}


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    rows, t0 = [], time.time()
    for domain, (rel, pattern) in _DOMAINS.items():
        if only and domain != only:
            continue
        dpath = Path(rel)
        if not dpath.exists():
            print(f"[{domain}] SKIP (no dir {dpath})", flush=True)
            continue
        for usdc in sorted(dpath.glob(pattern)):
            name = f"{domain}__{usdc.stem}"
            try:
                obj, density = usdc_meshes(usdc)
            except Exception as e:
                rows.append({"asset": name, "verdict": "EXTRACT_ERROR", "error": str(e)[:120]})
                continue
            if obj is None:
                rows.append({"asset": name, "verdict": "NO_MESH"})
                continue
            rows.append(drop_one(name, obj, density))
        print(f"[{domain}] done ({len(rows)} rows so far, {time.time()-t0:.0f}s)", flush=True)
    ok = [r for r in rows if r.get("verdict") == "PASS"]
    pens = sorted(r["ss_penetration_mm"] for r in rows if "ss_penetration_mm" in r)
    n = len(rows)
    summary = {
        "n": n, "n_pass": len(ok), "pass_rate": round(len(ok) / n * 100, 1) if n else 0.0,
        "ss_penetration_mm": {"p50": pens[len(pens)//2], "p90": pens[int(len(pens)*0.9)], "max": pens[-1]} if pens else None,
        "fails": [r["asset"] for r in rows if r.get("verdict") != "PASS"],
        "wall_time_s": round(time.time() - t0, 1),
    }
    (OUT / "batch_drop_report.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
