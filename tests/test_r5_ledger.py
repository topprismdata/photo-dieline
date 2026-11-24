"""R5 台账与标定自检测试 — 协议 §5/§8 + v0.1-A 九字段 + 双率 None 语义 + 标定正控制。"""

import math

import pytest

from photo_dieline.measurement import calibration, r5_ledger as L


# --- u_ref / compare (协议 §5) ---

def test_u_ref_formula():
    assert L.u_ref([100.0, 100.5, 100.2]) == pytest.approx(0.5 / math.sqrt(3.0))
    with pytest.raises(ValueError):
        L.u_ref([100.0, 100.0])  # 须 ≥3 次重复


def test_compare_tol_and_ku_ref_governing():
    # tol 主导: u_ref 极小 → bound = 1mm; 差 1.6mm > tol → 拒
    r = L.compare(101.6, [100.0, 100.0, 100.0])
    assert r["ok"] is False and r["governing"] == "tol" and r["bound_mm"] == 1.0
    assert L.compare(100.9, [100.0, 100.0, 100.0])["ok"] is True
    # k·u_ref 主导: 重复测量差 3mm → bound = 2·(3/√3) ≈ 3.46mm
    r2 = L.compare(103.0, [100.0, 101.0, 103.0])
    assert r2["governing"] == "k·u_ref"
    assert r2["bound_mm"] == pytest.approx(2.0 * 3.0 / math.sqrt(3.0))
    assert r2["ok"] is True


# --- v0.1-A 锚点九字段 ---

def _anchor(**over):
    base = {f: "x" for f in L.ANCHOR_FIELDS}
    base.update(anchor_id="A1", independence="independent", correlation="none",
                adjudication="ref值冲突→重测3次取中位")
    base.update(over)
    return base


def test_anchor_complete_passes():
    assert L.validate_anchor(_anchor()) == []


def test_anchor_missing_and_shared_requires_correlation():
    miss = L.validate_anchor({k: v for k, v in _anchor().items() if k != "calibration"})
    assert "calibration" in miss
    shared = _anchor(independence="shared_instrument", correlation="")
    assert "correlation" in L.validate_anchor(shared)


# --- specimen 冻结字段 (§8) ---

def _specimen(**over):
    rec = {
        "id": "R01-01", "group": "R01", "status_photo": "photos/r01/status.jpg",
        "observations": [{"image": f"img{i}.jpg", "device": "iPhone15", "intrinsics": "sess1_K.json"}
                         for i in range(3)],
        "annotations": [{"annotator_id": "A", "independent": True, "points_raw": [[1, 2]]},
                        {"annotator_id": "B", "independent": True, "points_raw": [[1, 2]]}],
        "reference": {"instrument": "卡尺 0.02mm", "repeats_mm": {"W": [80.0, 80.1, 80.0]},
                      "anchors": [_anchor()]},
        "solver": {"git_sha": "d7c1764", "config": "r4-baseline", "seed": 0},
        "acceptance": {"tol_mm": 1.0, "protocol_version": L.PROTOCOL_VERSION},
        "outputs": {},
    }
    rec.update(over)
    return rec


def test_specimen_valid():
    assert L.validate_specimen(_specimen()) == []


def test_specimen_rejections():
    assert any("independent" in e for e in L.validate_specimen(_specimen(
        annotations=[{"annotator_id": "A", "independent": False, "points_raw": [[0, 0]]}] * 2)))
    assert any("≥3 视角" in e for e in L.validate_specimen(_specimen(observations=[])))
    bad_ref = _specimen()
    bad_ref["reference"]["repeats_mm"]["W"] = [80.0]
    assert any("repeats_mm[W]" in e for e in L.validate_specimen(bad_ref))
    bad_anchor = _specimen()
    bad_anchor["reference"]["anchors"] = [{"anchor_id": "A1"}]
    assert any("缺字段" in e for e in L.validate_specimen(bad_anchor))
    wrong_tol = _specimen(acceptance={"tol_mm": 0.5, "protocol_version": L.PROTOCOL_VERSION})
    assert any("tol_mm" in e for e in L.validate_specimen(wrong_tol))


# --- 双率 (R4 收口裁决语义) ---

def test_dual_rate_undefined_r_auto_not_zero():
    recs = [{"delivery": "MANUAL"}, {"delivery": "MANUAL"}, {"delivery": "NO_GO"}]
    r = L.dual_rate(recs)
    assert r["R_auto"] is None and r["n_auto"] == 0          # 未定义, 禁 0
    assert r["C_manual"] == pytest.approx(2 / 3)
    assert r["n_manual"] == 2 and r["n_reject"] == 1          # MANUAL≠REJECT 分列


def test_dual_rate_with_auto_errors():
    recs = [{"delivery": "AUTO", "auto_wrong": True}, {"delivery": "AUTO"},
            {"delivery": "MANUAL"}, {"delivery": "NO_GO"}]
    r = L.dual_rate(recs)
    assert r["C_auto"] == 0.5 and r["R_auto"] == 0.5 and r["C_manual"] == 0.25
    assert r["n_auto_wrong"] == 1


# --- 标定正控制 (机器验证: 恢复正确盆, 非精度承诺) ---

def test_calibration_selfcheck():
    r = calibration.selfcheck()
    assert r["ok"], f"正控制失败: {r}"
    assert r["rms_px"] < 1.0 and r["fx_rel_err"] < 0.01
