"""Check existing split metadata only; no rendering, inference or flight."""
import datetime,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=W/'protocol/plan.json';rp=W/'protocol/round02_english.json'
train=read(base)['train_layouts'];heldout=read(rp)['heldout_layouts']
frames=read(W/'protocol/training_frames.json');extra=read(W/'protocol/train05_training_frames.json')
assert len(train)==20 and len(frames)==4000 and len(extra)==2000
assert {f['layout'] for f in frames+extra}==set(range(20))
xml=W/'scenes/primitive_regression/physics/rescue_scene.xml'
root=ET.parse(xml).getroot()
retained=[list(map(float,root.find(f".//body[@name='{color}_person']").attrib['pos'].split())) for color in ['blue','red']]
known=[(x['name'],np.asarray(x['positions'])[:,:2]) for x in train]+[('retained_final_room',np.asarray(retained)[:,:2])]
rows=[]
for h in heldout:
    target=np.asarray(h['positions'])[:,:2]
    distances=[(name,min(float(np.linalg.norm(target-p)),float(np.linalg.norm(target-p[::-1])))) for name,p in known]
    nearest,dist=min(distances,key=lambda x:x[1]);assert dist>1e-6
    rows.append(dict(layout=h['name'],nearest_training_layout=nearest,minimum_unordered_joint_distance_m=dist,
                     exact_training_layout_match=False))
sources=read(W/'data/dataset10_en/image_sources.json')
assert len(sources)==8408 and all(not any(x in r['path'] for x in ['runs/','heldout','probe']) for r in sources)
out=W/'reports/round02_layout_separation.json';assert not out.exists()
out.write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='Existing 20 multi-layout configurations plus retained final-room configuration in dataset10. Does not audit the foundation model pretraining.',
    source_plan_sha256=sha(base),round_plan_sha256=sha(rp),retained_scene_sha256=sha(xml),
    dataset_audit_sha256=sha(W/'data/dataset10_en/audit.json'),image_sources_sha256=sha(W/'data/dataset10_en/image_sources.json'),
    training_frames_sha256=sha(W/'protocol/training_frames.json'),additional_frames_sha256=sha(W/'protocol/train05_training_frames.json'),
    exact_configurations_disjoint=True,training_sources_exclude_evaluation_directories=True,rows=rows,
    interpretation='Distances are Euclidean in the joint four-dimensional x/y coordinates of both people, allowing actor permutation. Not a clearance or a per-person distance. Same room and spatial range; no claim of arbitrary-layout extrapolation.',
    renders=0,inferences=0,flights=0,conditions_changed=False),indent=2),encoding='utf8')
print(json.dumps(dict(report=str(out),rows=rows)))
