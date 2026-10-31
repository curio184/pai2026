"""Exactly one pass through the approved42 cases; no retries or tuning."""
import datetime,json
from run_suite_receipt import W,P,sha,write,run_case,lock_check
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def now():return datetime.datetime.now(datetime.timezone.utc)
def status(stage,**extra):
    obj=dict(stage=stage,updated_utc=now().isoformat(),**extra)
    write(W/'receipt_validation_status.json',obj);print(json.dumps(obj),flush=True)
def check(plan):
    assert sha(W/'protocol/runtime_navfocus_lock.json')==plan['runtime_lock_sha256']
    for name,h in plan['scripts'].items():assert sha(W/'scripts'/name)==h,name
    lock_check()
def main():
    plan=read(W/'protocol/navfocus_receipt.json');deadline=datetime.datetime.fromisoformat(plan['deadline_utc'])
    root=W/'runs/navfocus_receipt';root.mkdir(exist_ok=False)
    old=P/read(W/'protocol/plan.json')['training']['initial_checkpoint'];new=W/'models'/plan['candidate']/'final'
    assert sha(old/'model.safetensors')==plan['old_checkpoint_sha256']
    assert sha(new/'model.safetensors')==plan['checkpoint_sha256']
    check(plan);write(root/'suite_plan.json',plan);outcomes=[]
    for c in plan['cases']:
        if (deadline-now()).total_seconds()<840:
            status('deadline_reserve',completed=len(outcomes),planned=42,no_retry=True);return
        check(plan)
        status('flight',case=c['id'],model=c['model'],group=c['group'],completed=len(outcomes),planned=42)
        result=run_case(c,new if c['model']=='v1.1' else old,root/(c['id']+'_'+c['model']))
        outcomes.append(result)
        write(root/'summary.json',dict(completed=len(outcomes),planned=42,cases=outcomes,
            configuration='navfocus_receipt',protocol_sha256=sha(W/'protocol/navfocus_receipt.json')))
        if result.get('error'):
            status('infrastructure_error',completed=len(outcomes),error=result['error'],record=result['record'],automatic_retry=False);return
    status('flights_complete',completed=42,planned=42,static_probe_reused=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        status('execution_error',error=repr(exc),automatic_retry=False)
        raise
