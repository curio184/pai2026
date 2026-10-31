"""Preregister yaw correction refinement after all eight train09 development trials."""
import copy,datetime,hashlib,json,shutil
from pathlib import Path
from run_suite_english import lock_check
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (W/'models/train10_en').exists() and not (W/'data/dataset10_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*')) and not (W/'probe_round02_english/outputs').exists()
prior=read(W/'runs/dev_train09_en/summary.json');assert prior['completed']==prior['planned']==8 and prior['successes']==7
assert read(W/'reports/train09_en_all_records_verified.json')['evidence_consistent']
diagnostic=W/'reports/train09_rotation_development_diagnostic.json'
assert len(read(diagnostic)['cases'])==2
lock_check()
plan=copy.deepcopy(read(W/'protocol/train09_english.json'))
plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train10_en',
    previous_training_plan_sha256=sha(W/'protocol/train09_english.json'),
    prior_results=dict(development=[7,8],stress_not_started=True,selected=False),
    diagnosis_sha256=sha(diagnostic),full_suite_diagnosis_sha256=sha(W/'reports/train09_en_postflight_development_diagnostic.json'),
    teacher_source_sha256=sha(W/'scripts/teacher_flight10.py'),
    inherited_teacher_source_sha256=sha(W/'scripts/teacher_flight09.py'))
plan.pop('design_review',None)
plan['training'].update(initial_checkpoint='v11_color/models/train09_en/final',
    initial_checkpoint_sha256=read(W/'models/train09_en/result.json')['checkpoint_sha256'],
    output='models/train10_en',steps=4000,seed=2026102913,learning_rate=1e-5,
    source_dataset_audit_sha256=sha(W/'data/dataset09_en/audit.json'),
    action_loss_weights=[8.,8.,1.,4.,1.,1.],
    loss='Flow matching on six normalized action channels, weights [8,8,1,4,1,1], divided by their sum. Runtime units and normalization unchanged.',
    data='Same images, states, prompts and sampling as train09. Only airborne rotation yaw teacher targets are refined, with deadband 0.03 rad instead of 0.12 rad. Other targets are byte-identical.')
plan['teacher'].update(nonhorizontal_labels='Preserve all except yaw for rotation tasks 4/5 when captured state is armed and altitude >0.8m.',
    reason='Right rotation spent about 61s near an overshot target; median late airborne error about -9 degrees, with near-zero corrective output. Test tighter training targets and greater yaw loss weight. This is a hypothesis, not an isolated causal claim.',
    yaw_deadband_rad=.03,yaw_gain=.8,yaw_cap_rad_s=.35,
    yaw_target_rule='For armed rotation inputs above 0.8m: iterate yaw += 0.1*rate for 32 steps; rate=0 inside 0.03rad, otherwise clip(0.8*(target-yaw), +/-0.35). All other action channels copied from train09.')
plan['data'].update(source='data/dataset09_en',source_audit_sha256=sha(W/'data/dataset09_en/audit.json'),
    unchanged='All images, states, English prompts, splits, sampling pools, all non-yaw labels, navigation/landing labels, runtime and scoring.',
    training_yaw_coverage_audit_sha256=sha(W/'reports/train09_rotation_training_coverage.json'))
plan['hypotheses_not_results']=[
    'Tighter yaw teacher deadband and increased yaw training weight may improve settling near the target angle; preserve learned horizontal braking and navigation labels.',
    'The previous 61s right-turn settling delay left little mission time; full mission success remains required, including landing.',
    'No evaluation images or states are added to training. All previously registered evaluation gates remain unchanged. Fresh final evaluation has not started.']
plan['storage']=dict(project_root=str(W.parent),free_bytes=shutil.disk_usage(W).free)
assert plan['storage']['free_bytes']>=plan['training']['minimum_free_gib_before_training']*1024**3
plan['registration_script_sha256']=sha(Path(__file__))
out=W/'protocol/train10_english.json';assert not out.exists();out.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(plan_sha256=sha(out),steps=4000,fresh_final_unexposed=True)))
