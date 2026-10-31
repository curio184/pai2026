"""Recompute intervention metrics from raw actions; no model or flight execution."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def angle(v,d):
    if np.linalg.norm(v)<.02:return None
    return abs(math.degrees(math.atan2(v[0]*d[1]-v[1]*d[0],float(v@d))))
def main(write_report=True):
    base=read(W/'protocol/plan.json');results=[]
    specs=[('v10_language','probe_v10_language','probe_rebuild03/images','v10_language_reference.json','rebuild_final_layouts.json','selected_rebuild03.json')]
    for name,folder,images,protocol,layoutfile,selection in specs:
        root=W/folder
        if not (root/'outputs/summary.json').exists():continue
        plan=read(W/'protocol'/protocol);layouts={r['name']:r for r in read(W/'protocol'/layoutfile)['heldout_layouts']}
        chosen=read(W/'protocol'/selection) if selection else plan['selected'];expected_hashes={'v1.0':base['protected']['checkpoint_sha256'],'v1.1':chosen['checkpoint_sha256']}
        expected_hashes={k:v for k,v in expected_hashes.items() if k in plan['models']}
        summary=read(root/'outputs/summary.json');assert summary['probe_sha256']==sha(W/'protocol'/protocol)
        rows=[json.loads(line) for line in (root/'outputs/raw_outputs.jsonl').read_text(encoding='utf-8').splitlines()]
        expected={(m,f['id'],g,c) for m in expected_hashes for f in plan['frames'] for g in plan['prompts'] for c in ['blue','red']}
        actual={(r['model'],r['frame']['id'],r['prompt_group'],r['color']) for r in rows};assert len(actual)==len(rows) and actual==expected
        recomputed={}
        for row in rows:
            assert row['num_steps']==5
            f=row['frame'];assert f==plan['frames'][f['id']]
            assert row['checkpoint_sha256']==expected_hashes[row['model']]
            assert row['prompt']==plan['prompts'][row['prompt_group']][0 if row['color']=='blue' else 1]
            image=W/images/f"{f['id']:05d}.jpg";assert sha(image)==row['image_sha256'] and Image.open(image).size==(320,240)
            # The policy adapter returns float32; preserve that reduction precision.
            a=np.asarray(row['action_chunk'],dtype=np.float32);assert a.shape==(32,6) and np.isfinite(a).all()
            v=a[:10,:2].mean(axis=0);assert np.allclose(v,row['body_horizontal'],rtol=0,atol=1e-8)
            q=np.asarray(f['qpos']);qw,qx,qy,qz=q[3:];assert qx==qy==0
            world=np.array([[1-2*qz*qz,-2*qw*qz],[2*qw*qz,1-2*qz*qz]])@v
            assert np.allclose(world,row['world_horizontal'],rtol=0,atol=1e-8)
            positions=np.asarray(layouts[f['scene']]['positions'])[:,:2]
            actor=f['blue_actor'] if row['color']=='blue' else 1-f['blue_actor'];other=1-actor
            ga=angle(world,positions[actor]+[-.9,0]-q[:2]);oa=angle(world,positions[other]+[-.9,0]-q[:2])
            pa=angle(world,positions[actor]-q[:2]);op=angle(world,positions[other]-q[:2])
            for field,value in [('goal_angle_deg',ga),('other_goal_angle_deg',oa),('person_angle_deg',pa),('other_person_angle_deg',op)]:
                assert row[field] is None if value is None else abs(row[field]-value)<1e-5
            correct=ga is not None and ga<oa;person=pa is not None and pa<op
            assert bool(row['correct_goal'])==correct and bool(row['correct_person'])==person
            recomputed[row['model'],f['id'],row['prompt_group'],row['color']]=(correct,person,ga)
        for s in summary['summary']:
            m,g=s['model'],s['prompt_group'];rr=[v for (mm,_,gg,_),v in recomputed.items() if mm==m and gg==g]
            assert s['outputs']==len(rr) and s['correct_goal']==sum(v[0] for v in rr) and s['correct_person']==sum(v[1] for v in rr)
            angles=[v[2] for v in rr if v[2] is not None];assert s['stationary']==len(rr)-len(angles)
            if angles:assert abs(s['median_goal_angle_deg']-float(np.median(angles)))<1e-5
            both=[all(recomputed[m,f['id'],g,c][0] for c in ['blue','red']) for f in plan['frames']]
            assert s['both_instructions_correct']==sum(both)
            quads=[]
            for i in range(0,len(plan['frames']),2):
                f,h=plan['frames'][i:i+2];assert f['qpos']==h['qpos'] and f['state']==h['state'] and f['scene']==h['scene'] and f['blue_actor']!=h['blue_actor']
                quads.append(both[i] and both[i+1])
            assert s['whole_quartet_correct']==sum(quads)
        results.append(dict(probe=name,outputs=len(rows),metric_and_image_checks_passed=True,selected_checkpoint_sha256=chosen['checkpoint_sha256'],
            protocol_sha256=sha(W/'protocol'/protocol),raw_sha256=sha(root/'outputs/raw_outputs.jsonl'),summary_sha256=sha(root/'outputs/summary.json')))
    report=dict(probes=results,all_consistent=True,scope='Offline arithmetic and image-hash checks. No fresh model inference or flight.')
    if write_report:(W/'reports/v10_language_reference_verified.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--no-write',action='store_true');args=parser.parse_args()
    main(write_report=not args.no_write)
