"""Finish preregistered evidence after the live flight pipeline exits.

No training restart, PDF completion claim, Git mutation, or upload.
"""
import argparse, datetime, json, subprocess, sys, time
from pathlib import Path
import psutil

W=Path(__file__).resolve().parents[1]
PLOT=Path('C:/Temp/pai2026_submission/check_env/Scripts/python.exe')
BLENDER='C:/Program Files/Blender Foundation/Blender 3.1/blender.exe'

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def status(stage,**kwargs):
    obj=dict(stage=stage,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kwargs)
    (W/'post_pipeline_status.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(obj,ensure_ascii=False),flush=True)

def run(stage,command):
    status(stage,state='running')
    with (W/'logs'/('post_'+stage+'.log')).open('x',encoding='utf-8') as log:
        completed=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    if completed.returncode:raise RuntimeError(f'{stage} returned {completed.returncode}; attempt preserved')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pipeline-pid',type=int,required=True);parser.add_argument('--status-file',default='pipeline_status.json');a=parser.parse_args()
    process=psutil.Process(a.pipeline_pid)
    assert any(str(arg).replace('\\','/').endswith(('v11_color/scripts/pipeline.py','v11_color/scripts/pipeline_train02.py','v11_color/scripts/pipeline_train03.py')) for arg in process.cmdline())
    status('wait_for_pipeline',pid=process.pid,process_created=process.create_time(),state='live_process_verified')
    while process.is_running():time.sleep(5)
    terminal=read(W/a.status_file)
    if terminal['stage']!='flight_evidence_ready':
        status('development_needs_review',pipeline=terminal,automatic_retraining=False);return
    selected=read(W/'protocol/selected_final.json')
    run('known_failure',[sys.executable,str(W/'scripts/run_known_failure.py')])
    known=W/'runs'/('known_failure_'+selected['candidate'])/'summary.json'
    if any(c.get('error') for c in read(known)['cases']):raise RuntimeError('Known-failure regression had infrastructure error; preserve and investigate')
    run('render_probe',[BLENDER,'--factory-startup','--background','--python',str(W/'scripts/render_probe.py')])
    run('probe_inference',[sys.executable,str(W/'scripts/run_probe.py')])
    run('probe_figure',[str(PLOT),str(W/'scripts/plot_probe.py')])
    run('summarize',[sys.executable,str(W/'scripts/summarize.py')])
    run('trial_index',[sys.executable,str(W/'scripts/trial_index.py')])
    run('rescore',[sys.executable,str(W/'scripts/verify_records.py'),'--output',str(W/'reports/all_records_verified.json')])
    result=read(W/'results/all_trials.json')
    if not result['preregistered_goal_met']:
        status('results_need_review',goal_met=False,automatic_retraining=False);return
    run('readme',[sys.executable,str(W/'scripts/prepare_readme.py')])
    status('evidence_and_readme_ready',pdf_review_pending=True,published=False)

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        status('post_pipeline_error',error=repr(exc));raise
