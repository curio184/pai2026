"""Describe the selected model's actual completed training lineage."""
import json
from pathlib import Path
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lineage(work,candidate):
    rows=[];seen=set()
    while candidate:
        alias=work/'models'/candidate/'evaluation_alias.json'
        if alias.exists():
            mapping=read(alias);source=mapping['source_candidate']
            assert read(work/'models'/source/'result.json')['checkpoint_sha256']==read(work/'models'/candidate/'result.json')['checkpoint_sha256']
            candidate=source
        assert candidate not in seen;seen.add(candidate)
        root=work/'models'/candidate;result=read(root/'result.json');start=read(root/'started.json')
        rows.append(dict(candidate=candidate,steps=result['optimizer_steps_completed'],checkpoint_sha256=result['checkpoint_sha256'],plan_sha256=result['plan_sha256']))
        source=start['config']['initial_checkpoint'].replace('\\','/').split('/')
        if source[:2]==['v11_color','models']:
            previous=source[2];assert read(work/'models'/previous/'result.json')['checkpoint_sha256']==start['initial_checkpoint_sha256'];candidate=previous
        else:candidate=None
    return list(reversed(rows))
