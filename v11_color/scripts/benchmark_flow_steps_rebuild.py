"""Preregistered offline speed/plan-fidelity check. No flight or optimization."""
import os,sys,json,time,hashlib,datetime,math
from pathlib import Path
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(W/'runtime_rebuild02'))
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
from smolvla_policy import DroneVLA
from plan_endpoint import decode_plan_endpoint
import torch
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ids=['NFH01','NFH04','NFH07','NFH13','NFH14','NFH16'];frames=[]
    for cid in ids:
        rec=W/'runs/navfocus_final'/(cid+'_v1.1')/'record';events=read(rec/'events.json')
        end=next(e['t'] for e in events if e.get('event')=='vla_approach_completed')
        packets=[e for e in read(rec/'vla_link_events.json') if e['event']=='inference' and e['instruction'].startswith('Approach')]
        for offset in [5.,.5]:
            e=min(packets,key=lambda e:abs(e['sim_time_capture']-(end-offset)))
            frames.append(dict(case=cid,offset=offset,record=rec.relative_to(W).as_posix(),packet=e))
    plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope='Existing development frames only; six prior stopping cases, two preregistered times each. No final holdout data.',
        steps=[10,5,2],frames=[dict(case=f['case'],offset=f['offset'],record=f['record'],image=f['packet']['image_file']) for f in frames],
        selection='Choose fastest candidate with max decoded endpoint deviation <=.025m from10 steps and identical stop_planned flags on all12 frames. Never selects weights.',
        checkpoint_sha256=sha(W/'models/train16_en/final/model.safetensors'))
    with (W/'protocol/flow_steps_benchmark01.json').open('x',encoding='utf-8') as f:json.dump(plan,f,indent=2)
    model=DroneVLA(W/'models/train16_en/final');assert model.policy.model.config.num_steps==10
    first=frames[0];e=first['packet'];rgb=Image.open(W/first['record']/'observations'/e['image_file']).convert('RGB')
    for _ in range(3):model.infer_chunk(rgb,e['instruction'],e['estimated_state'])
    rows=[]
    for f in frames:
        e=f['packet'];path=W/f['record']/'observations'/e['image_file'];assert sha(path)==e['image_sha256']
        rgb=Image.open(path).convert('RGB')
        for steps in [10,5,2]:
            model.policy.model.config.num_steps=steps
            torch.cuda.synchronize();start=time.perf_counter();chunk=model.infer_chunk(rgb,e['instruction'],e['estimated_state']);torch.cuda.synchronize();elapsed=time.perf_counter()-start
            endpoint,info=decode_plan_endpoint(chunk,e['estimated_state'])
            rows.append(dict(case=f['case'],offset=f['offset'],steps=steps,elapsed_s=elapsed,
                image_sha256=e['image_sha256'],endpoint=endpoint.tolist(),stop_planned=info['stop_planned'],action_chunk=chunk.tolist()))
        print(f['case'],f['offset'],flush=True)
    summaries=[]
    for steps in [10,5,2]:
        rr=[r for r in rows if r['steps']==steps];errors=[];flags=[]
        for r in rr:
            b=next(b for b in rows if b['steps']==10 and (b['case'],b['offset'])==(r['case'],r['offset']))
            errors.append(float(np.linalg.norm(np.asarray(r['endpoint'])-b['endpoint'])));flags.append(r['stop_planned']==b['stop_planned'])
        summaries.append(dict(steps=steps,median_seconds=float(np.median([r['elapsed_s'] for r in rr])),max_endpoint_delta_m=max(errors),all_stop_flags_match=all(flags),eligible=max(errors)<=.025 and all(flags)))
    selected=min([s for s in summaries if s['eligible']],key=lambda s:s['median_seconds'])['steps']
    out=dict(plan=plan,rows=rows,summary=summaries,selected_steps=selected,not_closed_loop_success=True)
    with (W/'reports/flow_steps_benchmark01.json').open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
    print(json.dumps(dict(summary=summaries,selected_steps=selected)),flush=True)
if __name__=='__main__':main()
