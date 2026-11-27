#!/usr/bin/env python3
"""Batch dual thumbnails (dark+light, 256px) for a list of usdc files.

Run inside Blender:
  Blender --background --python scripts/render_thumbs_batch.py -- <manifest.txt>
manifest.txt: one usdc path per line. Output: <usdc_dir>/.thumbs/256x256/<name>.png + <name>_light.png
Camera: azimuth 45deg / elevation 30deg from -Y front, focal-fit (USDCraft contract, same as render_liquor_usdc).
"""
import math
import sys
from pathlib import Path

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
manifest = Path(argv[0])
usdc_files = [Path(l.strip()) for l in manifest.read_text().splitlines() if l.strip()]


def clear_scene():
    for name in ("Cube", "Light", "Camera"):
        o = bpy.data.objects.get(name)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras):
        for b in list(block):
            if b.users == 0:
                block.remove(b)


def world_bbox(objs):
    pts = []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        oe = o.evaluated_get(dg)
        for c in oe.bound_box:
            pts.append(oe.matrix_world @ mathutils.Vector(c))
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


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
sc.render.resolution_x = 256
sc.render.resolution_y = 256
cd = bpy.data.cameras.new("C"); cd.lens = 60
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam)
sc.camera = cam
half_fov = math.atan(12.0 / 60.0)

done = 0
for usdc in usdc_files:
    try:
        clear_scene()
        before = set(bpy.data.objects)
        bpy.ops.wm.usd_import(filepath=str(usdc))
        objs = [o for o in bpy.data.objects if o not in before]
        if not objs:
            print(f"SKIP (no objects): {usdc}")
            continue
        (mn, mx) = world_bbox(objs)
        c = mathutils.Vector(((mn[0]+mx[0])/2, (mn[1]+mx[1])/2, (mn[2]+mx[2])/2))
        r = max(mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2]) * 0.5
        d = r * 1.15 / math.sin(half_fov)
        az, el = math.radians(45), math.radians(30)
        cam.location = c + mathutils.Vector(
            (math.sin(az)*math.cos(el)*d, -math.cos(az)*math.cos(el)*d, math.sin(el)*d))
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        out_dir = usdc.parent / '.thumbs' / '256x256'
        out_dir.mkdir(parents=True, exist_ok=True)
        for dark, suffix in ((True, ''), (False, '_light')):
            w.color = (0.075, 0.078, 0.086) if dark else (0.93, 0.93, 0.94)
            sc.render.filepath = str(out_dir / f"{usdc.name}{suffix}.png")
            bpy.ops.render.render(write_still=True)
        done += 1
        print(f"THUMBS OK: {usdc.name}")
    except Exception as e:
        print(f"THUMBS FAIL: {usdc}: {e}")
print(f"DONE {done}/{len(usdc_files)}")
