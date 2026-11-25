#!/usr/bin/env python3
"""NV960: NVIDIA 480 零售资产全量独立 V-gate 审计 (路径键控).
复用 usdcraft_1v1_audit.mesh_checks (V1-V7 同判)。
输入: /tmp/nv960/usdc/*_physx_model.usdc + *_physx_model.json + /tmp/nv960/packjson/*.pkg.json
输出: docs/reviews/nv960_audit480.json {path: {full_pass, v2..v7}}
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from usdcraft_1v1_audit import mesh_checks, sidecar_ok, read_declared  # noqa: E402

USDC_DIR = Path("/tmp/nv960/usdc")
PKG_DIR = Path("/tmp/nv960/packjson")
OUT = Path(__file__).resolve().parent.parent / "docs/reviews/nv960_audit480.json"


def main():
    rows = {}
    usdcs = sorted(USDC_DIR.glob("*_physx_model.usdc"))
    print(f"审计 {len(usdcs)} usdc", flush=True)
    for u in usdcs:
        base = u.name.replace("_physx_model.usdc", "")
        rel = base.replace("_", "/", 1)  # kitchen_dining/R026_... 需两段: domain/R/variant
        # 名称: kitchen_dining_R026_bread_box_01_wooden_...  → rigid/kitchen_dining/R026.../<variant>
        mj_p = USDC_DIR / f"{base}_physx_model.json"
        pkg_p = PKG_DIR / f"rigid_{base}.pkg.json"
        declared_ext, declared_mass = None, None
        if mj_p.exists():
            try:
                declared_ext, declared_mass = read_declared(json.loads(mj_p.read_text()))
            except Exception:
                pass
        res = mesh_checks(u, declared_ext, declared_mass)
        res["v7_sidecar"] = sidecar_ok(pkg_p) if pkg_p.exists() else False
        full = all(res.get(k) for k in ("usd", "v2_manifold", "v3_clean", "v4_finite",
                                        "v5_dims", "v6_mass", "v7_sidecar"))
        rows[base] = {k: res.get(k) for k in ("usd", "v2_manifold", "v3_clean", "v4_finite",
                                              "v5_dims", "v6_mass", "v7_sidecar")}
        rows[base]["full_pass"] = bool(full)
        rows[base]["tris"] = res.get("tris", 0)
    n_full = sum(1 for r in rows.values() if r["full_pass"])
    print(f"全过: {n_full}/{len(rows)} ({n_full/max(len(rows),1)*100:.1f}%)")
    OUT.write_text(json.dumps(rows, indent=1))
    print(f"输出: {OUT}")


if __name__ == "__main__":
    main()
