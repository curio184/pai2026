"""Recompute timing summaries from every saved inference/control record."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(folder):
    rec=folder/'record';rows=[json.loads(l) for l in (rec/'trace.jsonl').open(encoding='utf-8')]
    inf=[r for r in read(rec/'vla_link_events.json') if r['event']=='inference']
    ages=[r['t']-r['model_capture_time'] for r in rows if r.get('model_capture_time') is not None and r['action_source']=='policy']
    intervals=np.diff([r['sim_time_capture'] for r in inf])
    nav=[r for r in rows if r['phase'] in ['blue','red']]
    assert min(ages)>=0 and min(intervals)>0
    return dict(record=folder.relative_to(W).as_posix(),success=read(folder/'outcome.json')['success'],
        capture_interval_median_s=float(np.median(intervals)),image_age_mean_s=float(np.mean(ages)),
        image_age_p95_s=float(np.percentile(ages,95)),image_age_max_s=max(ages),
        adopted_rows=len(ages),inferences=len(inf),approach_rows=len(nav),
        approach_stale_hover_rows=sum(r['action_source']=='stale_hover' for r in nav),
        inference_log_sha256=sha(rec/'vla_link_events.json'),trace_sha256=sha(rec/'trace.jsonl'))
def main():
    p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');p.add_argument('--no-write',action='store_true');a=p.parse_args()
    original=read(W/'reports/rebuild_latency_same_case.json');diagnostics=[]
    for row in original['cases']:
        new=metrics(W/'runs'/row['suite']/'NFH06_v1.1')
        for name in ['success','capture_interval_median_s','image_age_mean_s','image_age_p95_s']:
            assert abs(new[name]-row[name])<1e-9,(name,new[name],row[name])
        diagnostics.append(new)
    final=[]
    if a.final:
        plan=read(W/'protocol/rebuild03_final.json')
        for case in plan['cases']:
            row=metrics(W/'runs/rebuild03_final'/(case['id']+'_'+case['model']));row['case']=case;final.append(row)
        assert len(final)==42
    result=dict(definitions=dict(capture_interval='Median simulation-time gap between successive saved model-input captures.',
        image_age='Control simulation time minus captured-image simulation time, restricted to rows where action_source is policy; stale/initializing rows are excluded.',
        approach_stale='Count of approach-stage control rows whose source is stale_hover; denominator approach_rows.',
        attribution='Complete configurations, not isolated attribution to a single changed parameter.'),
        same_case_values_reproduced=True,diagnostics=diagnostics,final_cases=final,final_complete=len(final)==42)
    if not a.no_write:
        name='rebuild03_timing_verified.json' if a.final else 'rebuild_timing_diagnostic_verified.json'
        (W/'reports'/name).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(same_case_values_reproduced=True,final_cases=len(final))))
if __name__=='__main__':main()
