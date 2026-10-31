"""Register training labels and unchanged evaluation before data generation."""
import copy,datetime,hashlib,json,shutil
from pathlib import Path
from run_suite_english import lock_check
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (W/'models/train12_en').exists() and not (W/'data/dataset12_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*')) and not (W/'probe_round02_english/outputs').exists()
dev=read(W/'runs/dev_train11_en/summary.json');stress=read(W/'runs/stress_train11_en/summary.json')
assert dev['completed']==dev['planned']==dev['successes']==8
assert stress['completed']==stress['planned']==16 and stress['successes']==12
assert read(W/'reports/train11_en_all_records_verified.json')['evidence_consistent']
diagnostic=W/'reports/train11_failure_analysis.json';assert len(read(diagnostic)['cases'])==4
lock_check()
plan=copy.deepcopy(read(W/'protocol/train11_english.json'))
plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train12_en',previous_training_plan_sha256=sha(W/'protocol/train11_english.json'),diagnosis_sha256=sha(diagnostic),full_suite_diagnosis_sha256=sha(W/'reports/stress_train11_en_postflight_development_diagnostic.json'),teacher_source_sha256=sha(W/'scripts/teacher_flight12.py'),inherited_teacher_source_sha256=sha(W/'scripts/teacher_flight10.py'))
plan['training'].update(initial_checkpoint='v11_color/models/train11_en/final',initial_checkpoint_sha256=read(W/'models/train11_en/result.json')['checkpoint_sha256'],output='models/train12_en',steps=6000,seed=2026103012,braking_coefficient=1.2,data='Same dataset10 images and states. Relabel stationary horizontal braking and airborne rotation yaw only.',rationale='Address observed horizontal drift and rotation overshoot with training-only target changes. Preserve navigation and landing labels. No runtime or score changes.')
plan['teacher'].update(braking_coefficient=1.2,stationary_horizontal_command='-1.2 * input estimated horizontal velocity; norm cap0.2m/s, constant32 steps. Zero unarmed or takeoff below0.25m.',yaw_cap_rad_s=.25,yaw_capture_lookahead_s=1.0,yaw_target_rule='For armed rotation above0.8m: initial predicted yaw=own_yaw+1.0*own_yaw_rate. Iterate32 times at0.1s; rate=0 inside0.03rad else clip(0.8*(target-predicted_yaw), +/-0.25).',reason='H06/H11 insufficient physical hover with horizontal drift; H12 overshot scan and target near frame edge; H16 acquired red then lost it at right edge while drifting. Median capture-to-first-execution latency across16 development cases is0.9105s. Navigation error may persist; improvement is a hypothesis.')
plan['data'].update(source='data/dataset10_en',source_audit_sha256=sha(W/'data/dataset10_en/audit.json'),unchanged='All image/state/task input arrays, English prompts, sampling pools, flow-time/noise schedules, loss weights, navigation/landing labels, runtime and scoring.')
plan['hypotheses_not_results']=['Stronger training-only horizontal braking may reduce drift in stationary phases. No gain of the runtime controller is changed.','Yaw training labels anticipate1.0s delay using own yaw rate and cap teacher yaw at0.25rad/s; runtime cap remains0.35rad/s.','H16 also shows navigation-direction error; these target changes may not fix it. All subsequent runs, including failures, remain reportable.','No development images or states become training examples. Fresh round02 remains unexposed.','Multiple teacher changes plus continuation training prevent isolated causal attribution.']
plan['storage']=dict(project_root=str(W.parent),free_bytes_at_registration=shutil.disk_usage(W).free,inactive_record_compression_status_sha256=sha(W/'reports/inactive_record_compression/status.json'),training_must_wait_until_free_gib=7.4)
plan['registration_script_sha256']=sha(Path(__file__))
out=W/'protocol/train12_english.json';assert not out.exists();out.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(plan_sha256=sha(out),steps=6000,fresh_final_unexposed=True,training_not_started=True)))
