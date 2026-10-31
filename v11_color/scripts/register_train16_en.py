"""Register candidate16 only after all candidate15 evidence is complete."""
import copy
import datetime
import hashlib
import json
import shutil
from pathlib import Path
from run_suite_english import lock_check
from run_round02_english import stress_pass

W=Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

assert not (W/'models/train16_en').exists() and not (W/'data/dataset16_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*'))
assert not (W/'probe_round02_english/outputs').exists()
assert read(W/'pipeline_train15_en_status.json')['stage']=='development_review'
assert read(W/'reports/train15_postflight_completion_status.json')['stage']=='complete'
dev=read(W/'runs/dev_train15_en/summary.json')
stress=read(W/'runs/stress_train15_en/summary.json')
assert dev['completed']==dev['planned']==dev['successes']==8
assert stress['completed']==stress['planned']==16 and not stress_pass(stress)
assert read(W/'reports/train15_en_all_records_verified.json')['evidence_consistent']
diagnostic=W/'reports/train15_failure_analysis.json'
assert read(diagnostic)['stress_successes']==stress['successes']
lock_check()
plan=copy.deepcopy(read(W/'protocol/train15_english.json'))
plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), candidate='train16_en',
    previous_training_plan_sha256=sha(W/'protocol/train15_english.json'),
    diagnosis_sha256=sha(diagnostic),
    full_suite_diagnosis_sha256=sha(W/'reports/stress_train15_en_postflight_development_diagnostic.json'),
    teacher_source_sha256=sha(W/'scripts/teacher_flight16.py'),
    inherited_teacher_source_sha256=sha(W/'scripts/teacher_flight15.py'),
    prior_results=dict(development=[8,8],stress=[stress['successes'],16],selected=False))
source_sha=sha(W/'data/dataset15_en/audit.json')
plan['training'].pop('braking_coefficient',None)
plan['training'].update(initial_checkpoint='v11_color/models/train15_en/final',
    initial_checkpoint_sha256=read(W/'models/train15_en/result.json')['checkpoint_sha256'],
    output='models/train16_en',steps=6000,seed=2026103016,source_dataset_audit_sha256=source_sha,
    data='Same dataset15 images, states, tasks and sampling. Relabel stationary horizontal targets only.',
    noise_schedule='For steps1..6000 and micro0..1, fixed runtime Gaussian if (step+micro)%4<2, otherwise random; same50/50 as15.',
    rationale='Candidate15 still drifts during stationary flight while closely imitating its velocity-only teacher. Existing attitude inputs provide a leaky proxy for preceding acceleration requests. Test this training-only hypothesis; no runtime modification.')
plan['teacher'].pop('braking_coefficient',None)
plan['teacher'].update(velocity_retention=.6,attitude_retention=.9,gravity_m_s2=9.81,
    stationary_horizontal_command='0.6*own[:2] - 0.9*9.81*tan(own[[5,4]]), norm cap0.2m/s, constant32steps. Zero unarmed or takeoff below0.25m.',
    attitude_convention='Inputs are autopilot FRD roll/pitch; output is forward/left velocity. No true bias, position, acceleration or history is added to model inputs.',
    nonhorizontal_labels='All nonhorizontal, all navigation, and all landing labels remain byte-identical to15.',
    reason='A leaky incremental-request approximation may reject sustained attitude-estimation disturbance while limiting delayed-feedback oscillation. Only a simplified linear model has been checked; actual flight success is unproven.')
plan['data'].update(source='data/dataset15_en',source_audit_sha256=source_sha,
    unchanged='All image/state/task inputs, English prompts, sampling, loss, inference, navigation/landing/nonhorizontal labels, runtime, gains, detectors, manager and scoring.')
plan['analytical_evidence']={name:sha(W/'reports'/name) for name in [
    'stationary_feedback_analysis01.json','stationary_feedback_analysis02.json',
    'train15_attitude_teacher_input_coverage.json','stress_train15_en_stationary_full_v2.json']}
plan['hypotheses_not_results']=[
    'The stationary teacher uses velocity and attitude already provided to SmolVLA. The real-time controller, its gains and all six action meanings are unchanged.',
    'Linear surrogate cases are not drone trials and cannot prove stability. All analytical trajectories are retained, including oscillatory cases.',
    'There is no perfect bias estimate: the attitude term is a noisy, delayed proxy. Saturation and model approximation may still fail.',
    'Navigation labels are preserved to isolate the stationary change; existing approach failures may remain. Training and a new seed also change behavior, so causality is not isolated.',
    'All started suites finish; unchanged gates precede the untouched final round. Final step only; no evaluation images or states are added to training.']
plan['storage']=dict(project_root=str(W.parent),free_bytes_at_registration=shutil.disk_usage(W).free,
    training_must_wait_until_free_gib=10.,protected_final_models_and_all_trial_records_preserved=True)
plan['registration_script_sha256']=sha(Path(__file__))
out=W/'protocol/train16_english.json'
assert not out.exists()
out.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(plan_sha256=sha(out),steps=6000,fresh_final_unexposed=True,training_not_started=True)))
