"""One fixed confirmation; no optimisation, selection or automatic retries."""
import datetime,json,os,subprocess,sys
from pathlib import Path
from run_suite_control_v11 import W,P,PY,BLENDER,sha,write,run_case,lock_check

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def now():return datetime.datetime.now(datetime.timezone.utc)
def status(stage,**extra):
    obj=dict(stage=stage,updated_utc=now().isoformat(),**extra)
    write(W/'control_v11_final_status.json',obj);print(json.dumps(obj),flush=True)
def check(plan):
    assert sha(W/'protocol/runtime_control_v11_lock.json')==plan['runtime_lock_sha256']
    for name,h in plan['scripts'].items():assert sha(W/'scripts'/name)==h,name
    lock_check()
def main():
    plan=read(W/'protocol/control_v11_final.json');deadline=datetime.datetime.fromisoformat(plan['deadline_utc'])
    root=W/'runs/control_v11_final';root.mkdir(exist_ok=False)
    old=P/read(W/'protocol/plan.json')['training']['initial_checkpoint']
    new=W/'models'/plan['candidate']/'final'
    assert sha(old/'model.safetensors')==plan['old_checkpoint_sha256']
    assert sha(new/'model.safetensors')==plan['checkpoint_sha256']
    check(plan);write(root/'suite_plan.json',plan)
    outcomes=[]
    for c in plan['cases']:
        # Bound a whole case's existing startup+flight+scoring timeouts.
        if (deadline-now()).total_seconds()<840:
            status('deadline_reserve',completed=len(outcomes),planned=len(plan['cases']),no_retry=True);return
        check(plan)
        status('flight',case=c['id'],model=c['model'],group=c['group'],completed=len(outcomes),planned=len(plan['cases']))
        result=run_case(c,new if c['model']=='v1.1' else old,root/(c['id']+'_'+c['model']))
        outcomes.append(result)
        write(root/'summary.json',dict(completed=len(outcomes),planned=len(plan['cases']),
              cases=outcomes,configuration='control_v11',protocol_sha256=sha(W/'protocol/control_v11_final.json')))
        if result.get('error'):
            status('infrastructure_error',completed=len(outcomes),error=result['error'],record=result['record'],automatic_retry=False);return
    status('flights_complete',completed=len(outcomes),planned=42)
    for stage,command in [
        ('static_images',[BLENDER,'--factory-startup','--background','--python',str(W/'scripts/render_probe_control_v11.py')]),
        ('static_inference',[str(PY),'-B','-X','utf8',str(W/'scripts/run_probe_control_v11.py')]),
        ('static_figures',[r'C:\Temp\pai2026_submission\check_env\Scripts\python.exe','-B','-X','utf8',str(W/'scripts/plot_probe_control_v11.py')])]:
        if now()>=deadline:status('deadline_before_static',pending=stage);return
        check(plan);status(stage)
        with (W/'logs'/('control_v11_'+stage+'.log')).open('x',encoding='utf-8') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,
                                  timeout=max(1,(deadline-now()).total_seconds()))
        if result.returncode:status('static_processing_error',step=stage,returncode=result.returncode);return
    status('evidence_complete_documents_pending',flight_cases=42,static_probe='probe_control_v11/outputs/summary.json')

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        status('execution_error',error=repr(exc),automatic_retry=False)
        raise
