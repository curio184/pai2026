"""Finish offline evidence only. No inference, flight, tuning, upload or retries."""
import datetime,json,subprocess,sys,time
from pathlib import Path

W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    logdir=W/'logs/navfocus_offline';logdir.mkdir(exist_ok=True)
    statusfile=W/'navfocus_offline_status.json'
    def status(stage,**kwargs):
        result=dict(stage=stage,updated_utc=now(),**kwargs)
        statusfile.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result),flush=True)
    terminal={'evidence_complete_documents_pending','deadline_reserve','deadline_before_static',
              'infrastructure_error','static_processing_error','execution_error'}
    status('waiting_for_fixed_validation')
    while True:
        state=read(W/'navfocus_final_status.json')
        if state['stage'] in terminal:break
        time.sleep(5)
    complete=state['stage']=='evidence_complete_documents_pending'
    steps=[('verify_navfocus.py',[] if complete else ['--partial']),
           ('describe_navfocus_failures.py',[]),('report_bounded_execution.py',[])]
    if complete:steps.append(('verify_probe_navfocus.py',[]))
    steps.extend([('summarize_navfocus.py',[]),('trial_index_navfocus.py',[])])
    for script,args in steps:
        status('offline_verification',script=script)
        with (logdir/(script+'.log')).open('w',encoding='utf-8') as log:
            r=subprocess.run([sys.executable,'-B','-X','utf8',str(W/'scripts'/script),*args],stdout=log,stderr=subprocess.STDOUT)
        if r.returncode:
            status('verification_error',script=script,returncode=r.returncode);return
    result=read(W/'results/all_trials_navfocus.json')
    status('offline_evidence_ready',completed=result['completed'],goal_met=result['preregistered_goal_met'],
           flight_gate=result['closed_loop_gate_met'],regression_gate=result['regression_gate_met'],
           intervention_gate=result['color_intervention_gate_met'],known_failure_gate=result['known_failure_retest_passed'])
if __name__=='__main__':main()
