"""Preregister runtime-noise calibration after all train10 development trials."""
import copy,datetime,hashlib,json,shutil
from pathlib import Path
from run_suite_english import lock_check
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (W/'models/train11_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*')) and not (W/'probe_round02_english/outputs').exists()
dev=read(W/'runs/dev_train10_en/summary.json');stress=read(W/'runs/stress_train10_en/summary.json')
assert dev['completed']==dev['planned']==dev['successes']==8
assert stress['completed']==stress['planned']==16 and stress['successes']==12
assert read(W/'reports/train10_en_all_records_verified.json')['evidence_consistent']
diagnostic=W/'reports/stress_train10_en_postflight_development_diagnostic.json'
assert read(diagnostic)['completed']==16
lock_check()
plan=copy.deepcopy(read(W/'protocol/train10_english.json'))
plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train11_en',
    previous_training_plan_sha256=sha(W/'protocol/train10_english.json'),
    prior_results=dict(development=[8,8],stress=[12,16],selected=False),
    diagnosis_sha256=sha(diagnostic),full_suite_diagnosis_sha256=sha(diagnostic))
plan['training'].update(initial_checkpoint='v11_color/models/train10_en/final',
    initial_checkpoint_sha256=read(W/'models/train10_en/result.json')['checkpoint_sha256'],
    output='models/train11_en',steps=6000,seed=2026103011,learning_rate=1e-5,
    source_dataset_audit_sha256=sha(W/'data/dataset10_en/audit.json'),
    data='Reuse audited dataset10 exactly; no new images, states or labels.',
    noise_schedule='For step=1..6000 and micro=0..1, use the frozen runtime Gaussian realization if (step+micro)%4<2, otherwise fresh random noise. 50% each. Existing common-noise quartet rules and flow-time schedule unchanged.',
    runtime_noise_seed=20261024,
    rationale='Residual action error against the existing teacher remains during hover and yaw settling. Test calibration to the already fixed runtime flow-noise realization, retaining random-noise training. No inference/scoring/controller changes.')
plan['teacher']['reason']='Teacher10 retained byte-for-byte; this attempt changes training noise sampling only, alongside its preregistered continuation seed and 6000-step schedule.'
plan['data'].update(source='data/dataset10_en',source_audit_sha256=sha(W/'data/dataset10_en/audit.json'),
    unchanged='All images, states, English prompts, labels, splits, sampling pools, batch proportions, flow-time schedule, loss weights, runtime and scoring.')
plan['hypotheses_not_results']=[
    'Train10 passed basic8/8 but stress12/16. Failures: H06 disarm after prolonged hover; H07 physical initial hover2.20525s; H12 target-not-found after yaw overshoot; H15 physical target hold2.88675s.',
    'Postflight teacher comparison indicates residual horizontal and yaw errors. This does not prove a unique cause or that noise calibration will fix them.',
    'For H12, saved images37/41/47 show red leaving the left frame edge. Recorded relative yaw reaches1.826rad versus pi/2 target, while predicted corrective yaw remains small. No detector change.',
    'Only development records informed the training design. No evaluation images or states are used as training examples; the fresh final round remains unexposed.',
    'Runtime uses a fixed flow seed by prior design. Results will not establish robustness to arbitrary flow-noise seeds. No score thresholds or evaluation seeds are changed.']
plan['storage']=dict(project_root=str(W.parent),free_bytes=shutil.disk_usage(W).free,
    archival_compression_status_sha256=sha(W/'reports/archive_compression/status.json'),
    legacy_compression_status_sha256=sha(W/'reports/legacy_model_compression/status.json'))
assert plan['storage']['free_bytes']>=plan['training']['minimum_free_gib_before_training']*1024**3
plan['registration_script_sha256']=sha(Path(__file__))
out=W/'protocol/train11_english.json';assert not out.exists();out.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(plan_sha256=sha(out),steps=6000,dataset_unchanged=True,fresh_final_unexposed=True)))
