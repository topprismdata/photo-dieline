"""PD-Guardrails GA 门槛: 历史事故必须能被对应测试重新触发 (GPT 判决)."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GUARD = [sys.executable, str(ROOT / "scripts" / "pd_guard.py")]


def run(*a):
    return subprocess.run(GUARD + list(a), capture_output=True, text=True)


def test_units_catches_camera_85m():
    """历史事故 A1: d_fill×1000 → 相机 85m 外."""
    payload = {"camera": {"distance_m": 85.19, "equiv_focal_mm": 28.0, "pitch_deg": 5.0,
                           "yaw_deg": -30.0}, "params_gt": {"Hb": 119.0}}
    p = Path("/tmp/guard_units_85m.json")
    p.write_text(json.dumps(payload))
    r = run("units", "--payload", str(p))
    assert r.returncode == 1
    assert "85.19" in r.stdout


def test_units_passes_normal_payload():
    payload = {"camera": {"distance_m": 0.25, "equiv_focal_mm": 50.0, "pitch_deg": 20.0,
                           "yaw_deg": -30.0}, "params_gt": {"Hb": 119.0}}
    p = Path("/tmp/guard_units_ok.json")
    p.write_text(json.dumps(payload))
    r = run("units", "--payload", str(p))
    assert r.returncode == 0, r.stdout


def test_artifact_catches_empty_scene():
    """历史事故 B3: 有图无盒 (平滑渐变地面+背景)."""
    im = np.zeros((384, 384, 3), np.uint8)
    for y in range(384):
        im[y, :] = [int(60 + y / 384 * 60)] * 3
    Image.fromarray(im).save("/tmp/guard_empty.png")
    r = run("artifact", "--image", "/tmp/guard_empty.png")
    assert r.returncode == 1


def test_artifact_passes_box_render():
    """已知好图 (内联合成屋顶包校准件) 必须不误拦 (GA 门槛 3: 合法样本不误杀).

    历史教训: 旧版引用本地 /tmp/e3r_r_dist.png, CI 无此文件炸门禁 — 夹具必须内联自足.
    合成物对齐真实校准件结构: 均匀灰背景 + 居中蓝灰盒体(+顶肩) + 淡接触阴影.
    """
    im = np.full((384, 384, 3), 150, np.uint8)
    # 淡阴影 (与背景差 <45: 不计入主体, 只提供真实感)
    im[300:316, 130:280] = 138
    # 盒体: 居中矩形+顶肩, 与背景逐像素通道和差 ≈65 >50 (可分离度)
    im[90:300, 150:262] = (115, 135, 165)
    im[64:90, 170:242] = (118, 138, 168)
    Image.fromarray(im).save("/tmp/guard_box_ok.png")
    r = run("artifact", "--image", "/tmp/guard_box_ok.png")
    assert r.returncode == 0, r.stdout


def test_numeric_catches_nan():
    np.savez("/tmp/guard_pred.npz", ratios=np.array([0.5, np.nan, 0.2]))
    r = run("numeric", "--input", "/tmp/guard_pred.npz")
    assert r.returncode == 1


def test_family_catches_lock_violation():
    """历史事故 E3: 抖动破坏 H=Hf+D 锁定约束."""
    spec = {"params": {"H": 120.0, "Hf": 70.0, "D": 40.0}}  # 120 != 110
    p = Path("/tmp/guard_family.json")
    p.write_text(json.dumps(spec))
    r = run("family", "--spec", str(p), "--rule", "H=Hf+D")
    assert r.returncode == 1


def test_family_passes_valid():
    spec = {"params": {"H": 110.0, "Hf": 70.0, "D": 40.0}}
    p = Path("/tmp/guard_family_ok.json")
    p.write_text(json.dumps(spec))
    r = run("family", "--spec", str(p), "--rule", "H=Hf+D")
    assert r.returncode == 0


# ---- R3 (I/J/M + Release Gate) ----
def _r3(*a):
    return subprocess.run([sys.executable, "scripts/pd_guard_r3.py", *a],
                          capture_output=True, text=True)


def test_r3_pairs_catches_missing_frame(tmp_path):
    rd = tmp_path / "r"; rd.mkdir()
    (rd / "s_0.png").write_bytes(b"x")
    assert _r3("pairs", "--render-dir", str(rd)).returncode == 1  # 无JSON


def test_r3_dieline_catches_open_contour_and_no_strip(tmp_path):
    p = tmp_path / "d.json"
    p.write_text(json.dumps({"polygons": [{"material": "CUT", "points": [[0, 0], [1, 0]]}],
                             "H_mm": 10, "Hf_mm": 6, "D_mm": 4}))
    assert _r3("dieline", "--spec", str(p)).returncode == 1  # 未闭合+无校验条


def test_r3_dieline_passes_valid(tmp_path):
    p = tmp_path / "d.json"
    p.write_text(json.dumps({"polygons": [{"material": "CREASE", "points": [[0, 0], [1, 0], [1, 1], [0, 0]]}],
                             "params": {"H": 112, "Hb": 100, "Hr": 12},
                             "calibration_strip_mm": 50}))
    assert _r3("dieline", "--spec", str(p)).returncode == 0


def test_r3_license_catches_missing_notice(tmp_path):
    mp = tmp_path / "m.json"; zd = tmp_path / "z"; zd.mkdir()
    mp.write_text(json.dumps([{"key": "tin_can", "license": "CC-BY", "source_url": "https://x"}]))
    assert _r3("license", "--manifest", str(mp), "--zoo-dir", str(zd)).returncode == 1  # lic 文件缺


def test_r3_svg_strip_measured(tmp_path):
    svg = ('<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="120.000mm" '
           'height="80.000mm" viewBox="0 0 120 80">\n<g id="INFO">'
           '<line x1="10.000" y1="8.000" x2="60.000" y2="8.000" stroke="#111"/>'
           '<text> CHECK BAR = 50 mm</text></g>\n</svg>')
    p = tmp_path / "d.svg"; p.write_text(svg)
    assert _r3("dieline", "--svg", str(p)).returncode == 0


def test_r3_svg_catches_wrong_strip(tmp_path):
    svg = ('<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="120.000mm" '
           'height="80.000mm" viewBox="0 0 120 80">\n<g id="INFO">'
           '<line x1="10.000" y1="8.000" x2="50.000" y2="8.000" stroke="#111"/>'
           '<text> CHECK BAR = 50 mm</text></g>\n</svg>')
    p = tmp_path / "d.svg"; p.write_text(svg)
    assert _r3("dieline", "--svg", str(p)).returncode == 1  # 条只有 40mm
