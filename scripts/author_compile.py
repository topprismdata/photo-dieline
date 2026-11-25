#!/usr/bin/env python3
"""Author 家族编译器: 家族模块 → 门禁 → usdc (+可选渲染 JSON)。

用法: python author_compile.py <family.py> [--out-dir DIR] [--render-json]
门禁 G-F1..G-F7 (含 G-F7 家族语义)。导出 physx 方言 usdc。
全绿输出 COMPILATION PASS; 任一失败输出 GATE-FAIL 行 (回注 Author 用)。
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from photo_dieline.authoring.validate_parts import (  # noqa: E402
    export_parts_usdc, load_family, validate_parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("family_file")
    ap.add_argument("--out-dir", default="/tmp/author")
    ap.add_argument("--render-json", action="store_true")
    args = ap.parse_args()

    mod = load_family(args.family_file)
    params = dict(mod.DEFAULTS)
    parts = mod.build_parts(params)
    rep = validate_parts(parts, params, mod.FAMILY)
    if not rep["ok"]:
        print("COMPILATION FAIL")
        for gate, detail in rep["fails"]:
            print(f"GATE-FAIL {gate}: {detail}")
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cls = mod.CLASSES[0]
    usdc = out_dir / f"{cls}.usdc"
    ev = export_parts_usdc(parts, usdc, rep["mass_kg"], mod.FAMILY)
    print(f"COMPILATION PASS — {mod.FAMILY}/{cls}: parts={len(parts)} "
          f"mass={rep['mass_kg']}kg dims={rep['dims_mm']} usdc={usdc}")
    if args.render_json:
        rj = out_dir / f"{mod.FAMILY}_parts.json"
        json.dump({"class_id": cls, "params": {"board_t": 0.45},
                   "parts": [{"name": p["name"], "verts": p["verts_mm"],
                              "tris": p["tris"],
                              "material_id": p["material_id"]} for p in parts]},
                  open(rj, "w"))
        print(f"render json: {rj}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
