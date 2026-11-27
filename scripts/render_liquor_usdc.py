#!/usr/bin/env python3
"""Render liquor usdc assets to studio PNGs (Workbench, USDCraft camera contract).

Usage: /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/render_liquor_usdc.py -- <usdc> <out_png>
Camera: azimuth 45deg, elevation 30deg, from -Y front, focal-fit to bbox (same contract as pack10k_thumbs).
"""
import math
import sys
from pathlib import Path

import bpy
import mathutils
from pxr import Usd, UsdGeom, Vt

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
usdc_path, out_png = Path(argv[0]), Path(argv[1])


def clear_scene():
    for name in ("Cube", "Light", "Camera"):
        o = bpy.data.objects.get(name)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)


def import_usdc(path):
    before = set(bpy.data.objects)
    bpy.ops.wm.usd_import(filepath=str(path))
    return [o for o in bpy.data.objects if o not in before]


def world_bbox(objs):
    pts = []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        oe = o.evaluated_get(dg)
        for c in oe.bound_box:
            pts.append(oe.matrix_world @ mathutils.Vector(c))
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


clear_scene()
objs = import_usdc(usdc_path)
assert objs, f"no objects imported from {usdc_path}"
(mn, mx) = world_bbox(objs)
c = mathutils.Vector(((mn[0]+mx[0])/2, (mn[1]+mx[1])/2, (mn[2]+mx[2])/2))
r = max(mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2]) * 0.5

sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.render_aa = "FXAA"
sh = sc.display.shading
sh.background_type = "WORLD"
sh.light = "STUDIO"
sh.color_type = "TEXTURE"
sh.show_cavity = True
sh.cavity_type = "WORLD"
w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
sc.world = w
w.color = (0.93, 0.93, 0.94)

cd = bpy.data.cameras.new("C"); cd.lens = 60
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam)
sc.camera = cam
half_fov = math.atan(12.0 / 60.0)  # 60mm lens vertical half-FOV
d = r * 1.15 / math.sin(half_fov)
az, el = math.radians(45), math.radians(30)
cam.location = c + mathutils.Vector(
    (math.sin(az)*math.cos(el)*d, -math.cos(az)*math.cos(el)*d, math.sin(el)*d))
direction = c - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.filepath = str(out_png)
bpy.ops.render.render(write_still=True)
print(f"rendered {usdc_path.name} -> {out_png}")
