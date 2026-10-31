"""Operational amendment only: restore the latest complete save, not a new recipe."""
import ast,datetime,difflib,hashlib,json,shutil
from pathlib import Path
from run_suite_english import lock_check
W=Path(__file__).resolve().parents[1];M=W/'models/train13_en'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock_check()
old=W/'scripts/train13_en.py';resume=W/'scripts/train13_resume01.py'
assert not (M/'result.json').exists() and not (M/'final').exists()
assert not (W/'runs/dev_train13_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*')) and not (W/'probe_round02_english/outputs').exists()
failure=read(M/'failure.json');assert failure['attempted_step']==2000 and 'PermissionError' in failure['error']
integrity=W/'reports/train13_interrupted_save_integrity.json';audit=read(integrity)
latest=max(audit['files'],key=lambda r:r['step']);assert latest['step']==2000 and latest['file']=='recovery.pt.tmp'
assert sha(M/latest['file'])==latest['sha256']
implementation=read(W/'protocol/train13_english_implementation.json')
for n,h in implementation['scripts'].items():assert sha(W/'scripts'/n)==h,n
def fn(path,name):
    tree=ast.parse(path.read_text(encoding='utf8'))
    return ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
assert fn(old,'weighted_loss')==fn(resume,'weighted_loss')
assert fn(old,'frozen_vlm_digest')==fn(resume,'frozen_vlm_digest')
diff=''.join(difflib.unified_diff(old.read_text().splitlines(True),resume.read_text().splitlines(True),fromfile=old.name,tofile=resume.name))
diffpath=W/'protocol/train13_resume01.diff';assert not diffpath.exists();diffpath.write_text(diff,encoding='utf8')
record=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train13_en',
    classification='Operational recovery, same registered training recipe',
    cause='torch.save completed but os.replace(recovery.pt.tmp,recovery.pt) failed with Windows access denied. Specific holder/cause unknown.',
    recovery_file=latest['file'],recovery_sha256=latest['sha256'],resume_step=2000,final_step=6000,
    selection='Latest integrity-checked completed step only; no intermediate checkpoint evaluated.',
    restore=['all155 trainable tensors','AdamW states and parameter groups','NumPy sampler RNG','PyTorch CPU RNG','all CUDA RNGs','image/task/language exposure counters'],
    unchanged=['seed','images/states/prompts/labels','sampler','flow noise/time schedule','loss','optimizer hyperparameters','6000 total steps','runtime/controller/detector/manager','success criteria','development/regression/final trial conditions'],
    new_save_policy='Write once to a unique recovery_resume01_stepNNNNN.pt and checksum receipt at each remaining1000-step boundary; no replacement of existing files.',
    original_plan_sha256=sha(W/'protocol/train13_english.json'),original_implementation_sha256=sha(W/'protocol/train13_english_implementation.json'),
    original_trainer_sha256=sha(old),resume_trainer_sha256=sha(resume),resume_pipeline_sha256=sha(W/'scripts/pipeline_train13_resume01.py'),
    integrity_audit_sha256=sha(integrity),failure_sha256=sha(M/'failure.json'),original_training_log_sha256=sha(M/'training.jsonl'),
    difference_sha256=sha(diffpath),free_bytes=shutil.disk_usage(W).free,
    prior_files_preserved=True,performance_trials_before_resume=0,optimizer_updates_after_interruption=0)
out=W/'protocol/train13_resume01.json';assert not out.exists();out.write_text(json.dumps(record,indent=2),encoding='utf8')
print(json.dumps(dict(amendment_sha256=sha(out),resume_step=2000,remaining_steps=4000,final_step=6000)))
