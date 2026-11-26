#!/usr/bin/env python3
"""release_link_check — R7-F03 门禁: 解析发布文档内部引用路径, 断链=FAIL.

扫描 docs/nv960/*.md + hfpackage/README.md 中的 `docs/nv960/...` / `scripts/...`
/ `hfpackage/...` 引用, 验证在 GitHub 仓库根与 hfpackage 包根下均可解析。
验收: 内部证据引用失效数 = 0。
"""
import re, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ['docs/nv960/scoreboard.md', 'docs/nv960/protocols.md', 'docs/nv960/pixel_audit.md',
        'docs/nv960/coverage_map.md']
PKG = ROOT / 'hfpackage' / 'README.md'

def refs_of(text):
    return set(re.findall(r'`?((?:docs|scripts|hfpackage|manifests)/[A-Za-z0-9_./-]+\.(?:md|json|py|txt))`?', text))

def resolve(ref, base_is_pkg=False):
    if base_is_pkg and ref.startswith('docs/'):
        p = ROOT / 'hfpackage' / ref
        return p.exists()
    if base_is_pkg and ref.startswith('hfpackage/'):
        p = ROOT / ref[len('hfpackage/'):]
        return p.exists()
    p = ROOT / ref
    return p.exists()

def main():
    broken = []
    checked = 0
    files = [(f, False) for f in DOCS] + [(str(PKG.relative_to(ROOT)), True)]
    for f, is_pkg in files:
        p = ROOT / f
        if not p.exists():
            broken.append((f, '<file itself missing>'))
            continue
        text = p.read_text()
        for ref in sorted(refs_of(text)):
            checked += 1
            if not resolve(ref, is_pkg):
                broken.append((f, ref))
    print(f'checked_refs={checked} broken={len(broken)}')
    for f, ref in broken:
        print('BROKEN:', f, '->', ref)
    return 0 if not broken else 1

if __name__ == '__main__':
    sys.exit(main())
