"""Draw four fresh evaluation layouts for rebuild05 with the same sampler as rebuild03.

Drawn once, before any rebuild04 flight. Not filtered by any model output.
Separation from training/development/previous evaluation layouts is reported, not used to reject.
"""
import datetime,hashlib,itertools,json
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
SEED=202610312000
def main():
    out=W/'protocol/rebuild05_layouts.json';assert not out.exists()
    rng=np.random.default_rng(SEED);layouts=[]
    for i in range(4):
        a=[float(rng.uniform(2.65,3.65)),float(rng.uniform(.52,1.1)),0.]
        b=[float(rng.uniform(2.65,3.65)),float(rng.uniform(-1.1,-.52)),0.]
        layouts.append(dict(name=f'heldout_r05_{i+1:02d}',positions=[a,b],blue_actor=i%2))
    plan=json.loads((W/'protocol/plan.json').read_text(encoding='utf-8'))
    prior=json.loads((W/'protocol/rebuild_final_layouts.json').read_text(encoding='utf-8'))['heldout_layouts']+json.loads((W/'protocol/rebuild04_layouts.json').read_text(encoding='utf-8'))['heldout_layouts']
    nav=json.loads((W/'protocol/navfocus_layouts.json').read_text(encoding='utf-8'))
    navl=nav.get('heldout_layouts',[]) if isinstance(nav,dict) else []
    others=[('train',l) for l in plan['train_layouts']]+[('development',l) for l in plan['development_layouts']]+[('previous_evaluation',l) for l in plan['heldout_layouts']+prior+navl]
    def joint(p,q):
        p=np.array(p)[:,:2].ravel();return min(np.linalg.norm(p-np.array(q)[:,:2].ravel()),np.linalg.norm(p-np.array(q)[::-1,:2].ravel()))
    separation=[]
    for l in layouts:
        rows=[dict(kind=k,name=o['name'],unordered_joint_distance_m=float(joint(l['positions'],o['positions']))) for k,o in others]
        best=min(rows,key=lambda r:r['unordered_joint_distance_m'])
        train_best=min((r for r in rows if r['kind']=='train'),key=lambda r:r['unordered_joint_distance_m'])
        separation.append(dict(layout=l['name'],nearest_any=best,nearest_training=train_best))
    obj=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),layout_seed=SEED,heldout_layouts=layouts,
        layout_sampling=dict(x=[2.65,3.65],positive_y=[.52,1.1],negative_y=[-1.1,-.52],filtering='None. Retain all four generated layouts.',shirt_assignment='alternating actors'),
        use='Reserved rebuild05 evaluation only. Not used for training or development.',
        separation_report=separation,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(separation,indent=1))
if __name__=='__main__':main()
