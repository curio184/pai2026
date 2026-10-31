"""Register the next candidate after ALL train08 stressed trials have completed."""
import copy,datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
from run_round02_english import stress_pass
from run_suite_english import lock_check
assert not (W/'models/train09_en').exists() and not (W/'data/dataset09_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*')) and not (W/'probe_round02_english/outputs').exists()
prior=read(W/'runs/stress_train08_en_capped/summary.json');assert prior['completed']==prior['planned']==16
assert not stress_pass(prior)
assert read(W/'reports/train08_en_capped_all_records_verified.json')['evidence_consistent']
diagnostic=W/'reports/stress_train08_en_capped_postflight_development_diagnostic.json'
assert read(diagnostic)['completed']==16
lock_check()
plan=copy.deepcopy(read(W/'protocol/train08_english.json'))
plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train09_en',
    previous_training_plan_sha256=sha(W/'protocol/train08_english.json'),
    prior_results=dict(development=[8,8],stress=[prior['successes'],16],selected=False),
    diagnosis_sha256=sha(diagnostic),
    full_suite_diagnosis_sha256=sha(W/'reports/stress_train08_en_capped_failure_details.json'),
    teacher_source_sha256=sha(W/'scripts/teacher_flight09.py'),
    inherited_teacher_source_sha256=sha(W/'scripts/teacher_flight08.py'),
    bounded_execution_protocol_sha256=sha(W/'protocol/bounded_execution.json'))
plan['training'].update(initial_checkpoint='v11_color/models/train08_en/final',
    initial_checkpoint_sha256=read(W/'models/train08_en/result.json')['checkpoint_sha256'],
    output='models/train09_en',steps=4000,seed=2026102912,learning_rate=1e-5,braking_coefficient=.6,
    source_dataset_audit_sha256=sha(W/'data/dataset08_en/audit.json'),
    data='Same pixels, states, English prompts, sampling and navigation as train08. Only stationary horizontal teacher labels use -0.6 times captured estimated velocity, clipped to 0.2m/s; grounded takeoff stays zero.')
plan['teacher'].pop('hold_horizontal_command',None)
plan['teacher'].update(braking_coefficient=.6,grounded_takeoff_horizontal_zero_below_m=.25,
    stationary_horizontal_command='-0.6 * input estimated horizontal velocity; vector norm <=0.2m/s; constant across 32 steps. Zero while unarmed or takeoff altitude <0.25m.',
    reason='Zero horizontal targets yielded insufficient physical hover duration in several completed jitter trials. Test mild learned braking rather than the earlier stronger 0.8/1.2 teacher coefficients. This is a training hypothesis, not a proven stability guarantee or a change to the runtime controller.')
plan['data'].update(source='data/dataset08_en',source_audit_sha256=sha(W/'data/dataset08_en/audit.json'),
    unchanged='All pixels, states, English prompts, splits, navigation/landing labels, nonhorizontal labels, runtime and scoring.')
plan['hypotheses_not_results']=[
    'Mild braking learned from estimated velocity may improve settling after takeoff without the oscillation risk of stronger delayed corrections. Keep navigation and all nonhorizontal targets unchanged.',
    'Detector failures and stability failures are separate from choosing the wrong color; full mission success, not component success, remains required.',
    'All existing dev, stress, regression, known-failure, fresh paired and static intervention gates remain unchanged; final-step weights only.']
plan['design_review']=dict(unregistered_draft_coefficient=.3,registered_coefficient=.6,
    training_or_flight_at_draft_coefficient=False,
    reason='Full-suite review showed 7 initial-hover failures and prolonged drift during H15 hover (median physical speed about 0.110m/s with near-zero requested horizontal velocity). Choose 0.6 before any new training: a moderate correction below prior 0.8/1.2 teachers, while retaining train08 navigation. This is not a claim of an optimal or proven-stable gain.',
    prior_hover_success_counts={'train05_coefficient_0_8':[14,16],'train06_coefficient_1_2':[11,16],'train08_coefficient_0':[9,16]},
    caveat='These candidates also differ in training history/data. The counts are development evidence, not an isolated gain comparison.')
plan['resources']=dict(simulator_cpu_cores_max=4,simulator_memory_max_bytes=8*1024**3,nice=10,concurrent_flights=1,
    training='Windows GPU, no WSL training; no flight concurrent with training',
    scope='Project WSL process tree only; other user workloads and global WSL settings untouched')
plan['storage']=dict(project_root=str(W.parent),free_bytes=shutil.disk_usage(W).free)
assert plan['storage']['free_bytes']>=plan['training']['minimum_free_gib_before_training']*1024**3
plan['registration_script_sha256']=sha(Path(__file__))
out=W/'protocol/train09_english.json';assert not out.exists();out.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(plan_sha256=sha(out),steps=4000,prior_stress_successes=prior['successes'],fresh_final_unexposed=True)))
