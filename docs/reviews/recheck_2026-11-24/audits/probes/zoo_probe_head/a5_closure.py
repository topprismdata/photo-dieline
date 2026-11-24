import json, sys, copy
import numpy as np
sys.path.insert(0, "/tmp/pd_recheck/probe_head")
from common import *
TOLQ = 0.2
out = {}
for cid in T.all_classes():
    mod, params, ir, world = load(cid)
    base = {k: float(v) for k, v in mod.closure_checks(ir, world).items()}
    chk_move = {k: 0.0 for k in base}
    edges = list(ir.edges)
    net = {p["id"]: np.array(p["polygon_2d"], float) for p in ir.panels}
    und35 = []; und180 = []; n_ok = 0
    for e in edges:
        if e.target_dir_3d is None:
            continue
        n_ok += 1
        try:
            R = rigid_fit(net[e.parent], world[e.parent])
        except Exception:
            R = None
        res35 = 0.0; res180 = 0.0
        for ang, acc in ((math.radians(35.0), "35"), (math.radians(-35.0), "35"), (math.pi, "180")):
            raw = copy.deepcopy(ir.raw)
            for re in raw["edges"]:
                if re["id"] == e.id:
                    t = np.array(re["fold"]["target_dir_3d"], float)
                    if R is None:
                        break
                    axis = R @ (np.array(e.seg_2d[1]) - np.array(e.seg_2d[0]))
                    tp = rot_axis(t, axis, ang)
                    re["fold"]["target_dir_3d"] = [float(v) for v in tp / np.linalg.norm(tp)]
                    break
            else:
                pass
            try:
                irp = from_raw(raw)
                wp = fold_all(irp)
                resp = {k: float(v) for k, v in mod.closure_checks(irp, wp).items()}
                worst = max(resp.values())
                for k in chk_move:
                    if k in resp:
                        chk_move[k] = max(chk_move[k], abs(resp[k] - base[k]))
            except Exception as exc:
                worst = 1e9
            if acc == "35":
                res35 = max(res35, worst)
            else:
                res180 = max(res180, worst)
        if res35 <= TOLQ:
            und35.append(e.id)
        if res180 <= TOLQ:
            und180.append(e.id)
    frozen = [k for k, v in chk_move.items() if v < 1e-3]
    out[cid] = {"n_checks": len(base), "n_edges": len(edges), "n_tdir": n_ok,
                "und35": und35, "und180": und180, "frozen_checks": frozen,
                "base_max": max(base.values())}
json.dump(out, open("/tmp/pd_recheck/probe_head/a5.json", "w"), ensure_ascii=False, indent=1)
print("class | edges | undetected@±35° | undetected@180° | frozen checks (never move under single-fold perturbation)")
for cid, r in out.items():
    print(f"{cid} | {r['n_edges']} | {len(r['und35'])}{'' if not r['und35'] else ' '+','.join(r['und35'])} | {len(r['und180'])}{'' if not r['und180'] else ' '+','.join(r['und180'])} | {len(r['frozen_checks'])}/{r['n_checks']} {r['frozen_checks'][:8]}")
