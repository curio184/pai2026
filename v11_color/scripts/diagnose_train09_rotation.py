"""Postflight yaw diagnostic; preserves runtime and original scoring."""
import json, math, hashlib
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def stats(v):return np.percentile(v,[0,10,50,90,100]).tolist() if len(v) else None

def main():
    cases=[]
    for case_id in ['primitive_turns','primitive_left']:
        rec=W/'runs/dev_train09_en'/(case_id+'_v1.1')/'record'
        rows=[json.loads(x) for x in (rec/'trace.jsonl').read_text().splitlines()]
        phases={}
        for phase in ['right','left']:
            rr=[r for r in rows if r['phase']==phase and r.get('estimated_state') is not None]
            if not rr:continue
            target=math.pi/2 if phase=='right' else -math.pi/2
            late=[r for r in rr if r['t']>rr[0]['t']+10 and -r['truth'][3]>.8]
            samples=[]
            for i in range(0,len(rr),max(1,len(rr)//24)):
                r=rr[i];s=r['estimated_state']
                samples.append(dict(t=r['t'],error_deg=math.degrees(target-s[6]),yaw_rate=s[7],action=r['model_action'],physical_alt=-r['truth'][3],yaw_chunk_index=r.get('yaw_chunk_index'),source=r['action_source']))
            phases[phase]=dict(start=rr[0]['t'],end=rr[-1]['t'],
                late_airborne_error_deg=stats([math.degrees(target-r['estimated_state'][6]) for r in late]),
                late_airborne_model_yaw=stats([r['model_action'][3] for r in late]),
                late_airborne_estimated_yaw_rate=stats([r['estimated_state'][7] for r in late]),
                samples=samples)
        events=read(rec/'vla_link_events.json');near=[]
        for e in events:
            if e.get('event')!='inference' or 'clockwise' not in e['instruction']:continue
            left='counterclockwise' in e['instruction'];target=-math.pi/2 if left else math.pi/2
            err=target-e['estimated_state'][6]
            if abs(err)<.3:
                actions=np.asarray(e['action_chunk'])
                near.append(dict(id=e['id'],image=e['image_file'],capture=e['sim_time_capture'],
                    instruction=e['instruction'],error_deg=math.degrees(err),own=e['estimated_state'],
                    predicted_yaw_first10_mean=float(actions[:10,3].mean()),
                    predicted_yaw_steps=actions[:,3].tolist()))
        cases.append(dict(case=case_id,success=read(rec/'physical_score.json')['success'],phases=phases,near_target_inferences=near,
                          trace_sha256=hashlib.sha256((rec/'trace.jsonl').read_bytes()).hexdigest()))
    out=W/'reports/train09_rotation_development_diagnostic.json'
    assert not out.exists()
    out.write_text(json.dumps(dict(scope='Saved trace and inference inspection only; no inference or flight performed.',cases=cases),indent=2),encoding='utf-8')
    print(json.dumps([dict(case=r['case'],success=r['success'],phases={k:{kk:vv for kk,vv in v.items() if kk!='samples'} for k,v in r['phases'].items()}) for r in cases]))
if __name__=='__main__':main()
