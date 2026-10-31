"""Wait for the existing pipeline, then finish read-only offline diagnostics.

Never starts a flight or training; never restarts a missing process. The process
identity, candidate, suite completion and existing independent rescore are checked.
"""
import datetime
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
import psutil

W=Path(__file__).resolve().parents[1]
PLOT='C:/Temp/pai2026_submission/check_env/Scripts/python.exe'
PID=33644
CREATED=1793347134.7165525
status_file=W/'reports/train15_postflight_completion_status.json'
def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def status(stage,**kwargs):
    d=dict(updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stage=stage,**kwargs)
    status_file.write_text(json.dumps(d,indent=2),encoding='utf8')
    print(json.dumps(d),flush=True)

def main():
    assert not status_file.exists()
    jobs=[
      ('teacher','diagnose_train15_postflight.py',[], 'stress_train15_en_postflight_development_diagnostic.json'),
      ('geometry','diagnose_search_geometry.py',['--suite','stress_train15_en'],'stress_train15_en_perception_diagnostic.json'),
      ('power','diagnose_power_margin.py',['--suite','stress_train15_en'],'stress_train15_en_power_diagnostic.json'),
      ('stationary','diagnose_stationary_estimator_full_v2.py',[],'stress_train15_en_stationary_full_v2.json'),
      ('summary','analyze_train15_failure.py',[],'train15_failure_analysis.json')]
    pins={script:sha(W/'scripts'/script) for _,script,_,_ in jobs}
    try:
        process=psutil.Process(PID)
        assert abs(process.create_time()-CREATED)<.01
    except psutil.NoSuchProcess:
        process=None
    status('waiting_for_existing_pipeline',pipeline_pid=PID,script_hashes=pins)
    while process is not None and process.is_running():
        assert abs(process.create_time()-CREATED)<.01
        time.sleep(20)
    state=read(W/'pipeline_train15_en_status.json')
    assert state['stage']=='development_review' and state['failed_suite']=='stress',state
    suite=read(W/'runs/stress_train15_en/summary.json')
    assert suite['completed']==suite['planned']==16
    assert read(W/'reports/train15_en_all_records_verified.json')['evidence_consistent']
    for name,script,args,output in jobs:
        assert sha(W/'scripts'/script)==pins[script]
        assert not (W/'reports'/output).exists(),output
        status(name,script=script)
        with (W/'logs'/('postflight15_'+name+'.log')).open('x',encoding='utf8') as log:
            p=subprocess.run([PLOT,'-B','-X','utf8',str(W/'scripts'/script),*args],stdout=log,stderr=subprocess.STDOUT)
        assert p.returncode==0,(name,p.returncode)
        assert (W/'reports'/output).exists()
    status('complete',stress_successes=suite['successes'],stress_planned=16,
           report=str(W/'reports/train15_failure_analysis.json'),
           report_sha256=sha(W/'reports/train15_failure_analysis.json'),
           training_or_new_flights_started=False)

if __name__=='__main__':
    try: main()
    except BaseException as exc:
        status('error',error=repr(exc))
        raise
