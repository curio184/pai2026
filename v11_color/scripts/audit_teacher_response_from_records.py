"""Check the teacher's horizontal response approximation on saved commands.

No new flight or inference. Observed yaw and commands are supplied in hindsight;
this is not a teacher rollout success test or a causal attribution experiment.
"""
import datetime,hashlib,json,math
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def world_fl(vector,yaw):
    c,s=math.cos(yaw),math.sin(yaw)
    return np.array([[c,-s],[s,c]])@(np.asarray(vector)*[1.,-1.])
def main():
    # Freeze the completed-file list before analysis, not based on outcome.
    folders=sorted(p.parent for p in (W/'runs/navfocus_receipt').glob('*_v1.1/outcome.json'))
    folders += sorted(p.parent for p in (W/'runs/navfocus_final').glob('*_v1.1/outcome.json'))
    result=[];inputs={}
    for folder in folders:
        trace=folder/'record/trace.jsonl';score=folder/'record/physical_score.json'
        if not score.exists():continue
        rows=[json.loads(line) for line in trace.open(encoding='utf-8')]
        times=np.array([r['t'] for r in rows]);inputs[str(trace.relative_to(W))]=sha(trace)
        output=[]
        # Starts at one-second spacing, independent of the final success label.
        next_start=0.
        for i,r in enumerate(rows):
            if r['t']<next_start or r['phase'] not in ('blue','red') or not r.get('estimated_state') or not r.get('estimated_attitude'):continue
            if (r.get('execution_owner') or {}).get('owner')!='VLA':continue
            next_start=r['t']+1.;start=r['t'];phase=r['phase']
            end_idx=int(np.argmin(abs(times-(start+1.5))))
            if abs(times[end_idx]-(start+1.5))>.02:continue
            segment=rows[i:end_idx+1]
            if any(q['phase']!=phase or (q.get('execution_owner') or {}).get('owner')!='VLA' or not q.get('horizontal_control') or not q.get('estimated_attitude') for q in segment):continue
            initial_velocity=world_fl(r['estimated_state'][:2],r['estimated_attitude'][2])
            v=initial_velocity.copy();position=np.zeros(2)
            truth_start=np.asarray(r['truth'][1:3])
            for step in range(15):
                lo=start+.1*step;hi=lo+.1
                controls=[q for q in segment if lo<=q['t']<hi]
                if not controls:break
                u=np.mean([world_fl(q['horizontal_control']['adopted_requested_forward_left'],q['estimated_attitude'][2]) for q in controls],axis=0)
                v += .1*(u-v);position += .1*v
                if step not in (4,14):continue
                at=rows[int(np.argmin(abs(times-hi)))];truth=np.asarray(at['truth'])
                observed_estimated=world_fl(at['estimated_state'][:2],at['estimated_attitude'][2])
                output.append(dict(start_s=start,horizon_s=(step+1)*.1,
                    position_error_m=float(np.linalg.norm(position-(truth[1:3]-truth_start))),
                    speed_vector_error_vs_truth_m_s=float(np.linalg.norm(v-truth[4:6])),
                    speed_vector_error_vs_estimate_m_s=float(np.linalg.norm(v-observed_estimated)),
                    initial_estimate_error_m_s=float(np.linalg.norm(initial_velocity-np.asarray(r['truth'][4:6])))))
        if not output:continue
        stats=[]
        for horizon in [.5,1.5]:
            samples=[x for x in output if abs(x['horizon_s']-horizon)<1e-8]
            stats.append(dict(horizon_s=horizon,windows=len(samples),**{key:dict(median=float(np.median([x[key] for x in samples])),p90=float(np.percentile([x[key] for x in samples],90))) for key in ['position_error_m','speed_vector_error_vs_truth_m_s','speed_vector_error_vs_estimate_m_s','initial_estimate_error_m_s']}))
        result.append(dict(record=folder.relative_to(W).as_posix(),physical_success=read(score)['success'],statistics=stats,windows=output))
    assert all(sha(W/n)==h for n,h in inputs.items())
    report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
       method='Apply teacher velocity transition v+=.1*(u-v), p+=.1*v to actual saved adopted commands averaged in each100ms interval, transformed with observed estimated yaw. Initial velocity is the saved estimate. Compare with later recorded motion.',
       scope='Postflight model-consistency check; no new flight, policy inference, fitting, gain changes, training or scoring changes.',
       limitations=['Observed future commands and yaw are supplied in hindsight; this is not an online predictor.',
                    'Differences include simplified response, initial-state estimation error and100ms discretization. They do not establish teacher-only causation.',
                    'Windows overlap and are not independent trials. No success-rate claim uses these windows.',
                    'Receipt batch is still running; the analyzed completed-folder list is frozen below.'],
       records=result,trace_sha256=inputs)
    path=W/'reports/teacher_response_record_audit.json'
    with path.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    for suite in ['navfocus_final','navfocus_receipt']:
        samples=[x for r in result if suite in r['record'] for x in r['windows'] if abs(x['horizon_s']-1.5)<1e-8]
        print(json.dumps(dict(suite=suite,windows=len(samples),median_position_error_m=float(np.median([x['position_error_m'] for x in samples])),median_speed_error_m_s=float(np.median([x['speed_vector_error_vs_truth_m_s'] for x in samples])))))
if __name__=='__main__':main()
