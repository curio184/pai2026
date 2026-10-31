"""All saved navigation packets from prior split v1.1. Offline truth scoring only."""
import json,hashlib,math
from pathlib import Path
import numpy as np
from plan_endpoint import decode_plan_endpoint
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=read(W/'results/all_trials_navfocus.json')
    cases=[r for r in source['final_cases'] if r['case']['model']=='v1.1' and r['case'].get('color',r['case'].get('profile')) in ['blue','red']]
    plan=dict(scope='Offline decoder diagnostic, no model inference or flight. All navigation packets from all24 prior v1.1 person cases, including failures. No selecting individual favorable frames.',
        cases=[r['record'] for r in cases],decoder_sha256=sha(Path(__file__).with_name('plan_endpoint.py')))
    with (W/'protocol/endpoint_offline01.json').open('x',encoding='utf-8') as f:json.dump(plan,f,indent=2)
    results=[]
    for case in cases:
        rec=W/case['record']/'record';rows=[json.loads(l) for l in (rec/'trace.jsonl').open()];ts=np.array([r['t'] for r in rows])
        score=read(rec/'physical_score.json');color=score['profile'];goal=np.asarray(score['goal_holds'][color]['goal_scene_xy_m'])
        samples=[]
        for e in read(rec/'vla_link_events.json'):
            if e['event']!='inference' or e['instruction']!='Approach the person wearing '+color+' and stop.':continue
            idx=int(np.argmin(abs(ts-e['sim_time_capture'])));r=rows[idx]
            q=np.asarray(r['truth'][19:26]);qw,qx,qy,qz=q[3:]/np.linalg.norm(q[3:])
            h=math.atan2(2*(qx*qy+qw*qz),1-2*(qy*qy+qz*qz));c,s=math.cos(h),math.sin(h)
            rot=np.array([[c,-s],[s,c]])
            delta,details=decode_plan_endpoint(e['action_chunk'],e['estimated_state'])
            endpoint=q[:2]+rot@delta
            samples.append(dict(id=e['id'],image=e['image_file'],capture_s=e['sim_time_capture'],
                capture_goal_distance_m=float(np.linalg.norm(q[:2]-goal)),
                endpoint_error_score_goal_m=float(np.linalg.norm(endpoint-goal)),
                endpoint_error_teacher_goal_m=float(np.linalg.norm(endpoint-(goal+[-.1,0]))),
                endpoint_scene=endpoint.tolist(),**details))
        results.append(dict(record=case['record'],success=case['success'],samples=samples,
            sources={n:sha(rec/n) for n in ['trace.jsonl','vla_link_events.json','physical_score.json']}))
    output=dict(preregistered=plan,cases=results,not_closed_loop_proof=True)
    dest=W/'reports/endpoint_offline01.json'
    with dest.open('x',encoding='utf-8') as f:json.dump(output,f,indent=2)
    for label,predicate in [('all',lambda s:True),('near',lambda s:s['capture_goal_distance_m']<.5),('stop_planned',lambda s:s['stop_planned'])]:
        ss=[s for r in results for s in r['samples'] if predicate(s)]
        print(label,len(ss),json.dumps({k:[float(np.median([s[k] for s in ss])),float(np.quantile([s[k] for s in ss],.9))] for k in ['endpoint_error_score_goal_m','endpoint_error_teacher_goal_m']}))
if __name__=='__main__':main()
