import sys
sys.path.insert(0,'/tmp/pd_recheck/probe_head')
from common import *
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.ops import polygonize

def silhouette(world, axis):
    elems = []
    for v in world.values():
        P = np.delete(np.asarray(v, float), axis, axis=1)
        if Polygon(P).area > 1e-9:
            elems.append(Polygon(P).buffer(0).exterior)
        else:
            for i in range(len(P)):
                elems.append(LineString([P[i], P[(i + 1) % len(P)]]))
    G = unary_union(elems).buffer(0.02)
    polys = [g for g in (G.geoms if G.geom_type != 'Polygon' else [G])]
    return unary_union([Polygon(p.exterior) for p in polys])

def cover(cid, axis, groups):
    mod, params, ir, world = load(cid)
    sil = silhouette(world, axis)
    out = {}
    for name, pids in groups.items():
        polys = [Polygon(np.delete(world[p], axis, axis=1)).buffer(0) for p in pids]
        u = unary_union([p for p in polys if p.area > 1e-9])
        out[name] = {'union': round(float(u.area), 1), 'uncovered': round(float(sil.difference(u).area), 1),
                     'cover_ratio': round(float(u.intersection(sil).area) / float(sil.area), 3)}
    return round(float(sil.area), 1), out

print('--- envelopes (front coverage on body plane) ---')
for cid, flaps in (('envelope_square', ['flapL','flapR','flapB','flapT']), ('envelope_wedge', ['sideL','sideR','bot','top'])):
    mod, params, ir, world = load(cid)
    body = [p for p in world if ir.panel(p)['role']=='wall'][0]
    n, _ = plane_normal(world[body]); axis = int(np.argmax(np.abs(n)))
    B = Polygon(np.delete(world[body], axis, axis=1)); U = unary_union([Polygon(np.delete(world[p], axis, axis=1)) for p in flaps])
    hole = B.difference(U)
    nparts = len(hole.geoms) if hole.geom_type != 'Polygon' else (1 if hole.area > 0 else 0)
    print(cid, 'body', round(B.area,1), 'covered', round(B.intersection(U).area,1), 'UNCOVERED', round(hole.area,1), f'({100*hole.area/B.area:.1f}%)', 'holes', nparts, 'sum/union', round(float(sum(Polygon(np.delete(world[p], axis, axis=1)).area for p in flaps))/B.area,3))
print('--- pillow ends (x faces) ---')
print(cover('pillow_box', 0, {'endL': ['endFL','endBL'], 'endR': ['endFR','endBR']}))
print('--- clamshell ends ---')
print(cover('food_clamshell_burger', 0, {'wL': ['wL'], 'wR': ['wR']}))
print('--- tray_domelid ends ---')
print(cover('tray_domelid', 0, {'wL': ['wL'], 'wR': ['wR']}))
print('--- tube_cap_end bottom (z=0) / top ---')
print(cover('tube_cap_end', 2, {'cap*': [f'cap{k}' for k in range(8)], 'flange': [f'f{i}' for i in range(16)]}))
print('--- noodle pail top/bottom ---')
print(cover('food_noodle_pail', 2, {'tf*': [f'tf{k}' for k in range(8)], 'wg*': ['wg0','wg4']}))
print('--- wrap pocket bottom ---')
print(cover('food_wrap_pocket', 2, {'all': list(load('food_wrap_pocket')[3].keys())}))
print('--- frustum bottom ---')
print(cover('pyramid_frustum_n4', 2, {'all': list(load('pyramid_frustum_n4')[3].keys())}))
print('--- hexagonal_flip bottom ---')
print(cover('hexagonal_flip', 2, {'all': list(load('hexagonal_flip')[3].keys())}))
print('--- liner rim (z=H plane projected) ---')
print(cover('food_tray_liner', 2, {'rim': [f'f{i}' for i in range(6)]}))
for cid in ('prism_n4_open','prism_n5_tuck','prism_n6_tuck','prism_n8_tuck','prism_n12_tuck','prism_dust_n6','prism_dust_n12','hexagonal_flip','tube_double_seam','rsc_rsc','tuck_top_box','clv_double_tuck','gable_top','envelope_square','envelope_wedge','lockbottom_123','crashlock_rect'):
    mod, params, ir, world = load(cid)
    roles = {p['id']: p['role'] for p in ir.panels}
    fl = [p for p in world if roles[p] == 'flap']
    groups = {}
    for p in fl:
        n, _ = plane_normal(world[p]); c = world[p].mean(0)
        key = None
        for g in groups:
            if abs(float(n @ groups[g][0])) > 1 - 1e-7 and abs(float((c - groups[g][1]) @ groups[g][0])) < 1e-3:
                key = g; break
        if key is None:
            groups[f"g{len(groups)}"] = (n, c, [p])
        else:
            groups[key][2].append(p)
    for g, (n, c, pids) in groups.items():
        axis = int(np.argmax(np.abs(n)))
        ar = sum(Polygon(np.delete(world[p], axis, axis=1)).area for p in pids)
        u = unary_union([Polygon(np.delete(world[p], axis, axis=1)) for p in pids]).area
        if len(pids) >= 2 and ar / u > 1.01:
            # multiplicity
            cells = list(polygonize(unary_union([Polygon(np.delete(world[p], axis, axis=1)).buffer(0) for p in pids]).boundary))
            cnt = np.zeros(len(cells))
            for p in pids:
                P = Polygon(np.delete(world[p], axis, axis=1))
                cnt += np.array([cell.representative_point().within(P) for cell in cells])
            h = [round(float(sum(cell.area for cell, k in zip(cells, cnt) if k == m)) / u, 3) for m in (1, 2)]
            h3 = round(float(sum(cell.area for cell, k in zip(cells, cnt) if k >= 3)) / u, 3)
            print(f"{cid} {g}: n={len(pids)} sum/union={ar/u:.3f} 1x/2x/3x+={h+[h3]} union_area={u:.0f} ids={pids[:8]}")
