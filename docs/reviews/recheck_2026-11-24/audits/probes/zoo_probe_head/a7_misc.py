"""杂项探针 (固定 HEAD 54b81ca 快照): G06 覆盖率 / allowed_overlap 空放行 / 折线标注朝向 /
SVG 铰链切断 / 底板合法性 / validate 边界用例 / 模块 probe / 核心交叉核对 / 退化首三角."""
import json, sys, re, copy
import numpy as np
from collections import Counter, defaultdict
from shapely.geometry import Polygon, LineString
sys.path.insert(0, "/tmp/pd_recheck/probe_head")
from common import *
from photo_dieline.qa.pipeline import _intersect3d
import photo_dieline
from shapely import is_valid_reason

OUT = {"photo_dieline_file": photo_dieline.__file__}
# 1. G06 pair coverage + allowed_overlap vacuity + crossings
tot = Counter(); vac_tot = allowed_tot = 0; rows = []; cross = []
for cid in T.all_classes():
    mod, params, ir, world = load(cid)
    roles = {p['id']: p['role'] for p in ir.panels}
    ids = list(world); n = len(ids); allp = n * (n - 1) // 2
    share = {frozenset((e.parent, e.child)) for e in ir.edges}
    allowed = mod.allowed_overlap() | ALLOWED_OVERLAP
    sk = al = ff = tested = 0
    norms = {p: plane_normal(world[p])[0] for p in ids}
    real = set()
    for i in range(n):
        for j in range(i + 1, n):
            a, b = ids[i], ids[j]; key = frozenset((a, b))
            na, nb = norms[a], norms[b]
            ov = False
            if na is not None and nb is not None:
                if coplanar(world[a], na, world[b], nb):
                    ov = Polygon(to2d(world[a], na)).intersection(Polygon(to2d(world[b], na))).area > 1e-3
                else:
                    L = cross_len(world[a], na, world[b], nb)
                    if L > 1e-3:
                        cross.append((cid, a, b, round(float(L), 2), key in allowed))
                    ov = L > 1e-3
            if ov:
                real.add(key)
            if key in share: sk += 1; continue
            if key in allowed: al += 1; continue
            if roles[a] == 'flap' and roles[b] == 'flap': ff += 1; continue
            tested += 1
    vac = len(allowed - real)
    allowed_tot += len(allowed); vac_tot += vac
    tot['all'] += allp; tot['share'] += sk; tot['allowed'] += al; tot['flapflap'] += ff; tot['tested'] += tested
    rows.append((round(tested / allp if allp else 1.0, 4), cid, allp, sk, al, ff, tested, len(allowed), vac))
OUT['g06'] = {'pairs': dict(tot), 'tested_pct': round(100 * tot['tested'] / tot['all'], 2),
              'allowed_entries': allowed_tot, 'allowed_vacuous': vac_tot,
              'allowed_vacuous_pct': round(100 * vac_tot / allowed_tot, 2),
              'least_tested': sorted(rows)[:16], 'robust_crossings': cross}
# 2. crease label orientation vs net-up
ori = defaultdict(list)
for cid in T.all_classes():
    mod, params, ir, world = load(cid)
    net = {p["id"]: np.array(p["polygon_2d"], float) for p in ir.panels}
    up_v = down_v = 0
    for e in ir.edges:
        if e.target_dir_3d is None or e.mt_va != 'VALLEY':
            continue
        Rp = rigid_fit(net[e.parent], world[e.parent])
        up = np.cross(Rp[:, 0], Rp[:, 1]); up /= np.linalg.norm(up)
        z = float((world[e.child].mean(0) - world[e.parent].mean(0)) @ up)
        if z > 1e-6: up_v += 1
        elif z < -1e-6: down_v += 1
    kind = 'mixed' if (up_v and down_v) else ('VALLEY->net-up' if up_v else ('VALLEY->net-down' if down_v else 'no-valley'))
    ori[kind].append(cid)
OUT['crease_orientation'] = {k: {'n': len(v), 'classes': v} for k, v in ori.items()}
# 3. SVG hinge cut lines (rsc_handhole, gable_screw_cap) using HEAD export
num = r'(-?[\d.]+)'
pat = re.compile(r'<line x1="' + num + r'" y1="' + num + r'" x2="' + num + r'" y2="' + num + r'"')
svgchk = {}
for cid in ('rsc_handhole', 'gable_screw_cap', 'pyramid_frustum_n4', 'egg_tray_2x4', 'cup_sleeve'):
    mod, params, ir, world = load(cid)
    x0, y0, x1, y1 = net_bbox(ir)
    svg = svg_render(ir, x1 - x0, y1 - y0)
    i = svg.index('<g id="CUT">'); j = svg.index('</g>', i)
    segs = [tuple(map(float, m)) for m in pat.findall(svg[i:j])]
    P2 = {p['id']: Polygon(p['polygon_2d']).buffer(-1e-6) for p in ir.panels}
    own = {}
    for pid, poly in {p['id']: np.array(p['polygon_2d'], float) for p in ir.panels}.items():
        for k in range(len(poly)):
            own.setdefault(tuple(sorted((tuple(poly[k]), tuple(poly[(k + 1) % len(poly)])))), set()).add(pid)
    inside = {}; onfold = {}
    folds = [(e.id, np.array(e.seg_2d[0]), np.array(e.seg_2d[1])) for e in ir.edges]
    for xa, ya, xb, yb in segs:
        a = np.array([xa - 12.0, ya - 12.0]); b = np.array([xb - 12.0, yb - 12.0])
        L = LineString([a, b])
        o = own.get(tuple(sorted((tuple(a), tuple(b)))), set())
        for q, P in P2.items():
            if q in o:
                continue
            d = L.intersection(P).length
            if d > 1e-6:
                inside[q] = round(inside.get(q, 0.0) + d, 2)
        for eid, fa, fb in folds:
            d = seg_overlap(a, b, fa, fb)
            if d > 1e-6:
                onfold[eid] = round(onfold.get(eid, 0.0) + d, 2)
    svgchk[cid] = {'svg_cut_lines': len(segs), 'cut_inside_panel': inside, 'cut_on_fold': onfold}
OUT['svg_cut_check'] = svgchk
# 4. divided floor validity
mod, params, ir, world = load('divided_tray_3comp')
P = Polygon(ir.panel('floor')['polygon_2d'])
OUT['divided_floor'] = {'is_valid': P.is_valid, 'reason': is_valid_reason(P), 'area': P.area, 'WxD': params['W'] * params['D'],
                        'buffer0_area': P.buffer(0).area}
# 5. validate boundary cases
def trial(cid, ov):
    mod = T.get(cid); params = dict(mod.DEFAULTS)
    if hasattr(mod, 'class_params'): params.update(mod.class_params(cid))
    params.update(ov)
    try:
        raw = mod.build_ir(params); raw.pop('_derived', None); ir = from_raw(raw)
    except Exception as exc:
        return 'REJECT ' + str(exc)[:70]
    try:
        st, rep = qa_status(ir)
    except Exception as exc:
        return 'ERROR ' + repr(exc)[:60]
    return st
cases = [('rsc_rsc', {'flap_ratio': 0.1}), ('rsc_rsc', {'flap_ratio': 0.3}), ('rsc_rsc', {'flap_ratio': 0.95}), ('rsc_rsc', {'flap_ratio': 1.0}),
         ('rsc_hsc', {'flap_ratio': 0.2}), ('rsc_lock', {'flap_ratio': 0.3}),
         ('clv_tuck_insert', {'W': 0.0}), ('clv_tuck_insert', {'W': -50.0}), ('clv_tuck_insert', {'D': -10.0}), ('clv_tuck_insert', {'H': -5.0}),
         ('clv_tuck_insert', {'ins': 60.0}), ('tuck_top_box', {'W': -40.0}), ('tuck_top_box', {'ins': 60.0}), ('two_piece', {'W': 0.0}),
         ('two_piece', {'clear': 0.0}), ('two_piece', {'clear': 50.0}), ('slide_box', {'W': -30.0}), ('window_box', {'W': 0.0}),
         ('gable_top', {'glue_w': 60.0}), ('gable_top', {'fin_gap_mm': 40.0}), ('prism_n4_open', {'glue_w': 200.0}), ('rsc_rsc', {'glue_w': 99.0}),
         ('rsc_rsc', {'board_t': 50.0}), ('envelope_square', {'flap_d': 50.0}), ('envelope_square', {'flap_d': 69.0}),
         ('tube_glue_n8', {'glue_w': 0.1}), ('tray_6corner', {'side': 30.0, 'glue_w': 14.0, 'H': 50.0}), ('crashlock_rect', {'W': 80.0, 'D': 70.0})]
OUT['validate_cases'] = [{'class': c, 'override': o, 'result': trial(c, o)} for c, o in cases]
# 6. module probes
pr = {}
for cid in T.all_classes():
    mod, params, ir, world = load(cid)
    if hasattr(mod, 'probe'):
        try:
            o = mod.probe(ir, fold_all, from_raw)
            pr[cid] = {k: round(float(p), 3) for k, (b, p) in o.items()}
        except Exception as exc:
            pr[cid] = {'error': repr(exc)[:80]}
OUT['module_probe'] = {'n_classes_with_probe': len(pr), 'min_perturbed': min(min(v.values()) for v in pr.values() if 'error' not in v),
                       'max_perturbed': max(max(v.values()) for v in pr.values() if 'error' not in v)}
# 7. core cross-checks
base = {"meta": {"ir_version": "0.1", "units": "mm", "generator": "t", "root_panel": "a", "root_frame": {"R": [[1, 0, 0], [0, 0, 0], [0, 1, 0]], "off": [0, 0, 0]}},
        "package": {"type": "x", "template": {"id": "x", "version": "0.1"}, "params": {}, "photo": None},
        "panels": [{"id": "a", "role": "wall", "polygon_2d": [[0, 0], [10, 0], [10, 10], [0, 10]]}, {"id": "b", "role": "flap", "polygon_2d": [[10, 0], [20, 0], [20, 10], [10, 10]]}],
        "edges": [{"id": "e", "kind": "FOLD", "seg_2d": [[10, 0], [10, 10]], "fold": {"mt_va": "VALLEY", "parent": "a", "child": "b", "target_angle_deg": 90}}], "features": []}
fb = {}
for mt in ("VALLEY", "MOUNTAIN"):
    raw = json.loads(json.dumps(base)); raw["edges"][0]["fold"]["mt_va"] = mt
    fb[mt] = np.round(fold_all(from_raw(raw))['b'].mean(0), 6).tolist()
OUT['fallback_tie'] = {'VALLEY': fb['VALLEY'], 'MOUNTAIN': fb['MOUNTAIN'], 'identical': fb['VALLEY'] == fb['MOUNTAIN']}
mod, params, ir, world = load('gable_top')
from photo_dieline.cli import _layer_geo
OUT['pdf_layers_with_content'] = {k: len(v) for k, v in _layer_geo(ir).items()}
try:
    ir.folds_from('slopeB'); OUT['folds_from'] = 'ok'
except Exception as exc:
    OUT['folds_from'] = repr(exc)[:80]
# 8. degenerate first-triangle classes
deg = []
for cid in T.all_classes():
    mod, params, ir, world = load(cid)
    bad = [pid for pid, v in world.items() if np.linalg.norm(np.cross(v[1] - v[0], v[2] - v[0])) < 1e-7 * max(1e-9, float(np.abs(v).max()))]
    if bad:
        deg.append((cid, len(bad)))
OUT['degen_first_tri'] = deg
json.dump(OUT, open('/tmp/pd_recheck/probe_head/a7.json', 'w'), ensure_ascii=False, indent=1, default=str)
for k, v in OUT.items():
    print(k, ':', json.dumps(v, ensure_ascii=False, default=str)[:900])
