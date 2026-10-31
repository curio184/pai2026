"""Sequential authorized work; stop on infrastructure errors or development failure."""
import json,subprocess,sys,time,datetime
from pathlib import Path
from PIL import Image
W=Path(__file__).resolve().parents[1]
def write(obj):
    obj['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (W/'pipeline_status.json').write_text(json.dumps(obj,indent=2));print(json.dumps(obj),flush=True)
def run(name,args):
    write(dict(stage=name,state='running'))
    with (W/'logs'/(name+'.log')).open('x',encoding='utf-8') as log:
        p=subprocess.run([sys.executable,*map(str,args)],stdout=log,stderr=subprocess.STDOUT)
    if p.returncode:raise RuntimeError(f'{name} returned {p.returncode}; preserve attempt and inspect log')
try:
    write(dict(stage='rendering',state='waiting_for_4000_training_frames'))
    while True:
        files=list((W/'data/rendered_png').glob('*.png'))
        if len(files)==4000:
            for p in files:
                with Image.open(p) as im:im.verify()
            break
        if not (W/'logs/render_full.log').exists():raise RuntimeError('Missing render log')
        # A stopped Blender must be investigated; do not silently change data or restart.
        log=(W/'logs/render_full.log').read_text(encoding='utf-16',errors='replace')
        if 'Blender quit' in log and 'COLOR_RENDER_FINISHED' not in log:raise RuntimeError('Renderer ended incompletely')
        time.sleep(10)
    run('dataset',[W/'scripts/build_dataset.py'])
    run('train01',[W/'scripts/train.py'])
    run('dev_train01',[W/'scripts/run_suite.py','dev'])
    dev=json.loads((W/'runs/dev_train01/summary.json').read_text(encoding='utf-8'))
    if dev['successes']!=8:
        write(dict(stage='development_review',state='needs_analysis',completed=dev['completed'],successes=dev['successes'],heldout_not_started=True));sys.exit(2)
    run('regression_train01',[W/'scripts/run_suite.py','regression'])
    reg=json.loads((W/'runs/regression_train01/summary.json').read_text(encoding='utf-8'))
    if reg['successes']!=5:
        write(dict(stage='regression_review',state='needs_analysis',successes=reg['successes'],heldout_not_started=True));sys.exit(2)
    run('heldout_train01',[W/'scripts/run_suite.py','heldout'])
    write(dict(stage='flight_evidence_ready',state='needs_analysis_and_documents'))
except Exception as e:
    write(dict(stage='pipeline_error',error=repr(e)));raise
