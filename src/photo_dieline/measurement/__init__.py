"""参数化测量 (B0): 已标注关键点 + 已知内参 + 可选实测尺寸 → 投影几何联合拟合包装参数与相机位姿。

重依赖 (scipy 求解; trimesh 仅可见性剔除) 走可选 extras: `pip install photo-dieline[measure]`。
实验证据与生成/求解两端投影对账 (最大差 0.004px) 见 docs/reviews/recheck_2026-11-24/evidence/b0/。
"""
from .solve import (  # noqa: F401
    MODELS, REL, RES, back_dir, basis, cuboid_faces, cuboid_keypoints, eye_pos,
    gable_faces, gable_keypoints, observe, project, ratio_mae, solve, to_world, visible,
)

__all__ = [
    "MODELS", "REL", "RES", "back_dir", "basis", "cuboid_faces", "cuboid_keypoints",
    "eye_pos", "gable_faces", "gable_keypoints", "observe", "project", "ratio_mae",
    "solve", "to_world", "visible",
]
