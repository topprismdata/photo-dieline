#!/usr/bin/env python3
"""Route A experiment runner — S / R / S+R mixed-data comparison with sample-efficiency curve.

Protocol (preregistered, GPT review 2026-11-27):
  R    = real-only baseline (annotated real photos)
  S    = synthetic-only (existing v0.2 DR corpus, 120 img)
  S+R  = synthetic + N real images, N in {5, 10, 20, 40}
  Metric: real-eval mAP50 on the fixed 5-photo / 177-box eval set (identical for all arms)
  Key claim tested: does S+R beat R at equal N (sample efficiency gain), not merely beat S.
  Seeds: 3 repeats per arm (42/43/44); report mean±min.
  Real annotation source: data/bench_a_candidates/ (27 sourced + vision-annotated on demand).

Usage (after annotation approval):
  python3 scripts/bench_a_route_a.py --real-imgs 5 10 20 40 --seeds 42 43 44
Requires: data/bench_a_real_mixed/ populated by annotation step (images+labels).
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / 'output/bench_a/route_a'
SYN_CORPUS = ROOT / 'output/bench_a'                 # v0.2 DR corpus: images/{train,val} (100+20)
REAL_EVAL = ROOT / 'data/bench_a_real'               # frozen 5-photo eval set
REAL_ANN = ROOT / 'data/bench_a_real_mixed'         # annotated real training pool (post-approval)


def build_mixed(n_real: int, seed: int, workdir: Path) -> Path:
    """S corpus + first-n annotated real images (deterministic pick by sorted name)."""
    workdir.mkdir(parents=True, exist_ok=True)
    for sub in ('images', 'labels'):
        (workdir / sub).mkdir(exist_ok=True)
        for src in (SYN_CORPUS / sub / 'train').glob('*'):
            shutil.copy(src, workdir / sub / src.name)
    reals = sorted((REAL_ANN / 'images').glob('*.jpg'))[:n_real]
    assert len(reals) == n_real, f'need {n_real} annotated real images, have {len(reals)}'
    for img in reals:
        shutil.copy(img, workdir / 'images' / img.name)
        lab = REAL_ANN / 'labels' / (img.stem + '.txt')
        assert lab.exists(), f'missing label {lab}'
        shutil.copy(lab, workdir / 'labels' / lab.name)
    names = {0: 'beer_bottle_330', 1: 'beer_bottle_500', 2: 'beer_can_500', 3: 'baijiu_bottle_500',
             4: 'wine_bottle_750', 5: 'whisky_bottle_700', 6: 'vodka_bottle_700', 7: 'liquor_gift_dual',
             8: 'beer_can_330', 9: 'beverage_can_330', 10: 'food_container_1l', 11: 'rsc_rsc_closed'}
    yaml = workdir / 'dataset.yaml'
    yaml.write_text(
        f"path: {workdir}\ntrain: images\nval: {REAL_EVAL / 'images'}\nnames: {json.dumps(names, indent=0)}"
    )
    return yaml


def run_arm(arm: str, n_real: int, seed: int, data_yaml: Path) -> dict:
    base = YOLO(str(RUNS.parent / 'yolov8n/weights/best.pt'))  # v0.2 DR checkpoint
    lr0 = 0.005 if arm in ('R', 'S+R') else 0.01              # low LR for real-data arms
    name = f'{arm}_n{n_real}_s{seed}'
    base.train(data=str(data_yaml), epochs=20, imgsz=640, device='mps', lr0=lr0,
               project=str(RUNS), name=name, seed=seed, exist_ok=True, verbose=False)
    m = YOLO(str(RUNS / name / 'weights/best.pt'))
    r = m.val(data=str(data_yaml), imgsz=640, device='mps', verbose=False)
    return {'arm': arm, 'n_real': n_real, 'seed': seed, 'mAP50': float(r.box.map50),
            'recall': float(r.box.mr), 'precision': float(r.box.mp)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--real-imgs', type=int, nargs='+', default=[5, 10, 20, 40])
    ap.add_argument('--seeds', type=int, nargs='+', default=[42, 43, 44])
    ap.add_argument('--arms', nargs='+', default=['R', 'S+R'], choices=['R', 'S', 'S+R'])
    args = ap.parse_args()
    if not REAL_ANN.exists() or not any((REAL_ANN / 'images').glob('*.jpg')):
        sys.exit('ERROR: annotation pool empty — populate data/bench_a_real_mixed/ first (user-gated).')
    rows = []
    for arm in args.arms:
        if arm == 'S':
            yaml = build_mixed(0, 42, RUNS / 'mix_S')  # S arm ignores real images
            rows.append(run_arm('S', 0, 42, yaml))
            continue
        for n in args.real_imgs:
            for seed in args.seeds:
                yaml = build_mixed(n if arm == 'S+R' else 0, seed,
                                   RUNS / f'mix_{arm}_n{n}_s{seed}')
                row = run_arm(arm, n, seed, yaml)
                rows.append(row)
                print(json.dumps(row))
    out = RUNS / 'route_a_results.json'
    out.write_text(json.dumps(rows, indent=1))
    print('saved', out)


if __name__ == '__main__':
    main()
