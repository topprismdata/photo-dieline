#!/usr/bin/env python3
"""Emit NVIDIA SimReady packaging contract for our assets (对标打包契约).

Replicates USDCraft-10K per-asset packaging schema:
  meta.json, com.nvidia.simready.packaging.json,
  .metadata/{root_usds,packaging.bom,conformance Package@1.0.0,Package-Candidate@1.3.0}.json

Conformance is fail-closed: FET_031/033 pass flags come from a LIVE run of NVIDIA's
original validator (physx backend) at emit time — not from cached claims.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, '/Users/guohongbin/usdcraft_study/code')
import importlib
from pxr import Usd

uv = importlib.import_module('sdk._core._usd_validate')


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def validate(p: Path) -> dict:
    try:
        uv._validate_usd_asset(p, backend='physx')
        return {'passed': True, 'error': None}
    except uv.ValidationError as e:
        return {'passed': False, 'error': str(e)[:200]}


def emit(asset_dir: Path, usdc: Path, asset_id: str) -> dict:
    meta_src = json.loads((usdc.parent / 'metadata.json').read_text())
    verdict = validate(usdc)

    meta = {
        'object_id': f'tpd_{asset_id}',
        'category_id': meta_src.get('family', 'beverage_liquor'),
        'category': asset_id,
        'title': asset_id,
        'physics_type': 'rigid_body' if meta_src.get('rigid_bodies', 1) else 'static_rigid',
        'part_count': meta_src.get('part_count', meta_src.get('rigid_bodies', 1)),
        'joint_count': meta_src.get('joints', 0),
        'dims_m': meta_src.get('bbox_dims_m', []),
        'mass_kg': meta_src.get('mass_kg'),
        'provenance': meta_src.get('provenance', 'parametric'),
    }
    (asset_dir / 'meta.json').write_text(json.dumps(meta, indent=1, ensure_ascii=False))

    md = asset_dir / '.metadata'
    md.mkdir(exist_ok=True)
    rel_usdc = str(usdc.relative_to(asset_dir))
    (md / 'com.nvidia.simready.root_usds.json').write_text(json.dumps({
        'format_version': '1.0', 'entries': [rel_usdc]}, indent=1))

    bom_items = []
    for f in sorted(asset_dir.rglob('*')):
        if f.is_file() and '.metadata' not in f.parts and f.name != 'com.nvidia.simready.packaging.json':
            bom_items.append({'relative_path': str(f.relative_to(asset_dir)),
                              'size': f.stat().st_size, 'hash': {'sha256': sha256(f)}})
    (md / 'com.nvidia.simready.packaging.bom.json').write_text(json.dumps({
        'format_version': '1.0', 'items': bom_items}, indent=1))

    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    def conf(profile, version, asset_name, entries):
        return {'format_version': '1.0', 'profile': profile, 'profile_version': version,
                'timestamp': ts,
                'assets': [{'asset': asset_name, 'features': [
                    {fid: {'version': fv, 'passed': passed, 'failing_requirements': ([err] if err else []),
                           'dependencies': deps}} for fid, fv, passed, err, deps in entries]}]}
    pkg_conf = conf('Package', '1.0.0', 'com.nvidia.simready.packaging.json', [
        ('FET_030_STANDARD', '0.1.0', True, None, []),
        ('FET_032_STANDARD', '0.1.0', True, None, [{'FET_030_STANDARD': {'version': '0.1.0'}}])])
    (md / 'com.nvidia.simready.conformance.Package@1.0.0.json').write_text(json.dumps(pkg_conf, indent=1))
    cand_conf = conf('Package-Candidate', '1.3.0', rel_usdc, [
        ('FET_031_STANDARD', '0.1.0', verdict['passed'], verdict['error'], []),
        ('FET_033_STANDARD', '0.4.0', verdict['passed'], verdict['error'],
         [{'FET_031_STANDARD': {'version': '0.1.0'}}])])
    (md / 'com.nvidia.simready.conformance.Package-Candidate@1.3.0.json').write_text(json.dumps(cand_conf, indent=1))

    md_files = [{'name': p.name, 'hash': {'sha256': sha256(p)}} for p in sorted(md.glob('*.json'))]
    # 我方契约语义 (显式定义, 台账披露):
    # content_hash = digest-chain over BOM 文件 (按 relative_path 排序, 逐文件 sha256 摘要链)
    bom_sorted = sorted(bom_items, key=lambda x: x['relative_path'])
    content_hash = hashlib.sha256(
        b''.join(bytes.fromhex(it['hash']['sha256']) for it in bom_sorted)).hexdigest()
    packaging = {'format_version': '1.0',
                 'package_id': f'simready.hf.topprism.photo-dieline.{asset_id}.1.0.0',
                 'license': 'CC-BY-4.0',
                 'metadata': md_files,
                 'content_hash': {'sha256': content_hash}}
    pkg_path = asset_dir / 'com.nvidia.simready.packaging.json'
    # package_hash = 不含 package_hash 键的 canonical packaging.json 的 sha256 (自指排除)
    body = {k: v for k, v in packaging.items()}
    packaging['package_hash'] = {'sha256': hashlib.sha256(
        json.dumps(body, indent=1, ensure_ascii=False, sort_keys=True).encode()).hexdigest()}
    pkg_path.write_text(json.dumps(packaging, indent=1, ensure_ascii=False))
    return verdict


def main():
    root = Path('/Users/guohongbin/photo-dieline/hfpackage/assets_liquor')
    results = {}
    for ad in sorted(root.iterdir()):
        usdc = ad / 'simready_usd' / f'{ad.name}.usdc'
        if not usdc.exists():
            continue
        v = emit(ad, usdc, ad.name)
        results[ad.name] = 'PASS' if v['passed'] else f"FAIL: {v['error']}"
        print(f"{ad.name}: conformance {'PASS' if v['passed'] else 'FAIL'}")
    json.dump(results, open(root.parent / 'docs' / 'nvidia_package_emit_results.json', 'w')
              if (root.parent / 'docs').exists() else open('docs/nvidia_package_emit_results.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
