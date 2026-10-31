import json,datetime
from run_suite_rebuild01 import W,sha,write,run_case
def main():
    plan=json.loads((W/'protocol/rebuild01_dev.json').read_text())
    assert sha(W/'scripts/run_suite_rebuild01.py')==plan['runner_sha256']
    root=W/'runs/rebuild01_dev';root.mkdir(exist_ok=False)
    checkpoint=W/'models'/plan['candidate']/'final';assert sha(checkpoint/'model.safetensors')==plan['checkpoint_sha256']
    outcomes=[]
    for case in plan['cases']:
        write(W/'rebuild10h_status.json',dict(stage='development_flight',case=case['id'],completed=len(outcomes),updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        outcome=run_case(case,checkpoint,root/(case['id']+'_'+case['model']));outcomes.append(outcome)
        write(root/'summary.json',dict(cases=outcomes,completed=len(outcomes),planned=len(plan['cases'])))
        if outcome.get('error'):raise RuntimeError(outcome)
    write(W/'rebuild10h_status.json',dict(stage='development_batch_complete',completed=len(outcomes),successes=sum(r['success'] for r in outcomes),updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
if __name__=='__main__':main()
