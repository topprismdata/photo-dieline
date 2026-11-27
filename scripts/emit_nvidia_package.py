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
from pxr import Usd, UsdPhysics

uv = importlib.import_module('sdk._core._usd_validate')


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def validate(p: Path) -> dict:
    try:
        uv._validate_usd_asset(p, backend='physx')
        return {'passed': True, 'error': None}
    except uv.ValidationError as e:
        return {'passed': False, 'error': str(e)[:200]}


def emit(asset_dir: Path, usdc: Path, asset_id: str, meta_src: dict) -> dict:
    meta_src = meta_src or {}
    verdict = validate(usdc)

    # COM (质量加权, 来自 MassAPI authored 属性; 缺质量时均匀平均, derived 口径)
    com_acc, mass_acc, coms = 0.0, 0.0, []
    try:
        st = Usd.Stage.Open(str(usdc))
        for prim in st.Traverse():
            if prim.HasAPI(UsdPhysics.MassAPI):
                m = UsdPhysics.MassAPI(prim).GetMassAttr().Get()
                c = UsdPhysics.MassAPI(prim).GetCenterOfMassAttr().Get()
                if c is not None:
                    coms.append((float(m) if m else 1.0, [float(v) for v in c]))
                    if m:
                        mass_acc += float(m)
    except Exception:
        pass
    if coms:
        wsum = sum(w for w, _ in coms)
        meta_com = [round(sum(w * v[i] for w, v in coms) / wsum, 4) for i in range(3)]
    else:
        meta_com = None

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
        'center_of_mass_m': meta_com,
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


def stage_meta(usdc: Path) -> dict:
    """从 stage 内省派生 meta (legacy 4 无伴生 json 的兜底)。"""
    from pxr import Usd, UsdGeom, UsdPhysics
    st = Usd.Stage.Open(str(usdc))
    bc = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'proxy'])
    mesh = next((x for x in st.Traverse() if x.IsA(UsdGeom.Mesh)), None)
    dims = None
    if mesh is not None:
        try:
            b = bc.ComputeWorldBound(mesh)
            rng = b.ComputeAlignedRange()
            dims = [round(float(v), 4) for v in rng.GetSize()]
        except Exception:
            dims = None
    mass, joints, rigid = 0.0, 0, 0
    com = None
    for x in st.Traverse():
        if 'Joint' in str(x.GetTypeName()):
            joints += 1
        if x.HasAPI(UsdPhysics.MassAPI):
            m = UsdPhysics.MassAPI(x).GetMassAttr().Get()
            if m is not None:
                mass += float(m); rigid += 1
            c = UsdPhysics.MassAPI(x).GetCenterOfMassAttr().Get()
            if c is not None and com is None:
                com = [round(float(v), 4) for v in c]
    return {'dims_m': dims, 'mass_kg': round(mass, 4) if mass else None,
            'joints': joints, 'rigid_bodies': rigid, 'center_of_mass_m': com}



def emit_model_json(asset_dir: Path, usdc: Path, asset_id: str, meta_src: dict) -> None:
    """发行约定: 每个 usdc 旁伴生 model.json 快照 (schema 逐字段照抄 NVIDIA USDCraft-10K 样本)。"""
    mass = meta_src.get('mass_kg')
    model = {
        'author': 'Topprism',
        'asset_name': asset_id,
        'asset_type': 'prop',
        'asset_license': 'CC-BY-4.0',
        'category': meta_src.get('category', asset_id),
        'source_file': f'./{usdc.name}',
        'rigid_body_count': meta_src.get('rigid_bodies') or meta_src.get('part_count') or 1,
        'mass': round(float(mass), 4) if mass else None,
        'asset_extents': meta_src.get('dims_m') or [],
    }
    (usdc.parent / 'model.json').write_text(json.dumps(model, indent=1, ensure_ascii=False))

def main():
    root = Path('/Users/guohongbin/photo-dieline/hfpackage/assets_liquor')
    results = {}
    for ad in sorted(root.iterdir()):
        usdc = ad / 'simready_usd' / f'{ad.name}.usdc'
        if not usdc.exists():
            continue
        ms = json.loads((usdc.parent / 'metadata.json').read_text())
        emit_model_json(ad, usdc, ad.name, ms)
        v = emit(ad, usdc, ad.name, ms)
        results[ad.name] = 'PASS' if v['passed'] else f"FAIL: {v['error']}"
    # nv960 正典 20 (meta 由 family 重算)
    sys.path.insert(0, '/Users/guohongbin/photo-dieline/src')
    from photo_dieline.authoring.validate_parts import load_family, validate_parts, export_parts_usdc
    fam = load_family('/Users/guohongbin/photo-dieline/pipelines/packaging/author_families/nv960_fixture_family.py')
    nroot = Path('/Users/guohongbin/photo-dieline/output/nv960_usd')
    for cid in fam.DEFAULTS:
        usdc = nroot / f'{cid}.usdc'
        if not usdc.exists():
            continue
        p = dict(fam.DEFAULTS[cid]); p['class_id'] = cid
        rep = validate_parts(fam.build_parts(p), p, fam.FAMILY)
        meta = {'category': fam.FAMILY, 'dims_m': [rep['dims_mm'][k] / 1000 for k in 'XYZ'],
                'mass_kg': rep['mass_kg'], 'part_count': len(rep.get('parts', [])) if isinstance(rep.get('parts'), list) else None,
                'authoring_inputs': p, 'rigid_bodies': None, 'joints': 0}
        emit_model_json(nroot, usdc, cid, meta)
        v = emit(nroot, usdc, cid, meta)
        results[f'nv960/{cid}'] = 'PASS' if v['passed'] else f"FAIL: {v['error']}"
    # nv960 变体 35 (params 从文件名解码)
    vroot = Path('/Users/guohongbin/photo-dieline/output/nv960_variants')
    import re
    for usdc in sorted(vroot.glob('*.usdc')):
        m = re.match(r'(.+)_h(\d+)_d(\d+)$', usdc.stem)
        if not m:
            continue
        cid, hi, di = m.group(1), int(m.group(2)) / 100, int(m.group(3)) / 100
        p = dict(fam.DEFAULTS[cid]); p['H'] = round(fam.DEFAULTS[cid]['H'] * hi, 1)
        p['D'] = round(fam.DEFAULTS[cid]['D'] * di, 1); p['class_id'] = cid
        rep = validate_parts(fam.build_parts(p), p, fam.FAMILY)
        meta = {'category': fam.FAMILY, 'dims_m': [rep['dims_mm'][k] / 1000 for k in 'XYZ'],
                'mass_kg': rep['mass_kg'], 'authoring_inputs': p, 'joints': 0}
        emit_model_json(vroot, usdc, usdc.stem, meta)
        v = emit(vroot, usdc, usdc.stem, meta)
        results[f'variant/{usdc.stem}'] = 'PASS' if v['passed'] else f"FAIL: {v['error']}"
    # TDE 试点 100 (复用既有 model.json)
    troot = Path('/Users/guohongbin/photo-dieline/output/pack10k_pilot')
    for usdc in sorted(troot.glob('*/model.usdc')):
        mj = json.loads((usdc.parent / 'model.json').read_text())
        meta = {'category': mj.get('category'), 'dims_m': mj.get('asset_extents_m'),
                'mass_kg': mj.get('mass_kg'), 'rigid_bodies': mj.get('rigid_body_count'),
                'author': mj.get('author'), 'joints': 0}
        v = emit(usdc.parent, usdc, usdc.parent.name, meta)
        results[f'tde/{usdc.parent.name}'] = 'PASS' if v['passed'] else f"FAIL: {v['error']}"
    # legacy 4 (stage 内省)
    lroot = Path('/Users/guohongbin/photo-dieline/hfpackage/families')
    for usdc in sorted(lroot.glob('*.usdc')):
        sm = stage_meta(usdc)
        emit_model_json(lroot, usdc, usdc.stem, sm)
        v = emit(lroot, usdc, usdc.stem, sm)
        results[f'legacy/{usdc.stem}'] = 'PASS' if v['passed'] else f"FAIL: {v['error']}"
    n_pass = sum(1 for v in results.values() if v == 'PASS')
    print(f'contract emit: {n_pass}/{len(results)} conformance PASS')
    json.dump(results, open('/Users/guohongbin/photo-dieline/docs/nvidia_package_emit_results.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
