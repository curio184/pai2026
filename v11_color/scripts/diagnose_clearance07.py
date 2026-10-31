"""Postflight minimum-clearance attribution for the completed development case."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
record=W/'runs/dev_train07_en/dev02_blue_v1.1/record'
rows=[json.loads(l) for l in (record/'trace.jsonl').read_text().splitlines()]
root=ET.parse(W/'scenes/dev02/physics/rescue_scene.xml').getroot().find('worldbody')
persons={c:np.fromstring(root.find(f"body[@name='{c}_person']").get('pos'),sep=' ')[:2] for c in ['blue','red']}
results=[]
for color,pos in persons.items():
    eligible=[r for r in rows if -r['truth'][3]>.1]
    closest=min(eligible,key=lambda r:np.linalg.norm(np.asarray(r['truth'])[[2,1]]-pos))
    timeline=[]
    for r in rows:
        if abs(r['t']-closest['t'])<=4 and (not timeline or r['t']-timeline[-1]['t']>=.5):
            timeline.append(dict(t=r['t'],phase=r['phase'],position=np.asarray(r['truth'])[[2,1]].tolist(),
                height=-r['truth'][3],clearance=float(np.linalg.norm(np.asarray(r['truth'])[[2,1]]-pos)),
                physical_velocity=r['truth'][4:6],estimated_state=r['estimated_state'],action=r['model_action'],
                action_source=r['action_source'],capture_time=r['model_capture_time'],chunk_index=r['chunk_index']))
    results.append(dict(color=color,minimum_clearance=float(np.linalg.norm(np.asarray(closest['truth'])[[2,1]]-pos)),
        t=closest['t'],phase=closest['phase'],timeline=timeline))
out=dict(scope='Postflight geometry only; no truth sent to runtime; no additional inference or flights.',
    completed_case='dev02_blue',trace_sha256=hashlib.sha256((record/'trace.jsonl').read_bytes()).hexdigest(),persons=results)
dest=W/'reports/train07_dev02_clearance_development_diagnostic.json';assert not dest.exists()
dest.write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(results))
