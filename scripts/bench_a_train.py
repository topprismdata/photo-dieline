#!/usr/bin/env python3
"""Benchmark A 训练适配器 — ultralytics YOLO on bench_a dataset.yaml (MPS).

用法: python3 scripts/bench_a_train.py [--epochs 40] [--model yolov8n]
输出: output/bench_a/runs/<model>/ (权重+训练日志) ; 验证指标打印并落盘 val_metrics.json
"""
import argparse
import json
import sys
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output/bench_a"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--model", default="yolov8n")
    ap.add_argument("--imgsz", type=int, default=640)
    args = ap.parse_args()

    dev = "mps" if sys.platform == "darwin" else "cpu"
    y = YOLO(f"{args.model}.pt")
    r = y.train(data=str(OUT / "dataset.yaml"), epochs=args.epochs, imgsz=args.imgsz,
                device=dev, project=str(OUT / "runs"), name=args.model, exist_ok=True,
                batch=16 if dev == "mps" else 8, workers=2, seed=42)
    metrics = {
        "mAP50": float(r.results_dict.get("metrics/mAP50(B)", 0.0)),
        "mAP50_95": float(r.results_dict.get("metrics/mAP50-95(B)", 0.0)),
        "model": args.model, "epochs": args.epochs, "device": dev,
    }
    (OUT / "val_metrics.json").write_text(json.dumps(metrics, indent=1))
    print("VAL:", json.dumps(metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
