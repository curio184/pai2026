import os,sys,json,time,hashlib,math
from pathlib import Path
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parents[1];P=W.parent
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1');sys.path.insert(0,str(P))
from smolvla_policy import DroneVLA
import torch
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def angle(a,b):
    if np.linalg.norm(a)<.02:return None
    return float(np.degrees(np.arccos(np.clip(a@b/(np.linalg.norm(a)*np.linalg.norm(b)),-1,1))))
plan=json.loads((W/'protocol/plan.json').read_text(encoding='utf-8'));probe=json.loads((W/'protocol/train04_english_diagnostic_probe.json').read_text(encoding='utf-8'))
selected=probe['selected'];layouts={l['name']:l for l in plan['heldout_layouts']}
models={'v1.1':W/'models'/selected['candidate']/'final'}
out=W/'probe_train04_english_dev/outputs';out.mkdir(parents=True,exist_ok=False)
for f in probe['frames']:
    src=W/'probe/images'/f"{f['id']:05d}.png";dest=src.with_suffix('.jpg')
    assert dest.exists(),'Diagnostic must reuse existing images without modification'
assert sha(Path(__file__))==probe['script_sha256']
assert json.loads((W/'runs/stress_train04_en/summary.json').read_text())['completed']==16
assert json.loads((W/'pipeline_train04_en_status.json').read_text())['stage']=='development_review'
for name,h in probe['image_sha256'].items():assert sha(W/name)==h
rows=[]
with (out/'raw_outputs.jsonl').open('x',encoding='utf-8') as raw:
    for version,ck in models.items():
        expected=plan['protected']['checkpoint_sha256'] if version=='v1.0' else selected['checkpoint_sha256'];assert sha(ck/'model.safetensors')==expected
        torch.manual_seed(20261024);torch.cuda.manual_seed_all(20261024);model=DroneVLA(ck)
        for f in probe['frames']:
            image=W/'probe/images'/f"{f['id']:05d}.jpg";q=np.asarray(f['qpos']);positions=np.asarray(layouts[f['scene']]['positions'])[:,:2]
            yaw=2*math.atan2(q[6],q[3]);c,s=math.cos(yaw),math.sin(yaw);rot=np.array([[c,-s],[s,c]])
            for group,prompts in probe['prompts'].items():
                for color,prompt in zip(['blue','red'],prompts):
                    actions=model.infer_chunk(Image.open(image).convert('RGB'),prompt,f['state']);body=actions[:10,:2].mean(axis=0);world=rot@body
                    actor=f['blue_actor'] if color=='blue' else 1-f['blue_actor'];other=1-actor
                    ga=angle(world,positions[actor]+[-.9,0]-q[:2]);oa=angle(world,positions[other]+[-.9,0]-q[:2]);pa=angle(world,positions[actor]-q[:2]);op=angle(world,positions[other]-q[:2])
                    row=dict(model=version,checkpoint_sha256=expected,frame=f,prompt_group=group,color=color,prompt=prompt,image_sha256=sha(image),body_horizontal=body.tolist(),world_horizontal=world.tolist(),goal_angle_deg=ga,other_goal_angle_deg=oa,person_angle_deg=pa,other_person_angle_deg=op,correct_goal=ga is not None and ga<oa,correct_person=pa is not None and pa<op,action_chunk=actions.tolist(),truth_used='posthoc only; model inputs RGB, text, own state')
                    rows.append(row);raw.write(json.dumps(row,ensure_ascii=False)+'\n');raw.flush()
            print(version,f['id'],flush=True)
        del model;__import__('gc').collect();torch.cuda.empty_cache()
summary=[]
for version in models:
    for group in probe['prompts']:
        rr=[r for r in rows if r['model']==version and r['prompt_group']==group]
        angles=[r['goal_angle_deg'] for r in rr if r['goal_angle_deg'] is not None]
        pairs=[all(r['correct_goal'] for r in rr if r['frame']['id']==f['id']) for f in probe['frames']]
        quads=[all(r['correct_goal'] for r in rr if r['frame']['id'] in [i,i+1]) for i in range(0,32,2)]
        summary.append(dict(model=version,prompt_group=group,outputs=len(rr),correct_goal=sum(r['correct_goal'] for r in rr),correct_person=sum(r['correct_person'] for r in rr),stationary=len(rr)-len(angles),median_goal_angle_deg=float(np.median(angles)) if angles else None,both_instructions_correct=sum(pairs),images=len(pairs),whole_quartet_correct=sum(quads),quartets=len(quads)))
(out/'summary.json').write_text(json.dumps(dict(summary=summary,probe_sha256=sha(W/'protocol/train04_english_diagnostic_probe.json'),script_sha256=sha(Path(__file__)),all_outputs=len(rows)),indent=2))
print(json.dumps(summary),flush=True)
