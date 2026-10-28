#!/usr/bin/env python3
"""Use rendered manifest to enumerate ONLY actual images; prepare offline mappings."""
import os, re, sys
import yaml
source, out = sys.argv[1:]
text = open(source, encoding='utf8').read()
refs = set()
for doc in yaml.safe_load_all(text):
    if not isinstance(doc, dict):
        continue
    def walk(obj):
        if isinstance(obj, dict):
            for k,v in obj.items():
                if k == 'image' and isinstance(v,str) and v:
                    refs.add(v)
                else: walk(v)
        elif isinstance(obj,list):
            for x in obj: walk(x)
    walk(doc)
if not refs:
    raise SystemExit('ERROR: no images discovered in rendered manifest')
registry = '192.168.72.60:32082'
with open(os.path.join(out,'images-map.tsv'),'w') as f:
    for i,src in enumerate(sorted(refs), 1):
        # Keep namespace and basename, remove source registry. All images are isolated under policy-reporter/.
        segments=src.split('/')
        remainder='/'.join(segments[1:]) if ('.' in segments[0] or ':' in segments[0] or segments[0]=='localhost') else src
        target=f'{registry}/policy-reporter/{remainder}'
        name=f'image-{i:02d}-{re.sub("[^a-zA-Z0-9._-]", "_", remainder)}.tar'
        f.write(f'{src}\t{name}\t{target}\n')
print(f'Images to download: {len(refs)}')
for ref in sorted(refs): print(ref)
