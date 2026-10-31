"""Second preregistered development attempt; no automatic further retraining."""
import datetime,json,subprocess,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def status(stage,**kw):
    obj=dict(stage=stage,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw)
    (W/'pipeline_train02_status.json').write_text(json.dumps(obj,indent=2),encoding='utf-8');print(json.dumps(obj),flush=True)
def run(stage,script,*args):
    status(stage,state='running')
    with (W/'logs'/('pipeline02_'+stage+'.log')).open('x',encoding='utf-8') as log:
        result=subprocess.run([sys.executable,str(W/'scripts'/script),*args],stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(f'{stage} returned {result.returncode}; preserve and investigate')
try:
    assert read(W/'runs/dev_train01/summary.json')['completed']==8
    assert not (W/'models/train02').exists()
    run('train02','train02.py')
    run('dev_train02','run_suite.py','dev','--candidate','train02')
    dev=read(W/'runs/dev_train02/summary.json')
    if dev['successes']!=8:
        status('development_review',state='needs_analysis',completed=dev['completed'],successes=dev['successes'],heldout_not_started=True);sys.exit(0)
    run('regression_train02','run_suite.py','regression','--candidate','train02')
    reg=read(W/'runs/regression_train02/summary.json')
    if reg['successes']!=5:
        status('regression_review',state='needs_analysis',successes=reg['successes'],heldout_not_started=True);sys.exit(0)
    run('heldout_train02','run_suite.py','heldout','--candidate','train02')
    status('flight_evidence_ready',state='needs_analysis_and_documents')
except Exception as e:
    status('pipeline_error',error=repr(e));raise
