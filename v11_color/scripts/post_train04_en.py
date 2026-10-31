"""Collect both evaluation rounds after the verified live English pipeline exits."""
import argparse,datetime,json,subprocess,sys,time
from pathlib import Path
import psutil
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def status(stage,**kw):
    r=dict(stage=stage,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw)
    (W/'post_train04_en_status.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r),flush=True)
def run(stage,script,*args):
    status(stage,state='running')
    with (W/'logs'/('post04_en_'+stage+'.log')).open('x',encoding='utf-8') as output:
        result=subprocess.run([sys.executable,str(W/'scripts'/script),*args],stdout=output,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(stage+' failed; keep evidence and investigate')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pipeline-pid',required=True,type=int);a=parser.parse_args()
    process=psutil.Process(a.pipeline_pid)
    assert any(arg.replace('\\','/').endswith('v11_color/scripts/pipeline_train04_en.py') for arg in process.cmdline())
    status('wait_for_pipeline',pid=process.pid,process_created=process.create_time(),state='live_process_verified')
    while process.is_running():time.sleep(5)
    terminal=read(W/'pipeline_train04_en_status.json')
    run('summarize','summarize_round02_english.py')
    run('index','trial_index_round02_english.py')
    # The original pipeline verifier targets the preserved round-1 report.
    # This additional verifier reads the new all-trial report and covers both rounds.
    run('all_record_rescore','verify_records_round02_english.py','--output',str(W/'reports/train04_en_all_records_verified.json'))
    run('verified_summary','summarize_round02_english.py')
    report=read(W/'results/all_trials_round02_english.json')
    if not report['preregistered_goal_met']:
        status('results_need_review',pipeline_terminal=terminal,goal_met=False,automatic_retraining=False);return
    run('readme','prepare_readme_round02_english.py')
    status('evidence_and_readme_ready',pdf_and_publication_review_pending=True,published=False)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        status('post_pipeline_error',error=repr(exc));raise
