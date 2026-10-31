"""Register the next training recipe before relabeling or model optimization."""
import copy,datetime,hashlib,json,shutil
from pathlib import Path
from run_suite_english import lock_check
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (W/'models/train14_en').exists() and not (W/'data/dataset14_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*')) and not (W/'probe_round02_english/outputs').exists()
dev=read(W/'runs/dev_train13_en/summary.json');stress=read(W/'runs/stress_train13_en/summary.json')
assert dev['completed']==dev['planned']==dev['successes']==8
assert stress['completed']==stress['planned']==16 and stress['successes']==9
assert read(W/'reports/train13_en_all_records_verified.json')['evidence_consistent']
diagnostic=W/'reports/train13_failure_analysis.json'
assert sha(diagnostic)=='4d5acbf1b879e290b3feb9052015768c87b7b6d53a8b9666bb93532fe6d0ceff'
assert read(W/'reports/train13_fit_diagnostic/summary.json')['complete']
lock_check()
plan=copy.deepcopy(read(W/'protocol/train13_english.json'))
plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train14_en',
    previous_training_plan_sha256=sha(W/'protocol/train13_english.json'),diagnosis_sha256=sha(diagnostic),
    full_suite_diagnosis_sha256=sha(W/'reports/stress_train13_en_postflight_development_diagnostic_v2.json'),
    fit_diagnosis_sha256=sha(W/'reports/train13_fit_diagnostic/summary.json'),
    teacher_source_sha256=sha(W/'scripts/teacher_flight14.py'),inherited_teacher_source_sha256=sha(W/'scripts/teacher_flight13.py'),
    prior_results=dict(development=[8,8],stress=[9,16],requested_goal_hold=[13,16],initial_hover=[14,16],selected=False))
source_sha=sha(W/'data/dataset13_en/audit.json')
plan['training'].update(initial_checkpoint='v11_color/models/train13_en/final',
    initial_checkpoint_sha256=read(W/'models/train13_en/result.json')['checkpoint_sha256'],output='models/train14_en',
    steps=8000,seed=2026103014,source_dataset_audit_sha256=source_sha,braking_coefficient=1.6,
    minimum_free_gib_before_training=10.0,recovery_interval_steps=2000,
    recovery_storage='Unique recovery_stepNNNNN.pt plus SHA receipt every2000steps; no replacement or deletion of previous saves.',
    noise_schedule='For step=1..8000 and micro=0..1, frozen runtime Gaussian if (step+micro)%4<2, otherwise random. Same50/50 and common-noise/time quartet rules as13.',
    data='Same dataset13 images, states, tasks and sampling. Relabel stationary xy and navigation xy/yaw only.',
    rationale='Stationary teacher imitation is already close but physical hover can fail. Increase the training-only braking coefficient modestly1.2->1.6. Forecast target bearing1s ahead for navigation yaw, using current own linear/angular velocity. Runtime remains unchanged.')
plan['teacher'].update(braking_coefficient=1.6,navigation_lookahead_s=1.0,
    stationary_horizontal_command='-1.6 * input estimated horizontal velocity; norm cap0.2m/s, constant32steps. Zero unarmed or takeoff below0.25m.',
    nonhorizontal_labels='Vertical and takeoff/landing requests remain byte-identical. All landing targets and primitive yaw remain byte-identical. Navigation yaw uses1s bearing prediction.',
    navigation_yaw_rule='At each teacher step, predict position=p+R(heading)*own_xy_velocity*1s and heading=heading-own_clockwise_rate*1s. Apply the existing0.8 proportional yaw law,0.05rad deadband,0.25rad/s cap to predicted requested-person bearing. Body velocity and heading rollout remain consistent.',
    reason='Train13 full9/16: initialhover2 failures despite small imitation error; requested-goal hold3 failures with lateral/yaw errors; one late-power failure after reacquisitions and one landing-clearance failure. These changes are hypotheses and do not uniquely isolate causality.')
plan['data'].update(source='data/dataset13_en',source_audit_sha256=source_sha,
    unchanged='All image/state/task input arrays, English prompts, sampling pools, flow-time/noise schedule, loss weights, vertical/request labels, primitive yaw, landing labels, runtime and scoring.')
plan['hypotheses_not_results']=[
    'One-second bearing prediction may reduce delayed yaw oscillation and reacquisition. No runtime state or truth channel is added.',
    'Moderate teacher braking1.6 may reduce steady drift; delayed feedback can also oscillate. All original stability and clearance gates still apply.',
    'No evaluation images/states enter training. Fresh round02 remains unexposed.',
    'Additional steps, new seed, and two label changes prevent an isolated causal attribution. Preserve and report every candidate and failure.',
    'Offline one-step inference did not provide a consistent advantage; deployed inference remains10steps.'
]
plan['storage']=dict(project_root=str(W.parent),free_bytes_at_registration=shutil.disk_usage(W).free,
    training_must_wait_until_free_gib=10.0,protected_final_models_and_all_trial_records_preserved=True)
plan['registration_script_sha256']=sha(Path(__file__))
out=W/'protocol/train14_english.json';assert not out.exists();out.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(plan_sha256=sha(out),steps=8000,fresh_final_unexposed=True,training_not_started=True)))
