"""Freeze the next candidate only after the entire train07 development suite ends."""
import copy,datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (W/'models/train08_en').exists() and not (W/'data/dataset08_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*'))
assert not (W/'probe_round02_english/outputs').exists()
prior=read(W/'runs/dev_train07_en/summary.json');assert prior['completed']==prior['planned']==8
assert prior['successes']<8
assert read(W/'reports/train07_en_all_records_verified.json')['evidence_consistent']
plan=copy.deepcopy(read(W/'protocol/train07_english.json'))
plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train08_en',
    previous_training_plan_sha256=sha(W/'protocol/train07_english.json'),
    prior_results=dict(development=[prior['successes'],8],stress_not_started=True,selected=False),
    diagnosis_sha256=sha(W/'reports/train07_dev02_clearance_development_diagnostic.json'),
    full_suite_diagnosis_sha256=sha(W/'reports/dev_train07_en_failure_details.json'),
    teacher_source_sha256=sha(W/'scripts/teacher_flight08.py'))
plan['training'].update(initial_checkpoint='v11_color/models/train07_en/final',
    initial_checkpoint_sha256=read(W/'models/train07_en/result.json')['checkpoint_sha256'],
    output='models/train08_en',steps=4000,seed=2026102911,learning_rate=1e-5,
    source_dataset_audit_sha256=sha(W/'data/dataset07_en/audit.json'),teacher_standoff_m=1.,
    data='Same pixels/states/sampling and teacher laws as train07 except approach teacher standoff restored to 1.0m. The score goal remains 0.9m.')
plan['teacher'].update(teacher_standoff_m=1.,
    reason='A completed development mission met the target stop but drifted to 0.4468m from a person during landing, failing the unchanged 0.45m clearance. Restore a 10cm teacher safety margin before landing; do not relax success criteria or alter runtime.')
plan['data'].update(source='data/dataset07_en',source_audit_sha256=sha(W/'data/dataset07_en/audit.json'))
plan['hypotheses_not_results']=[
    'A 10cm teacher standoff margin reduces post-stop/landing proximity while retaining the sharper approach teacher and zero horizontal hold targets. This has not yet been verified for the new candidate.',
    'All primitive, stressed, video, known-failure, fresh paired and color-intervention gates remain required; no checkpoint or trial is selected by outcome.']
plan['storage']=dict(project_root=str(W.parent),free_bytes=shutil.disk_usage(W).free)
plan['registration_script_sha256']=sha(Path(__file__))
out=W/'protocol/train08_english.json';assert not out.exists();out.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(plan_sha256=sha(out),steps=4000,prior_successes=prior['successes'])))
