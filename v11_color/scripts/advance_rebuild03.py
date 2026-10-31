"""Advance the fixed validation after the already-running launcher check succeeds."""
import datetime,json,subprocess,sys,time
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def run(name,*args):
    print('START',name,flush=True)
    subprocess.run([sys.executable,'-B','-X','utf8',str(W/'scripts'/name),*args],check=True)
def main():
    target=W/'runs/rebuild03_primitive5/summary.json'
    for _ in range(600):
        if target.exists():break
        time.sleep(1)
    result=json.loads(target.read_text(encoding='utf-8'))
    assert result['completed']==1 and result['cases'][0]['success'],'Corrected primitive diagnostic did not pass'
    run('audit_rebuild03_execution.py','rebuild03_primitive5','--output','rebuild03_primitive5_execution_verified.json')
    run('prepare_rebuild03_final.py')
    run('run_rebuild03_final.py')
    run('audit_rebuild03_execution.py','rebuild03_final','--output','rebuild03_final_execution_verified.json')
    run('verify_probe_rebuild03.py')
    run('summarize_rebuild03.py')
    run('describe_rebuild03_failures.py')
    run('trial_index_rebuild03.py')
if __name__=='__main__':main()
