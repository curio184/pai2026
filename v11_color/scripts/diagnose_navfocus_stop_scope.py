"""Read-only phase-boundary diagnosis. Never replace the registered scores."""
import hashlib,json
from pathlib import Path
import numpy as np

W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hold(times,mask):
    start=None;best=dict(duration_s=0.,start_s=None,end_s=None)
    for t,valid in zip(times,mask):
        if not valid:start=None;continue
        if start is None:start=float(t)
        if t-start>best['duration_s']:best=dict(duration_s=float(t-start),start_s=start,end_s=float(t))
    return best

def main():
    source=read(W/'reports/navfocus_failure_details.json');result=[]
    for failure in source['failures']:
        if failure['case']['model']!='v1.1':continue
        record=W/failure['record']/'record';scorefile=record/'physical_score.json';before=sha(scorefile)
        s=read(scorefile);color=s['profile'];goal=np.asarray(s['goal_holds'][color]['goal_scene_xy_m'])
        rows=[json.loads(l) for l in (record/'trace.jsonl').open(encoding='utf-8')]
        times=np.array([r['t'] for r in rows]);truth=np.array([r['truth'] for r in rows]);phase=np.array([r['phase'] for r in rows])
        distance=np.linalg.norm(truth[:,[2,1]]-goal,axis=1);speed=np.linalg.norm(truth[:,4:6],axis=1);height=-truth[:,3]
        physical=(distance<=.25)&(speed<=.08)&(height>=.8)&(height<=1.25)
        events=read(record/'events.json');end=next(e['t'] for e in events if e['event']=='vla_approach_completed')
        land=next(e['t'] for e in events if e['event']=='land_request')
        original=hold(times,physical&(phase==color))
        assert abs(original['duration_s']-s['goal_holds'][color]['physical_hold']['duration_s'])<1e-8
        diagnostic=hold(times,physical&np.isin(phase,[color,'report']))
        before_land=hold(times,physical&(times<land))
        all_airborne=hold(times,physical)
        endpoint=min(rows,key=lambda r:abs(r['t']-end))
        result.append(dict(case=failure['case']['id'],official_success=s['success'],official_score_sha256=before,
            registered_approach_only=original,diagnostic_approach_plus_report=diagnostic,
            diagnostic_all_before_land=before_land,diagnostic_all_airborne=all_airborne,
            approach_completed_s=end,land_requested_s=land,
            report_time_available_s=land-end,
            commanded_at_completion=endpoint['model_action'],
            note='The diagnostic windows are not the registered scoring window. They do not change the failure result.'))
        assert sha(scorefile)==before
    output=dict(scope='Postflight analysis of preserved traces. Same physical thresholds; alternative phase masks are diagnostic only, not new accepted scores.',
        runtime_changed=False,model_changed=False,new_flight=False,new_inference=False,official_scores_changed=False,cases=result)
    (W/'reports/navfocus_stop_scope_diagnostic.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    for r in result:print(json.dumps({k:r[k] for k in ['case','registered_approach_only','diagnostic_approach_plus_report','diagnostic_all_before_land','diagnostic_all_airborne','report_time_available_s']}))
if __name__=='__main__':main()
