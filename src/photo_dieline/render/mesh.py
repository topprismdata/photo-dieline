"""折叠孪生网格导出 (OBJ): fold_all 世界坐标 → Blender 可导入.

面板平面的多边形 (四/五边) 扇形三角化; 每面板一个 object (g 组),
材质按角色分 (wall/slope/fin/flap/glue) 供渲染端着色与消融实验。
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..folding.engine import fold_all
from ..core.ir import GeometryIR

ROLE_COLOR = {
    "wall": (0.88, 0.88, 0.90), "slope": (0.86, 0.86, 0.89), "fin": (0.80, 0.80, 0.84),
    "flap": (0.78, 0.78, 0.82), "glue": (0.76, 0.76, 0.79), "gable_end": (0.88, 0.88, 0.90),
}


def export_obj(ir: GeometryIR, out_path: str | Path) -> dict:
    """写 OBJ (mm 单位, 1:1). 返回 bbox 与面板数."""
    world = fold_all(ir)
    roles = {p["id"]: p["role"] for p in ir.panels}
    lines = ["# photo-dieline TDE folded twin (mm)"]
    materials = sorted({roles[pid] for pid in world})
    for m in materials:
        c = ROLE_COLOR.get(m, (0.85, 0.85, 0.87))
        lines.append(f"usemtl {m}")
        # mtl 在伴生文件; OBJ 内引用名字即可 (driver 端重建材质)
    offset = 1
    all_pts = []
    for pid, verts in world.items():
        lines.append(f"o {pid}")
        v = np.asarray(verts, float)
        for pt in v:
            lines.append(f"v {pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f}")
        n = len(v)
        for k in range(1, n - 1):  # 扇形三角化 (凸面板; 凹面板渲染可接受)
            lines.append(f"f {offset} {offset + k} {offset + k + 1}")
        all_pts.append(v)
        offset += n
    Path(out_path).write_text("\n".join(lines))
    allp = np.vstack(all_pts)
    return {"bbox_min": allp.min(0).round(3).tolist(),
            "bbox_max": allp.max(0).round(3).tolist(),
            "panels": len(world),
            "materials": materials}
