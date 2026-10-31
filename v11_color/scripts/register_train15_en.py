"""Preregister the candidate15 recipe before new targets or optimization."""
import copy,datetime,hashlib,json,shutil
from pathlib import Path
from run_suite_english import lock_check
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (W/'models/train15_en').exists() and not (W/'data/dataset15_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*')) and not (W/'probe_round02_english/outputs').exists()
assert read(W/'pipeline_train14_en_status.json')['stage']=='development_review'
dev=read(W/'runs/dev_train14_en/summary.json')
assert dev['completed']==dev['planned']==8 and dev['successes']==6
assert read(W/'reports/train14_en_all_records_verified.json')['evidence_consistent']
diagnostic=W/'reports/train14_failure_analysis.json'
assert sha(diagnostic)=='5effe9e09f83461bf0564c56465ecb5d23ad163ae1c2bda34830e822bee737f8'
lock_check()
plan=copy.deepcopy(read(W/'protocol/train14_english.json'))
plan.pop('fit_diagnosis_sha256',None)
plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train15_en',
    previous_training_plan_sha256=sha(W/'protocol/train14_english.json'),diagnosis_sha256=sha(diagnostic),
    full_suite_diagnosis_sha256=sha(W/'reports/dev_train14_en_postflight_development_diagnostic.json'),
    teacher_source_sha256=sha(W/'scripts/teacher_flight15.py'),inherited_teacher_source_sha256=sha(W/'scripts/teacher_flight14.py'),
    prior_results=dict(development=[6,8],search_goal_hold=[4,4],initial_hover=[8,8],failed_rotation_stability=2,selected=False))
source_sha=sha(W/'data/dataset14_en/audit.json')
plan['training'].update(initial_checkpoint='v11_color/models/train14_en/final',
    initial_checkpoint_sha256=read(W/'models/train14_en/result.json')['checkpoint_sha256'],output='models/train15_en',
    steps=6000,seed=2026103015,source_dataset_audit_sha256=source_sha,braking_coefficient=.6,
    minimum_free_gib_before_training=10.,recovery_interval_steps=2000,
    noise_schedule='For step1..6000 and micro0..1, fixed runtime Gaussian if (step+micro)%4<2, otherwise random; same 50/50 as14.',
    data='Same dataset14 images, states, tasks and sampling. Relabel stationary xy only.',
    rationale='Both14 failures show growing translation oscillations during rotation, despite close teacher imitation. Reduce training-only stationary braking1.6->0.6; retain every navigation/landing/yaw/vertical/request target.')
plan['teacher'].update(braking_coefficient=.6,
    stationary_horizontal_command='-0.6 * input estimated horizontal velocity; norm cap0.2m/s, constant32steps. Zero unarmed or takeoff below0.25m.',
    nonhorizontal_labels='All nonhorizontal, all navigation, and all landing labels remain byte-identical to14.',
    reason='Captured velocity is delayed at execution. Lower feedback magnitude is a delay-stability hypothesis supported by14 saved oscillations; no unique causality or flight success is claimed.')
plan['data'].update(source='data/dataset14_en',source_audit_sha256=source_sha,
    unchanged='All image/state/task inputs, English prompts, sampling, loss, inference, all navigation/landing/nonhorizontal labels, runtime, gains, detectors, manager and scoring.')
plan['hypotheses_not_results']=[
    'Milder learned stationary requests may reduce observed delayed-feedback oscillation while preserving14 navigation behavior.',
    'The illustrative dv/dt=-v-k*v(t-delay) model motivates k<1; it is not a verified drone plant model or proof of real-flight stability.',
    '6000 steps and a new seed also change the policy, so isolated causal attribution is unavailable.',
    'All eight development cases must pass before16stress cases. Original gates, final-round conditions and all failure reporting remain unchanged.',
    'No evaluation image/state is added to training. Final round02 remains unexposed. Final step only; no automatic performance retries.']
plan['storage']=dict(project_root=str(W.parent),free_bytes_at_registration=shutil.disk_usage(W).free,
    training_must_wait_until_free_gib=10.,protected_final_models_and_all_trial_records_preserved=True)
plan['registration_script_sha256']=sha(Path(__file__))
out=W/'protocol/train15_english.json';assert not out.exists();out.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(plan_sha256=sha(out),steps=6000,fresh_final_unexposed=True,training_not_started=True)))
