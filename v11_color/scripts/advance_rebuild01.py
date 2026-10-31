"""Advance only after completed development and independent verification; no retries."""
import datetime,json,subprocess,sys,time
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def status(stage,**extra):
    data=dict(stage=stage,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra)
    (W/'rebuild10h_advancement.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps(data),flush=True)
def run(script,args=(),timeout=300):
    status('running',script=script)
    with (W/'logs'/('rebuild01_advance_'+script+'.log')).open('x',encoding='utf-8') as log:
        result=subprocess.run([sys.executable,'-B','-X','utf8',str(W/'scripts'/script),*args],stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
    if result.returncode:raise RuntimeError((script,result.returncode))
def main():
    status('waiting_for_development')
    while True:
        try:
            s=read(W/'runs/rebuild01_expanded/summary.json')
            if any(r.get('error') for r in s['cases']):status('development_infrastructure_error');return
            if s['completed']==23:break
        except (OSError,json.JSONDecodeError):pass
        time.sleep(10)
    if not all(r['success'] for r in s['cases']):status('development_failure_requires_analysis',successes=sum(r['success'] for r in s['cases']),total=23);return
    run('audit_rebuild01_execution.py',['rebuild01_expanded','--output','rebuild01_expanded_execution_verified.json'],600)
    run('prepare_rebuild01_final.py')
    run('run_rebuild01_final.py',timeout=4*3600)
    status('final_flights_and_probe_finished')
if __name__=='__main__':
    try:main()
    except BaseException as e:status('advancement_error',error=repr(e));raise
