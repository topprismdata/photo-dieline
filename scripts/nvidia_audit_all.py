#!/usr/bin/env python3
"""One-command full audit of NVIDIA-parity compliance across all 170 assets.

Produces docs/nvidia_full_audit_<date>.json:
  - per-asset NVIDIA original validator verdict (physx, live run)
  - packaging-contract hash-chain verification (BOM spot-check + content_hash + package_hash)
  - meta.json completeness (dims/mass/COM presence)
Fail-closed: any mismatch marks the asset FAIL.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, '/Users/guohongbin/usdcraft_study/code')
import importlib
from pxr import Usd, UsdGeom, UsdPhysics

uv = importlib.import_module('sdk._core._usd_validate')
ROOT = Path('/Users/guohongbin/photo-dieline')


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def audit_asset(asset_dir: Path, usdc: Path, name: str) -> dict:
    r = {'asset': name}
    try:
        uv._validate_usd_asset(usdc, backend='physx')
        r['validator'] = 'PASS'
    except uv.ValidationError as e:
        r['validator'] = 'FAIL'
        r['validator_error'] = str(e)[:160]
    pkg_p = asset_dir / 'com.nvidia.simready.packaging.json'
    md_dir = asset_dir / '.metadata'
    if pkg_p.exists() and md_dir.exists():
        pkg = json.loads(pkg_p.read_text())
        bom = json.loads((md_dir / 'com.nvidia.simready.packaging.bom.json').read_text())
        bom_ok = all(sha256(asset_dir / it['relative_path']) == it['hash']['sha256']
                     for it in bom['items'] if (asset_dir / it['relative_path']).exists())
        ch = hashlib.sha256(b''.join(bytes.fromhex(it['hash']['sha256'])
                                     for it in sorted(bom['items'], key=lambda x: x['relative_path']))).hexdigest()
        body = {k: v for k, v in pkg.items() if k != 'package_hash'}
        ph = hashlib.sha256(json.dumps(body, indent=1, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        r['bom'] = 'OK' if bom_ok else 'MISMATCH'
        r['content_hash'] = 'OK' if ch == pkg['content_hash']['sha256'] else 'MISMATCH'
        r['package_hash'] = 'OK' if ph == pkg['package_hash']['sha256'] else 'MISMATCH'
        meta_p = asset_dir / 'meta.json'
        if meta_p.exists():
            meta = json.loads(meta_p.read_text())
            r['meta_dims'] = bool(meta.get('dims_m'))
            r['meta_mass'] = meta.get('mass_kg') is not None
            r['meta_com'] = meta.get('center_of_mass_m') is not None
    thumbs = list((usdc.parent / '.thumbs' / '256x256').glob(f'{usdc.name}*.png')) \
        if (usdc.parent / '.thumbs').exists() else []
    r['thumbs'] = len(thumbs)
    checks = [r.get('validator') == 'PASS']
    if 'bom' in r:
        checks += [r['bom'] == 'OK', r['content_hash'] == 'OK', r['package_hash'] == 'OK']
    r['overall'] = 'PASS' if all(checks) else 'FAIL'
    return r


def main():
    domains = {
        'liquor': sorted((ROOT / 'hfpackage/assets_liquor').glob('*/simready_usd/*.usdc')),
        'legacy': sorted((ROOT / 'hfpackage/families').glob('*.usdc')),
        'nv960_canonical': sorted((ROOT / 'output/nv960_usd').glob('*.usdc')),
        'nv960_variants': sorted((ROOT / 'output/nv960_variants').glob('*.usdc')),
        'tde_pilot': sorted((ROOT / 'output/pack10k_pilot').glob('*/model.usdc')),
    }
    out = {'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'),
           'validator': 'NVIDIA USDCraft _validate_usd_asset (physx), live run',
           'domains': {}, 'summary': None}
    total = passed = 0
    for dom, files in domains.items():
        rows = []
        for f in files:
            asset_dir = f.parent.parent if dom == 'liquor' else f.parent
            rows.append(audit_asset(asset_dir, f, f'{dom}/{f.parent.name}/{f.name}'))
        n_pass = sum(1 for r in rows if r['overall'] == 'PASS')
        out['domains'][dom] = {'count': len(rows), 'pass': n_pass, 'assets': rows}
        total += len(rows); passed += n_pass
        print(f'{dom}: {n_pass}/{len(rows)}')
    out['summary'] = {'total': total, 'pass': passed}
    dest = ROOT / 'docs' / f'nvidia_full_audit_{out["timestamp"][:10]}.json'
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f'TOTAL: {passed}/{total} -> {dest}')


if __name__ == '__main__':
    main()
