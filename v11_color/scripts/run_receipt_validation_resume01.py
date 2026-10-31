"""Run only the28 unstarted cases after a repaired scoring interpreter failure."""
import datetime,json
from run_receipt_validation import W,P,sha,write,run_case,lock_check,read,now,status,check
def main():
    plan=read(W/'protocol/navfocus_receipt.json');deadline=datetime.datetime.fromisoformat(plan['deadline_utc'])
    root=W/'runs/navfocus_receipt';summary=read(root/'summary.json');assert summary['completed']==14
    outcomes=summary['cases'];assert len(outcomes)==14 and not any(r.get('error') for r in outcomes)
    assert [r['case'] for r in outcomes]==plan['cases'][:14]
    assert all(not (root/(c['id']+'_'+c['model'])).exists() for c in plan['cases'][14:])
    old=P/read(W/'protocol/plan.json')['training']['initial_checkpoint'];new=W/'models'/plan['candidate']/'final'
    assert sha(old/'model.safetensors')==plan['old_checkpoint_sha256']
    assert sha(new/'model.safetensors')==plan['checkpoint_sha256']
    check(plan)
    with (root/'resume01.json').open('x',encoding='utf-8') as f:
        json.dump(dict(created_utc=now().isoformat(),reason='Same CPython binary restored after missing standard-library failure during scoring. Flight14 completed and scored offline; no flight is repeated.',
            remaining_cases=plan['cases'][14:],protocol_sha256=sha(W/'protocol/navfocus_receipt.json'),
            script_sha256=sha(__file__),environment_recovery='<WORK_ROOT>/runtimes/receipt_environment_recovery/recovery.json'),f,indent=2)
    for c in plan['cases'][14:]:
        if (deadline-now()).total_seconds()<840:status('deadline_reserve',completed=len(outcomes),planned=42,no_retry=True);return
        check(plan);status('flight',case=c['id'],model=c['model'],group=c['group'],completed=len(outcomes),planned=42)
        result=run_case(c,new if c['model']=='v1.1' else old,root/(c['id']+'_'+c['model']))
        outcomes.append(result)
        write(root/'summary.json',dict(completed=len(outcomes),planned=42,cases=outcomes,configuration='navfocus_receipt',protocol_sha256=sha(W/'protocol/navfocus_receipt.json')))
        if result.get('error'):status('infrastructure_error',completed=len(outcomes),error=result['error'],record=result['record'],automatic_retry=False);return
    status('flights_complete',completed=42,planned=42,static_probe_reused=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:status('execution_error',error=repr(exc),automatic_retry=False);raise
