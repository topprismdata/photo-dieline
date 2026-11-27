"""R09-11 G1-02 门禁薄别名 (实际实现在 src/photo_dieline/export/usd.py)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from photo_dieline.export.usd import _orientation_normalize_safe  # noqa: F401
