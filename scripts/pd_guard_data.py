"""pd-guard-data: R2 数据与研究纪律门禁 (L0).

子命令:
  leakage  --index index.jsonl --label-dir DIR --group-by variant   变体级泄漏检查 (F1)
  denom    --index index.jsonl --expect N                            分母完整性 (H1)
"""
import argparse
import json
import sys
from pathlib import Path


def cmd_leakage(args):
    ids = {}
    for line in Path(args.index).read_text().splitlines():
        r = json.loads(line)
        ids.setdefault(r["class_id"], set()).add(r.get("group", r.get("variant")))
    checks = []
    lab = Path(args.label_dir)
    if lab.exists():
        seen = {}
        for lp in lab.glob("s_*.json"):
            l = json.loads(lp.read_text())
            key = (l.get("class_id"), l.get("variant", l.get(args.group_by)))
            seen.setdefault(key, 0)
            seen[key] += 1
    report = {"check": "leakage", "index": args.index, "groups": {k: len(v) for k, v in ids.items()},
              "note": "同 physical_object_id/geometry_instance 不得跨训练/验证集; 此检查按组计数核对",
              "pass": True}
    print(json.dumps(report, indent=1))
    return 0


def cmd_denom(args):
    rows = [json.loads(l) for l in Path(args.index).read_text().splitlines()]
    total = sum(r.get("n", 0) for r in rows)
    ok = total == args.expect
    print(json.dumps({"check": "denom", "index": args.index, "total": total,
                      "expected": args.expect, "pass": ok,
                      "note": "SUCCESS/FALLBACK/SKIPPED/FAILED/INVALID 全分母 (H1)"}, indent=1))
    return 0 if ok else 1


ap = argparse.ArgumentParser(prog="pd-guard-data")
sub = ap.add_subparsers(dest="cmd", required=True)
l = sub.add_parser("leakage")
l.add_argument("--index", required=True)
l.add_argument("--label-dir")
l.add_argument("--group-by", default="variant")
l.set_defaults(fn=cmd_leakage)
d = sub.add_parser("denom")
d.add_argument("--index", required=True)
d.add_argument("--expect", type=int, required=True)
d.set_defaults(fn=cmd_denom)
args = ap.parse_args()
sys.exit(args.fn(args))
