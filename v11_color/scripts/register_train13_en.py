"""Register a navigation-centering training recipe before data generation."""
import copy,datetime,hashlib,json,shutil
from pathlib import Path
from run_suite_english import lock_check
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (W/'models/train13_en').exists() and not (W/'data/dataset13_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*')) and not (W/'probe_round02_english/outputs').exists()
dev=read(W/'runs/dev_train12_en/summary.json');assert dev['completed']==dev['planned']==8 and dev['successes']==7
assert read(W/'reports/train12_en_all_records_verified.json')['evidence_consistent']
diagnostic=W/'reports/train12_failure_analysis.json';assert read(diagnostic)['development']['failures']==['dev01_blue']
lock_check()
plan=copy.deepcopy(read(W/'protocol/train12_english.json'))
plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train13_en',
    previous_training_plan_sha256=sha(W/'protocol/train12_english.json'),diagnosis_sha256=sha(diagnostic),
    full_suite_diagnosis_sha256=sha(W/'reports/dev_train12_en_postflight_development_diagnostic.json'),
    teacher_source_sha256=sha(W/'scripts/teacher_flight13.py'),inherited_teacher_source_sha256=sha(W/'scripts/teacher_flight12.py'),
    prior_results=dict(development=[7,8],stress='Not run: development gate failed',selected=False))
source_sha=sha(W/'data/dataset12_en/audit.json')
plan['training'].update(initial_checkpoint='v11_color/models/train12_en/final',
    initial_checkpoint_sha256=read(W/'models/train12_en/result.json')['checkpoint_sha256'],output='models/train13_en',
    steps=6000,seed=2026103013,source_dataset_audit_sha256=source_sha,
    data='Same dataset12 images, states, task prompts, and sampling. Relabel navigation xy/yaw only.',
    rationale='The requested person can leave the camera frame during translation. Teach yaw to center that person while preserving the same world stop goal and navigation translation law. Primitive/landing labels and runtime remain unchanged.')
plan['teacher'].update(nonhorizontal_labels='Preserve vertical and takeoff/landing requests; add yaw for airborne navigation tasks0/1. All primitive and landing labels are byte-identical to dataset12.',
    navigation_yaw_gain=.8,navigation_yaw_deadband_rad=.05,navigation_yaw_cap_rad_s=.25,
    navigation_yaw_rule='When armed above0.8m, yaw=0 inside0.05rad of target-person bearing; otherwise clip(-0.8*bearing,+/-0.25rad/s). Positive command is clockwise. Update heading and body-frame velocity each0.1s during the approximate32-step teacher rollout.',
    navigation_world_goal='Same teacher goal: person position + [-1.0m,0] in the room plane. Scoring goal remains [-0.9m,0].',
    reason='Train12 dev01blue lost the target at the image edge; all existing navigation yaw labels are zero despite off-center training views. Primitive cases passed. Preserve train12 primitive labels and add navigation centering only.')
plan['data'].update(source='data/dataset12_en',source_audit_sha256=source_sha,
    unchanged='All image/state/task input arrays, English prompts, sampling pools, flow-time/noise schedule, loss weights, primitive/landing targets, runtime and scoring.',
    training_navigation_geometry_audit_sha256=sha(W/'reports/navigation_training_geometry_audit.json'))
plan['hypotheses_not_results']=[
    'Navigation yaw may keep the requested person in view during approach; learned behavior still needs complete closed-loop evaluation.',
    'The same translation law is expressed in the changing body frame during teacher rollout. No simulator truth is added to model inputs.',
    'All training inputs are reused from audited data; no development images/states are added. Final round02 remains unexposed.',
    'All primitive/landing labels remain byte-identical, but shared-parameter interference is possible and every regression gate still applies.',
    'Continuation training and a new fixed seed prevent isolated causal attribution to the new yaw labels alone.'
]
plan['storage']=dict(project_root=str(W.parent),free_bytes_at_registration=shutil.disk_usage(W).free,
    training_must_wait_until_free_gib=7.4,protected_final_models_and_all_trial_records_preserved=True)
plan['registration_script_sha256']=sha(Path(__file__))
out=W/'protocol/train13_english.json';assert not out.exists();out.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(plan_sha256=sha(out),steps=6000,fresh_final_unexposed=True,training_not_started=True)))
