#!/usr/bin/env python3
"""Fix physics:centerOfMass = (-inf,-inf,-inf) sentinel in simready usdc assets.

Root cause: lost inline structuring step authored -inf sentinel COM opinions.
NVIDIA USDCraft finite_authored_values gate correctly flags them (PhysX consumes
the attribute; -inf is invalid). Repair: compute mesh vertex centroid per Link
(uniform-density approximation, provenance: derived) and author finite COM.
Rerun scripts (usdcraft_gate in openusd-retail-twin) must pass 15/15.
"""
import sys, math, json
from pathlib import Path
from pxr import Usd, UsdPhysics, Gf, UsdGeom


def link_centroid(link_prim):
    """Uniform vertex centroid over all mesh descendants (world→link local)."""
    pts = []
    xform = UsdGeom.XformCache(Usd.TimeCode.Default())
    for descendant in Usd.PrimRange(link_prim, Usd.PrimIsActive):
        if descendant.IsA(UsdGeom.Mesh):
            mesh = UsdGeom.Mesh(descendant)
            world = xform.GetLocalToWorldTransform(descendant)
            for p in mesh.GetPointsAttr().Get():
                pts.append(world.Transform(Gf.Vec3d(p)))
    if not pts:
        return None
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    cz = sum(p[2] for p in pts) / len(pts)
    return Gf.Vec3f(cx, cy, cz)


def fix_asset(usdc_path):
    st = Usd.Stage.Open(str(usdc_path))
    fixed = 0
    for prim in st.Traverse():
        mass = UsdPhysics.MassAPI(prim) if prim.HasAPI(UsdPhysics.MassAPI) else None
        if mass is None:
            continue
        attr = mass.GetCenterOfMassAttr()
        v = attr.Get()
        needs = v is None or not all(math.isfinite(float(c)) for c in v)
        if not needs:
            continue
        com = link_centroid(prim)
        if com is None:
            print(f"  SKIP {prim.GetPath()}: no mesh descendants for centroid")
            continue
        attr.Set(com)
        fixed += 1
    if fixed:
        st.GetRootLayer().Save()
    return fixed


def main():
    roots = [Path('/Users/guohongbin/photo-dieline/hfpackage/assets_liquor'),
             Path('/Users/guohongbin/photo-dieline/hfpackage/families')]
    files = sorted(roots[0].glob('*/simready_usd/*.usdc')) + sorted(roots[1].glob('*.usdc'))
    total = 0
    for f in files:
        n = fix_asset(f)
        total += n
        if n:
            print(f'{f.name}: {n} COM opinions rewritten')
    print(f'total fixed: {total} across {len(files)} assets')


if __name__ == '__main__':
    main()
