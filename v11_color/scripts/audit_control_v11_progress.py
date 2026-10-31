"""Postflight stage/command accounting, not an additional experiment."""
import json, math
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    output=[]
    for folder in sorted((W/'runs/control_v11_final').iterdir()):
        if not folder.is_dir() or not (folder/'outcome.json').exists():continue
        outcome=read(folder/'outcome.json');r=folder/'record'
        if not (r/'trace.jsonl').exists():continue
        trace=[json.loads(s) for s in (r/'trace.jsonl').read_text(encoding='utf-8').splitlines()]
        result=read(r/'result.json');phases=[]
        for phase in dict.fromkeys(t['phase'] for t in trace):
            rr=[t for t in trace if t['phase']==phase and t.get('estimated_state')]
            if not rr:continue
            a=np.array([t['model_action'] for t in rr]);s=np.array([t['estimated_state'] for t in rr]);dt=np.median(np.diff([t['t'] for t in rr])) if len(rr)>1 else 0
            slow_yaw=np.abs(s[:,7])<.08;max_run=run=0.
            for flag in slow_yaw:
                run=run+dt if flag else 0.;max_run=max(max_run,run)
            phases.append(dict(phase=phase,first_s=rr[0]['t'],last_s=rr[-1]['t'],rows=len(rr),
                estimated_relative_yaw_deg_range=[float(np.degrees(s[:,6].min())),float(np.degrees(s[:,6].max()))],
                generated_yaw_rate_percentiles=np.percentile(a[:,3],[0,5,50,95,100]).tolist(),
                estimated_yaw_rate_percentiles=np.percentile(s[:,7],[0,5,50,95,100]).tolist(),
                yaw_rate_below_008_fraction=float(slow_yaw.mean()),max_contiguous_low_yaw_rate_s=max_run,
                estimated_horizontal_speed_percentiles=np.percentile(np.linalg.norm(s[:,:2],axis=1),[0,50,95,100]).tolist(),
                estimated_altitude_range=[float(s[:,3].min()),float(s[:,3].max())],
                action_sources={source:sum(t['action_source']==source for t in rr) for source in set(t['action_source'] for t in rr)}))
        output.append(dict(record=folder.relative_to(W).as_posix(),success=outcome['success'],
                           model=outcome['model'],mission_failure=result.get('mission_failure'),phases=phases))
    obj=dict(scope='Read-only accounting from completed original traces; no intervention, tuning or new inference.',cases=output)
    (W/'reports/control_v11_progress_audit.json').write_text(json.dumps(obj,indent=2),encoding='utf-8')
    print(json.dumps(obj,ensure_ascii=False))
if __name__=='__main__':main()
