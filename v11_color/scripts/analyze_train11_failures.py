"""Postflight development analysis only; no inference, training or trial edits."""
import datetime,hashlib,json,math,sys
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];sys.path[:0]=[str(W.parent),str(W/'scripts')]
from make_revision_data import rotation,scene_targets
from verify_records_round02_english import scene_path
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
suite=W/'runs/stress_train11_en';summary=read(suite/'summary.json')
assert summary['completed']==summary['planned']==16
report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Saved development records only; no new inference or changes to runtime or scores.',cases=[],latency=[])
for outcome in summary['cases']:
    c=outcome['case'];rec=suite/(c['id']+'_'+c['model'])/'record'
    rows=[json.loads(x) for x in (rec/'trace.jsonl').read_text().splitlines()]
    first={}
    for r in rows:
        if r.get('action_source')=='policy' and r.get('model_capture_time') is not None:
            first.setdefault(r['model_capture_time'],r['t']-r['model_capture_time'])
    report['latency'].append(dict(id=c['id'],capture_to_first_executed_action_s_p10_median_p90=np.percentile(list(first.values()),[10,50,90]).tolist()))
    if outcome['success']:continue
    target=scene_targets(scene_path(c))[c['color']]
    phases={}
    for phase in sorted(set(r['phase'] for r in rows)):
        rr=[r for r in rows if r['phase']==phase and r.get('estimated_state') is not None]
        if not rr:continue
        states=np.array([r['estimated_state'] for r in rr]);truth=np.array([r['truth'] for r in rr]);actions=np.array([r['model_action'] for r in rr])
        samples=[]
        for r in [rr[0],rr[-1]]:
            q=np.array(r['truth'][19:26]);rot=rotation(q[3:]);heading=math.atan2(rot[1,0],rot[0,0]);delta=target[:2]-q[:2]
            bearing=(math.atan2(delta[1],delta[0])-heading+math.pi)%(2*math.pi)-math.pi
            samples.append(dict(t=r['t'],position=q[:3].tolist(),heading_deg=math.degrees(heading),target_bearing_deg=math.degrees(bearing)))
        phases[phase]=dict(start_s=rr[0]['t'],end_s=rr[-1]['t'],estimated_horizontal_speed_median=float(np.median(np.linalg.norm(states[:,:2],axis=1))),physical_horizontal_speed_median=float(np.median(np.linalg.norm(truth[:,26:28],axis=1))),estimated_horizontal_speed_under_008_fraction=float(np.mean(np.linalg.norm(states[:,:2],axis=1)<=.08)),physical_horizontal_speed_under_008_fraction=float(np.mean(np.linalg.norm(truth[:,26:28],axis=1)<=.08)),physical_vertical_speed_under_008_fraction=float(np.mean(np.abs(truth[:,28])<=.08)),physical_height_080_125_fraction=float(np.mean((truth[:,21]>=.8)&(truth[:,21]<=1.25))),median_action=np.median(actions,axis=0).tolist(),endpoints=samples)
    report['cases'].append(dict(id=c['id'],failure=read(rec/'result.json').get('mission_failure'),score=read(rec/'search_score.json'),phases=phases,trace_sha256=sha(rec/'trace.jsonl')))
report['visual_review']=[dict(case='H16',images=['00049.jpg','00057.jpg'],observation='49: both people visible, red on right. 57: red largely clipped by right image edge. The recorded lateral movement is toward red, but forward approach and pre-existing lateral drift leave the target outside view. This does not prove a unique cause.' )]
report['hypotheses']=['Stronger braking targets may reduce sustained horizontal drift in initial hover and scanning; runtime gains remain unchanged.','Yaw labels can anticipate capture-to-actuation latency using only the recorded own yaw rate. Lower teacher yaw rate may reduce overshoot; runtime cap remains unchanged.','H16 has a navigation-direction error as well as drift. Improving stationary phases alone may not fix it; retain and report all subsequent failures.']
out=W/'reports/train11_failure_analysis.json';assert not out.exists();out.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(dict(report=str(out),sha256=sha(out),failed_cases=[r['id'] for r in report['cases']],latency_median_across_cases=float(np.median([x['capture_to_first_executed_action_s_p10_median_p90'][1] for x in report['latency']])))))
