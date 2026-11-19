"""纯 Python 折叠引擎: 展开网 → 3D 刚体折叠 (numpy, 无 Blender, 可 CI).

模型: 每面板维护 (R, off) — world = R @ [net_x, net_y, 0] + off.
根面板 wallL 直接放在封闭盒位姿 (x=-W/2 平面); 其余按 FOLD 边 BFS:
  轴 = 父帧下折线方向; 子面板先按父帧(展开延续)落位, 再绕轴旋转使
  子面板 away 方向到达 target_dir_3d (显式定向) 或按 mt_va+角度折叠
  (VALLEY 折向父质心侧, MOUNTAIN 折离)。
"""
from __future__ import annotations

import math

import numpy as np

from ..core.ir import ARError, GeometryIR

ROOT_PANEL = "wallL"


def _norm(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise ARError("零向量")
    return v / n


def _rot(axis: np.ndarray, ang: float) -> np.ndarray:
    """Rodrigues 旋转矩阵."""
    x, y, z = _norm(axis)
    K = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
    c, s = math.cos(ang), math.sin(ang)
    return np.eye(3) + s * K + (1.0 - c) * (K @ K)


def _away_net(poly: np.ndarray, seg: tuple) -> np.ndarray:
    """面板质心相对折线的垂直方向 (net 2D → 3D z=0)."""
    a, b = np.asarray(seg[0], float), np.asarray(seg[1], float)
    e = _norm(b - a)
    c = poly.mean(axis=0)
    v = c - (a + b) / 2.0
    away = v - (v @ e) * e
    return np.array([*(_norm(away)), 0.0])


def _pc_net(parent_poly: np.ndarray, seg: tuple) -> np.ndarray:
    """父质心相对折线的垂直方向 (net 2D → 3D z=0)."""
    return _away_net(parent_poly, seg)


def _net3(poly: np.ndarray) -> np.ndarray:
    return np.column_stack([poly, np.zeros(len(poly))])


def fold_all(ir: GeometryIR) -> dict[str, np.ndarray]:
    """返回 panel_id → (N,3) 世界顶点 (与 polygon_2d 顶点一一对应)."""
    polys = {p["id"]: np.array(p["polygon_2d"], float) for p in ir.panels}
    meta = getattr(ir, "raw", {}).get("meta", {}) if hasattr(ir, "raw") else {}
    root_id = meta.get("root_panel", ROOT_PANEL)
    if root_id not in polys:
        raise ARError(f"根面板 {root_id} 不在模板中")

    # 根面板位姿: 模板声明 root_frame 优先; 缺省回退 gable 旧映射 (M1 合同)
    root_poly = polys[root_id]
    rf = meta.get("root_frame")
    if rf:
        R0 = np.array(rf["R"], float)
        off0 = np.array(rf["off"], float)
    else:
        x1 = root_poly[:, 0].min()
        R0 = np.array([[0.0, 0.0, 0.0],
                       [1.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0]])
        off0 = np.array([-ir.param("W") / 2.0, -x1, 0.0])
    frames: dict[str, tuple[np.ndarray, np.ndarray]] = {root_id: (R0, off0)}
    world: dict[str, np.ndarray] = {root_id: _net3(root_poly) @ R0.T + off0}

    edges = list(ir.edges)
    while edges:
        progressed = False
        for e in list(edges):
            if e.child in frames:
                edges.remove(e)
                continue
            if e.parent not in frames:
                continue
            Rp, offp = frames[e.parent]
            a_net = np.array([*e.seg_2d[0], 0.0])
            axis = _norm(Rp @ (np.array([*e.seg_2d[1], 0.0]) - a_net))
            origin = Rp @ a_net + offp
            away_world = _norm(Rp @ _away_net(polys[e.child], e.seg_2d))

            if e.target_dir_3d is not None:
                tgt = _norm(np.asarray(e.target_dir_3d, float))
            else:
                interior = math.radians(e.target_angle_deg or 90.0)
                delta = math.pi - interior
                pc_world = _norm(Rp @ _pc_net(polys[e.parent], e.seg_2d))
                cand = []
                for sign in (+1.0, -1.0):
                    d = _rot(axis, sign * delta) @ away_world
                    cand.append((float(d @ pc_world), d))
                want_positive = e.mt_va == "VALLEY"
                cand.sort(key=lambda t: t[0], reverse=want_positive)
                tgt = cand[0][1]
            try:
                R_axis = _rotation_from_to(away_world, tgt, axis)
            except ARError as exc:
                raise ARError(f"{e.id}: away={away_world.round(3).tolist()} "
                              f"tgt={tgt.round(3).tolist()} axis={axis.round(3).tolist()}: {exc}") from None
            Rc = R_axis @ Rp
            offc = origin - Rc @ a_net
            frames[e.child] = (Rc, offc)
            world[e.child] = _net3(polys[e.child]) @ Rc.T + offc
            placed_ok = np.all(np.isfinite(world[e.child]))
            if not placed_ok:
                raise ARError(f"折叠产生非有限坐标: {e.child}")
            edges.remove(e)
            progressed = True
        if not progressed:
            raise ARError(f"折叠树断裂: {[e.id for e in edges]}")
    return world


def _rotation_from_to(v_from: np.ndarray, v_to: np.ndarray, axis: np.ndarray) -> np.ndarray:
    """绕 axis 将 v_from 转到 v_to 的旋转 (v 先投影到轴垂直面)."""
    axis = _norm(axis)
    f = v_from - (v_from @ axis) * axis
    t = v_to - (v_to @ axis) * axis
    f, t = _norm(f), _norm(t)
    c = float(f @ t)
    cross = np.cross(f, t)
    if np.linalg.norm(cross) < 1e-12:
        return np.eye(3) if c > 0 else _rot(axis, math.pi)
    return _rot(axis, math.atan2(float(np.dot(cross, axis)), c))
