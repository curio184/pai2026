"""Finish training-only data preparation; never start training or move files."""
import argparse,datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
import psutil
os.environ['PYTHONUTF8']='1'
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf8')
def status(stage,**kw):
    v=dict(stage=stage,updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw);write(W/'prepare_train05_status.json',v);print(json.dumps(v),flush=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--render-pid',type=int,required=True);args=ap.parse_args()
    proc=psutil.Process(args.render_pid)
    assert any(x.replace('\\','/').endswith('v11_color/scripts/render_training05.py') for x in proc.cmdline())
    status('waiting_for_render',pid=proc.pid,created=proc.create_time())
    start=time.monotonic()
    while proc.is_running():
        if time.monotonic()-start>2400:raise RuntimeError('Render wait deadline exceeded; preserve outputs and inspect')
        time.sleep(5)
    frames=read(W/'protocol/train05_training_frames.json')
    assert len(frames)==2000 and all((W/'data/rendered05_png'/f'{f["id"]:05d}.png').is_file() for f in frames)
    status('building_dataset',images=2000)
    with (W/'logs/build_dataset05_en.log').open('x',encoding='utf8') as log:
        result=subprocess.run([sys.executable,'-X','utf8',str(W/'scripts/build_dataset05_en.py')],stdout=log,stderr=subprocess.STDOUT)
    assert result.returncode==0,'Dataset preparation failed; keep partial outputs'
    names=['train05_en.py','build_dataset05_en.py','register_train05_en.py','render_training05.py','pipeline_train05_en.py','run_round02_english.py','run_suite_english.py','verify_saved_training.py','verify_suite_records.py','phase_diagnostics.py','failure_details.py','summarize_round02_english.py','trial_index_round02_english.py','verify_records_round02_english.py','render_probe_round02_english.py','run_probe_round02_english.py','plot_probe_round02_english.py','verify_probe_consistency.py','verify_runtime_instructions.py']
    lock=W/'protocol/train05_english_implementation.json';assert not lock.exists()
    write(lock,dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(W/'protocol/train05_english.json'),trainer_sha256=sha(W/'scripts/train05_en.py'),dataset_audit_sha256=sha(W/'data/dataset05_en/audit.json'),addendum_sha256=sha(W/'protocol/train05_state_pair_addendum.json'),runtime_lock_sha256=sha(W/'protocol/runtime_english_lock.json'),scripts={n:sha(W/'scripts'/n) for n in names},training_started=False,final_evaluation_started=False))
    status('data_ready',samples=read(W/'data/dataset05_en/manifest.json')['samples'],implementation_sha256=sha(lock),training_started=False,moves_performed=False,minimum_free_gib_before_training=7.4)
if __name__=='__main__':
    try:main()
    except BaseException as exc:status('preparation_error',error=repr(exc));raise
