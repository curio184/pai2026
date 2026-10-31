"""Wait for this fixed batch, then independently verify. Never launches flights."""
import datetime,json,subprocess,sys,time
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def status(stage,**extra):
    o=dict(stage=stage,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra)
    (W/'receipt_offline_status.json').write_text(json.dumps(o,indent=2),encoding='utf-8')
    print(json.dumps(o),flush=True)
def run(name,args=()):
    status('verifying',script=name)
    with (W/'logs'/('receipt_'+name+'.log')).open('x',encoding='utf-8') as f:
        p=subprocess.run([sys.executable,'-B','-X','utf8',str(W/'scripts'/name),*args],stdout=f,stderr=subprocess.STDOUT,timeout=600)
    if p.returncode:raise RuntimeError((name,p.returncode))
def main():
    status('waiting_for_fixed_flights')
    while True:
        p=W/'receipt_validation_status.json'
        try:s=read(p)
        except (OSError,json.JSONDecodeError):time.sleep(5);continue
        if s['stage']=='flights_complete':break
        if s['stage'] in ['execution_error','infrastructure_error','deadline_reserve']:
            status('flight_batch_incomplete',batch=s);return
        time.sleep(10)
    run('verify_receipt.py')
    run('summarize_receipt.py')
    run('describe_receipt_failures.py')
    run('trial_index_receipt.py')
    run('report_bounded_execution.py')
    report=read(W/'results/all_trials_receipt.json')
    status('verified_evidence_ready',completed=report['completed'],goal_met=report['preregistered_goal_met'],
           documents_not_generated=True,no_flight_retries=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:
        status('offline_verification_error',error=repr(e));raise
