"""One run of each remaining development case. No automatic retries."""
import json,datetime
from run_suite_rebuild01_expanded import W,sha,write,run_case
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    first=read(W/'runs/rebuild01_dev/summary.json');assert first['completed']==3 and all(r['success'] for r in first['cases'])
    plan=read(W/'protocol/rebuild01_expanded.json')
    assert sha(W/'scripts/run_suite_rebuild01_expanded.py')==plan['runner_sha256']
    root=W/'runs/rebuild01_expanded';root.mkdir(exist_ok=False)
    checkpoint=W/'models'/plan['candidate']/'final';assert sha(checkpoint/'model.safetensors')==plan['checkpoint_sha256']
    outcomes=[]
    for case in plan['cases']:
        write(W/'rebuild10h_status.json',dict(stage='expanded_development',case=case['id'],completed=len(outcomes),planned=len(plan['cases']),updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        outcome=run_case(case,checkpoint,root/(case['id']+'_'+case['model']));outcomes.append(outcome)
        write(root/'summary.json',dict(cases=outcomes,completed=len(outcomes),planned=len(plan['cases'])))
        if outcome.get('error'):raise RuntimeError(outcome)
    write(W/'rebuild10h_status.json',dict(stage='expanded_development_complete',completed=len(outcomes),successes=sum(r['success'] for r in outcomes),updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
if __name__=='__main__':main()
