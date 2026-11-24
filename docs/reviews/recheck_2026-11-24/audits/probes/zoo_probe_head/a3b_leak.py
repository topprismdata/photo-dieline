import json, sys
import numpy as np
sys.path.insert(0, "/tmp/pd_recheck/probe_head")
from common import *
res = {}
for cid in T.all_classes():
    mod, params, ir, world = load(cid)
    res[cid] = leak(world, N=12)
json.dump(res, open("/tmp/pd_recheck/probe_head/a3b.json", "w"), ensure_ascii=False, indent=1, default=str)
for cid, L in res.items():
    if L is None:
        print(f"  {cid}: FLAT"); continue
    if L["n_interior"] == 0:
        print(f"  {cid}: no interior (odd_hist={L['odd_hist']})"); continue
    lk = np.array(L["leak"])
    ax = lk[[4, 22, 10, 16, 12, 14]]  # (-x,+x,-y,+y,-z,+z)
    print(f"  {cid}: n={L['n_interior']} leak_any={L['leak_any']} max={lk.max():.2f} mean={lk.mean():.3f} axis(-x,+x,-y,+y,-z,+z)={np.round(ax,2).tolist()} ndir_leak>5%={int((lk>0.05).sum())}")
