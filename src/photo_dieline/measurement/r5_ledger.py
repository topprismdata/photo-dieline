"""R5 真实数据试验 — 冻结字段台账 (协议 §8) + v0.1-A 参考锚点审计 + 双率汇总。

对应协议: docs/measurement/r5_real_pilot_protocol.md (v0.1) 与
r5_real_pilot_protocol_v0.1-A.md (参考锚点独立性)。调参禁令 (§4) 不在本层 — 本模块只记录与对账。

判据: u_ref = 极差/√3 (§5, GUM 极差法); 接受界 = max(tol, k·u_ref), tol=1mm 冻结。
双率 (R4 收口裁决): R_auto 在 N_auto=0 时为**未定义 (None)**, 禁记 0; MANUAL 与 REJECT 分列。
"""

import json
import math
from pathlib import Path

TOL_MM = 1.0          # 制造容差, 协议 §5 冻结
K_SAFE = 2.0          # 安全系数 (与 delivery_policy 一致)
PROTOCOL_VERSION = "r5-v0.1+v0.1-A"

# v0.1-A 参考锚点九字段 (缺一不可)
ANCHOR_FIELDS = ("anchor_id", "reference_method", "instrument_id", "calibration",
                 "reference_value", "reference_uncertainty", "independence",
                 "correlation", "adjudication")

SPECIMEN_GROUPS = {
    "R01": "标准长方体纸盒 (正常对照: 尺度恢复+重复性)",
    "R02": "标准 gable top 屋顶包 (参数耦合)",
    "R03": "扁平/近退化包装 (弱可辨识 → 预期 MANUAL/OUT_OF_DOMAIN)",
    "R04": "高反光/弱边缘包装 (观测误差敏感性)",
    "R05": "轻微形变实物 (模型失配 → 失配门 rms 行为)",
}


def u_ref(repeats_mm):
    """参考不确定度: 极差/√3 (协议 §5)。要求 ≥3 次重复 (每边 3 次)。"""
    vals = [float(v) for v in repeats_mm if math.isfinite(float(v))]
    if len(vals) < 3:
        raise ValueError(f"u_ref 需 ≥3 次重复, 得到 {len(vals)}")
    return (max(vals) - min(vals)) / math.sqrt(3.0)


def ref_mean(repeats_mm):
    vals = [float(v) for v in repeats_mm]
    return sum(vals) / len(vals)


def compare(measured_mm, repeats_mm, tol_mm=TOL_MM, k=K_SAFE):
    """协议 §5 比较口径: |测得 − 参考| ≤ max(tol, k·u_ref)。
    结论措辞是'与参考测量的一致性', 禁用'精度 X mm' (调用方负责)。"""
    u = u_ref(repeats_mm)
    bound = max(tol_mm, k * u)
    diff = abs(float(measured_mm) - ref_mean(repeats_mm))
    return {"ok": diff <= bound, "diff_mm": diff, "bound_mm": bound,
            "u_ref_mm": u, "tol_mm": tol_mm, "k": k,
            "governing": "tol" if tol_mm >= k * u else "k·u_ref"}


def validate_anchor(rec):
    """v0.1-A 九字段审计。independence 须声明; 共享仪器/基准须在 correlation 里写明相关项。"""
    missing = [f for f in ANCHOR_FIELDS if not str(rec.get(f, "")).strip()]
    out = list(missing)
    if rec.get("independence") == "shared_instrument" and not str(rec.get("correlation", "")).strip():
        pass  # correlation 已在 missing 里覆盖; 保留分支便于未来加严
    return out


def validate_specimen(rec):
    """协议 §8 冻结字段核验。返回问题列表 (空 = 通过)。outputs 允许后补 (采集→求解→产物三段式)。"""
    errs = []
    if not str(rec.get("id", "")).strip():
        errs.append("specimen.id 缺失")
    if rec.get("group") not in SPECIMEN_GROUPS:
        errs.append(f"specimen.group 须为 R01-R05, 得到 {rec.get('group')!r}")
    if not rec.get("status_photo"):
        errs.append("status_photo (状态照片) 缺失")
    obs = rec.get("observations") or []
    if len(obs) < 3:
        errs.append(f"observations 须 ≥3 视角 (协议 §2), 得到 {len(obs)}")
    for i, o in enumerate(obs):
        for f in ("image", "device", "intrinsics"):
            if not str(o.get(f, "")).strip():
                errs.append(f"observations[{i}].{f} 缺失")
    ann = rec.get("annotations") or []
    if len(ann) < 2:
        errs.append("annotations 须 ≥2 名独立标注员 (协议 §3)")
    for i, a in enumerate(ann):
        if not str(a.get("annotator_id", "")).strip():
            errs.append(f"annotations[{i}].annotator_id 缺失")
        if not a.get("independent", False):
            errs.append(f"annotations[{i}].independent 须显式 true (§3 独立性)")
        if not a.get("points_raw"):
            errs.append(f"annotations[{i}].points_raw 缺失 (原始坐标不预处理)")
    ref = rec.get("reference") or {}
    if not str(ref.get("instrument", "")).strip():
        errs.append("reference.instrument 缺失 (真尺型号/分辨率)")
    reps = ref.get("repeats_mm") or {}
    if not isinstance(reps, dict) or not reps:
        errs.append("reference.repeats_mm 须为 {维度: [≥3 次重复值]}")
    else:
        for dim, vals in reps.items():
            try:
                u_ref(vals)
            except (ValueError, TypeError) as e:
                errs.append(f"reference.repeats_mm[{dim}]: {e}")
    for anc in ref.get("anchors") or []:
        miss = validate_anchor(anc)
        if miss:
            errs.append(f"reference.anchors[{anc.get('anchor_id', '?')}] 缺字段: {','.join(miss)}")
    sv = rec.get("solver") or {}
    for f in ("git_sha", "config", "seed"):
        if not str(sv.get(f, "")).strip():
            errs.append(f"solver.{f} 缺失 (§4 冻结求解器字段)")
    ac = rec.get("acceptance") or {}
    if ac.get("tol_mm") != TOL_MM:
        errs.append(f"acceptance.tol_mm 须为 {TOL_MM} (§5 冻结)")
    if str(ac.get("protocol_version", "")).strip() != PROTOCOL_VERSION:
        errs.append(f"acceptance.protocol_version 须为 {PROTOCOL_VERSION}")
    return errs


def dual_rate(records):
    """R4 收口裁决双率: C_auto / R_auto (N_auto=0 → None, 禁记 0) / C_manual; MANUAL≠REJECT。"""
    n = len(records)
    n_auto = sum(1 for r in records if r.get("delivery") == "AUTO")
    n_manual = sum(1 for r in records if r.get("delivery") == "MANUAL")
    n_reject = sum(1 for r in records if r.get("delivery") == "NO_GO")
    n_auto_wrong = sum(1 for r in records
                       if r.get("delivery") == "AUTO" and r.get("auto_wrong") is True)
    return {
        "n_total": n, "n_auto": n_auto, "n_manual": n_manual, "n_reject": n_reject,
        "n_auto_wrong": n_auto_wrong,
        "C_auto": (n_auto / n) if n else None,
        "R_auto": (n_auto_wrong / n_auto) if n_auto else None,  # None = 未定义, 禁 0
        "C_manual": (n_manual / n) if n else None,
        "note": "R_auto=None 表示无 AUTO 样本 (未定义); 目标是风险上限内最大化 C_auto",
    }


def session_summary(dirpath):
    """目录内全部 specimen JSON → 校验 + 双率汇总 (delivery 取 outputs.delivery)。"""
    recs, problems = [], {}
    for p in sorted(Path(dirpath).glob("*.json")):
        try:
            rec = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            problems[p.name] = [f"JSON 解析失败: {e}"]
            continue
        errs = validate_specimen(rec)
        if errs:
            problems[p.name] = errs
            continue
        recs.append({"id": rec["id"], "delivery": (rec.get("outputs") or {}).get("delivery"),
                     "auto_wrong": (rec.get("outputs") or {}).get("auto_wrong")})
    return {"records": recs, "rates": dual_rate(recs), "problems": problems}


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("用法: python -m photo_dieline.measurement.r5_ledger <specimens 目录>")
        raise SystemExit(2)
    rep = session_summary(sys.argv[1])
    print(json.dumps(rep, ensure_ascii=False, indent=2))
