"""Register train07 before relabeling/training; all final tests stay unexposed."""
import copy,datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (W/'models/train07_en').exists()
assert not (W/'data/dataset07_en').exists()
assert not (W/'protocol/selected_final_round02_english.json').exists()
assert not list((W/'runs').glob('heldout_round02_*'))
assert not (W/'probe_round02_english/outputs').exists()
assert read(W/'reports/train06_en_all_records_verified.json')['evidence_consistent']
plan=copy.deepcopy(read(W/'protocol/train06_english.json'))
plan.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train07_en',
    previous_training_plan_sha256=sha(W/'protocol/train06_english.json'),
    prior_results=dict(development=[8,8],stress=[9,16],selected=False),
    diagnosis_sha256=sha(W/'reports/train06_en_postflight_development_diagnostic.json'),
    teacher_source_sha256=sha(W/'scripts/teacher_flight07.py'))
t=plan['training']
t.update(initial_checkpoint='v11_color/models/train06_en/final',
    initial_checkpoint_sha256=read(W/'models/train06_en/result.json')['checkpoint_sha256'],
    output='models/train07_en',steps=6000,seed=2026102910,learning_rate=2e-5,
    source_dataset_audit_sha256=sha(W/'data/dataset06_en/audit.json'),
    teacher_standoff_m=.9,teacher_gain=1.4,teacher_stop_deadband_m=.02,
    braking_coefficient=0.,data='Same 8408 pixels and 236170 states; horizontal teacher labels only are replaced.',
    minimum_free_gib_before_training=7.4)
t.pop('braking_proposal_sha256',None)
plan['teacher']=dict(scope='Training labels only; frozen velocity-to-attitude controller already subtracts current estimated velocity.',
    hold_horizontal_command=0.,hold_tasks=[2,4,5,6],navigation_velocity_damping=.5,
    navigation_position_coefficient=1.4,horizontal_command_cap_m_s=.2,
    teacher_standoff_m=.9,scoring_standoff_m=.9,navigation_deadband_m=.02,
    nonhorizontal_labels='Preserve source byte-for-byte.',
    reason='Remove delayed duplicated velocity feedback in hold labels; remove the 10cm teacher/scorer target offset and reduce premature small approach commands. Runtime gains and stop acceptance remain unchanged.')
plan['data']=dict(source='data/dataset06_en',source_audit_sha256=sha(W/'data/dataset06_en/audit.json'),
    images=8408,added_images=0,layouts=20,evaluation_images_or_states_used_for_training=0,
    added_state_examples=0,expected_total_examples=236170,
    unchanged='All pixels, state examples, prompts, splits, nonhorizontal labels, runtime and scoring.')
plan['hypotheses_not_results']=[
    'Hold velocity targets of zero avoid adding image-latency-dependent feedback to the existing low-level velocity loop; flight improvement is not yet established.',
    'A stronger near-target teacher gradient and matched geometric standoff may reduce premature approach termination; this is a combined intervention, not an isolated ablation.',
    'Color selection and regression still require unchanged independent flight tests.']
plan['storage']=dict(project_root=str(W.parent),free_bytes=shutil.disk_usage(W).free)
plan['registration_script_sha256']=sha(Path(__file__))
out=W/'protocol/train07_english.json';assert not out.exists()
out.write_text(json.dumps(plan,indent=2),encoding='utf8')
print(json.dumps(dict(plan_sha256=sha(out),steps=t['steps'],runtime_unchanged=True)))
