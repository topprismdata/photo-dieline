"""参数化测量 (B0): 已标注关键点 + 已知内参 + 可选实测尺寸 → 投影几何联合拟合包装参数与相机位姿。

重依赖 (scipy 求解; trimesh 仅可见性剔除) 走可选 extras: `pip install photo-dieline[measure]`。
实验证据与生成/求解两端投影对账 (最大差 0.004px) 见 docs/reviews/recheck_2026-11-24/evidence/b0/。
"""
from . import calibration, r5_ledger  # noqa: F401  (R5 真实数据试验: 标定+台账)
from .solve import (  # noqa: F401
    MODELS, REL, RES, back_dir, basis, capture_protocol_check, cross_view_closure, cuboid_faces,
    cuboid_keypoints, delivery_policy, eye_pos, gable_faces, gable_keypoints, observe, project,
    ratio_mae, solve, to_world, visible,
)

__all__ = [
    "MODELS", "REL", "RES", "back_dir", "basis", "capture_protocol_check", "cross_view_closure",
    "cuboid_faces", "cuboid_keypoints", "delivery_policy", "eye_pos", "gable_faces",
    "gable_keypoints", "observe", "project", "ratio_mae", "solve", "to_world", "visible",
]
