import json,datetime
from run_suite_rebuild02 import W,sha,write,run_case
def main():
    plan=json.loads((W/'protocol/rebuild02_dev.json').read_text());assert sha(W/'scripts/run_suite_rebuild02.py')==plan['runner_sha256']
    root=W/'runs/rebuild02_dev';root.mkdir(exist_ok=False)
    checkpoint=W/'models'/plan['candidate']/'final';assert sha(checkpoint/'model.safetensors')==plan['checkpoint_sha256']
    outcomes=[]
    for case in plan['cases']:
        write(W/'rebuild10h_status.json',dict(stage='pipeline_development',case=case['id'],completed=len(outcomes),planned=len(plan['cases']),updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        outcome=run_case(case,checkpoint,root/(case['id']+'_'+case['model']));outcomes.append(outcome)
        write(root/'summary.json',dict(cases=outcomes,completed=len(outcomes),planned=len(plan['cases']),unrun=plan['cases'][len(outcomes):]))
        if outcome.get('error') or not outcome['success']:
            write(W/'rebuild10h_status.json',dict(stage='pipeline_diagnostic_needs_analysis',case=case['id'],completed=len(outcomes),error=outcome.get('error'),updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));return
    write(W/'rebuild10h_status.json',dict(stage='pipeline_development_complete',completed=len(outcomes),successes=sum(r['success'] for r in outcomes),updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
if __name__=='__main__':main()
