"""只读探针公共库 (仓外, 不改仓内文件)."""
import math, warnings, itertools
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely import contains_xy
from photo_dieline.parametric import base as T
from photo_dieline.core.ir import from_raw
from photo_dieline.folding.engine import fold_all
from photo_dieline.export.svg import cut_segments, render as svg_render, net_bbox
from photo_dieline.export.pdf import build_pdf
from photo_dieline.qa.pipeline import run_qa, ALLOWED_OVERLAP
warnings.filterwarnings("ignore")

TOL = 1e-6


def load(cid, override=None):
    mod = T.get(cid)
    params = dict(mod.DEFAULTS)
    if hasattr(mod, "class_params"):
        params.update(mod.class_params(cid))
    if override:
        params.update(override)
    raw = mod.build_ir(params)
    raw.pop("_derived", None)
    ir = from_raw(raw)
    return mod, params, ir, fold_all(ir)


def qa(ir):
    x0, y0, x1, y1 = net_bbox(ir)
    svg = svg_render(ir, x1 - x0, y1 - y0)
    from photo_dieline.cli import _layer_geo
    pdf = build_pdf(ir, x1 - x0, y1 - y0, _layer_geo(ir))
    return run_qa(ir, svg, pdf)


def qa_status(ir):
    try:
        rep = qa(ir)
    except Exception as exc:  # noqa
        return "ERROR", str(exc)[:80]
    bad = [g["id"] for g in rep["gates"] if g["id"] != "G01" and g["status"] != "PASS"]
    return ("GREEN" if not bad else "FAIL:" + ",".join(bad)), rep


def plane_normal(v):
    v = np.asarray(v, float)
    c = v.mean(0)
    s = np.linalg.svd(v - c, compute_uv=False)
    if s[0] < 1e-9:
        return None, s
    _, _, vt = np.linalg.svd(v - c)
    return vt[2], s


def frame(n):
    n = n / np.linalg.norm(n)
    t = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(n, t); u /= np.linalg.norm(u)
    w = np.cross(n, u)
    return u, w


def to2d(v, n):
    u, w = frame(n)
    return np.column_stack([v @ u, v @ w])


def coplanar(va, na, vb, nb, tol=1e-3):
    if abs(float(na @ nb)) < 1 - 1e-7:
        return False
    d = np.abs((vb - va[0]) @ na)
    return float(d.max()) < tol


def seg_overlap(a0, a1, b0, b1, tol=1e-7):
    """共线 (或近共线) 线段重叠长度; 不共线返回 -1."""
    d = a1 - a0
    L = float(np.linalg.norm(d))
    if L < tol:
        return 0.0
    d = d / L
    e = b1 - b0
    if abs(float(e[0] * d[1] - e[1] * d[0])) > 1e-6 * max(1.0, float(np.linalg.norm(e))):
        return -1.0
    off = (b0 - a0) - float((b0 - a0) @ d) * d
    if float(np.linalg.norm(off)) > 1e-6:
        return -1.0
    t0 = float((b0 - a0) @ d); t1 = float((b1 - a0) @ d)
    lo, hi = max(0.0, min(t0, t1)), min(L, max(t0, t1))
    return max(0.0, hi - lo)


def cross_len(va, na, vb, nb):
    """非共面两平面多边形的交线重叠长度 (robust 穿越检测)."""
    da = (vb - va[0]) @ na
    db = (va - vb[0]) @ nb
    scale = max(1e-9, float(np.abs(va).max()), float(np.abs(vb).max()))
    tol = 1e-7 * scale
    if (np.abs(da) <= tol).any() or (np.abs(db) <= tol).any():
        return 0.0  # 顶点落在对方平面上 (沿棱相接), 非穿越

    def pts(P, d):
        out = []
        n = len(P)
        for i in range(n):
            j = (i + 1) % n
            if (d[i] > 1e-9 and d[j] < -1e-9) or (d[i] < -1e-9 and d[j] > 1e-9):
                t = d[i] / (d[i] - d[j])
                out.append(P[i] + t * (P[j] - P[i]))
        return np.array(out) if out else np.zeros((0, 3))

    A = pts(va, db)
    B = pts(vb, da)
    if len(A) == 0 or len(B) == 0:
        return 0.0
    d = np.cross(na, nb)
    d /= np.linalg.norm(d)
    ta = A @ d; tb = B @ d
    lo = max(ta.min(), tb.min()); hi = min(ta.max(), tb.max())
    return max(0.0, float(hi - lo))


def rigid_fit(net, wor):
    X = np.column_stack([np.asarray(net, float), np.ones(len(net))])
    A, *_ = np.linalg.lstsq(X, np.asarray(wor, float), rcond=None)
    return A[:2, :].T  # R (3x2): world = R@net + off


def rot_axis(v, axis, ang):
    axis = axis / np.linalg.norm(axis)
    k = np.asarray(v, float)
    return (k * math.cos(ang) + np.cross(axis, k) * math.sin(ang)
            + axis * float(axis @ k) * (1.0 - math.cos(ang)))


def leak(world, N=14, ndir=26):
    """射线奇偶 watertight 探针: 26 个轴向/对角方向, 共面叠层按一次穿越计.
    返回 leak[d] = 内部网格点中该方向射线穿越数为偶 (透视) 的比例."""
    panels = [(pid, np.asarray(v, float)) for pid, v in world.items()]
    allp = np.vstack([v for _, v in panels])
    lo, hi = allp.min(0), allp.max(0)
    ext = hi - lo
    if ext.min() < 1e-6:
        return None
    fr = (np.arange(N) + 0.3819660113) / N
    pts = np.array(list(itertools.product(*[lo[i] + fr * ext[i] for i in range(3)])))
    dirs = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if (dx, dy, dz) != (0, 0, 0):
                    v = np.array([dx, dy, dz], float)
                    dirs.append(v / np.linalg.norm(v))
    scale = float(ext.max())
    npts = len(pts)
    parity = np.zeros((len(dirs), npts), dtype=int)
    preps = []
    for pid, v in panels:
        n, s = plane_normal(v)
        if n is None:
            continue
        preps.append((v.mean(0), n, Polygon(np.column_stack([v @ frame(n)[0], v @ frame(n)[1]]))))
    for di, d in enumerate(dirs):
        hits_p = []; hits_t = []
        for c, n, poly in preps:
            nd = float(n @ d)
            if abs(nd) < 1e-9:
                continue
            t = ((c - pts) @ n) / nd  # (npts,)
            ok = t > 1e-7 * scale
            idx = np.where(ok)[0]
            if len(idx) == 0:
                continue
            q = pts[idx] + t[idx, None] * d[None, :]
            u, w = frame(n)
            inside = contains_xy(poly, q @ u, q @ w)
            sel = idx[inside]
            if len(sel):
                hits_p.append(sel); hits_t.append(t[sel])
        if not hits_p:
            continue
        hp = np.concatenate(hits_p); ht = np.concatenate(hits_t)
        order = np.lexsort((ht, hp))
        hp = hp[order]; ht = ht[order]
        new_cluster = np.ones(len(hp), dtype=bool)
        new_cluster[1:] = (hp[1:] != hp[:-1]) | (ht[1:] - ht[:-1] > 1e-4 * scale)
        cl = np.cumsum(new_cluster) - 1
        cnt = np.bincount(cl)
        pc = np.bincount(hp, minlength=npts)  # hits per point
        first_idx = np.where(new_cluster)[0]
        cl_pid = hp[first_idx]
        ncl = np.bincount(cl_pid, minlength=npts)
        parity[di] = ncl % 2
    n_odd = parity.sum(0)
    nd = len(dirs)
    inter = n_odd > nd // 2
    if inter.sum() == 0:
        return {"n_interior": 0, "leak": None, "odd_hist": np.bincount(n_odd, minlength=nd + 1).tolist()}
    leakf = (1 - parity[:, inter]).mean(1)
    return {"n_interior": int(inter.sum()), "n_pts": npts, "n_dirs": nd,
            "leak": [round(float(x), 3) for x in leakf],
            "leak_any": round(float(((1 - parity[:, inter]).sum(0) > 0).mean()), 3),
            "odd_hist": np.bincount(n_odd, minlength=nd + 1).tolist()}
