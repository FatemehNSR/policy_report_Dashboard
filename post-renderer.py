#!/usr/bin/env python3
"""Helm post-renderer: rewrite exactly the image refs in images-map.tsv. Stdlib only."""
import os, re, sys
mapping_file=os.environ.get('POLICY_REPORTER_IMAGE_MAP', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images-map.tsv'))
mapping={}
with open(mapping_file,encoding='utf8') as f:
    for line in f:
        src, filename, dst = line.rstrip('\n').split('\t')
        mapping[src]=dst
payload=sys.stdin.read()
seen=set()
pattern=re.compile(r'(?m)^(\s*image:\s*)(["\']?)([^\s"\']+)(["\']?)(\s*(?:#.*)?)$')
def replace(m):
    src=m.group(3)
    if src not in mapping:
        raise SystemExit(f'Unmapped image reference: {src}')
    seen.add(src)
    return m.group(1)+m.group(2)+mapping[src]+m.group(4)+m.group(5)
output=pattern.sub(replace,payload)
if seen != set(mapping):
    raise SystemExit('Rendered images do not match bundled images. Check chart/version/values. Missing: '+str(set(mapping)-seen))
sys.stdout.write(output)
