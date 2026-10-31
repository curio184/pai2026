"""Freeze the next training recipe before generating any new labels or training."""
import copy,datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not (W/'models/train06_en').exists()
    assert not (W/'data/dataset06_en').exists()
    assert not (W/'protocol/selected_final_round02_english.json').exists()
    assert not list((W/'runs').glob('heldout_round02_*'))
    assert not (W/'probe_round02_english/outputs').exists()
    prior=read(W/'runs/stress_train05_en/summary.json')
    assert prior['completed']==16 and prior['successes']==11
    verified=read(W/'reports/train05_en_all_records_verified.json');assert verified['evidence_consistent']
    migration=read(W/'reports/storage_e_preflight_audit.json');assert migration['passed']
    training=copy.deepcopy(read(W/'protocol/train05_english.json')['training'])
    training.update(initial_checkpoint='v11_color/models/train05_en/final',
        initial_checkpoint_sha256=read(W/'models/train05_en/result.json')['checkpoint_sha256'],
        output='models/train06_en',steps=10000,seed=2026102908,learning_rate=1.5e-5,
        source_dataset_audit_sha256=sha(W/'data/dataset05_en/audit.json'),
        data='Same 8408 images; relabeled horizontal teacher; zero and half-velocity anchors added to existing state pairs.',
        sampling='Same 25% color quartets, 25% navigation, 40% state calibration, 10% retained primitive schedule. State calibration uses one same-image quartet [v,-v,0,v/2] per microbatch; domains 25/25/50% and tasks 2..6 cycle. Common flow noise/time across the quartet; t=1 on even steps, sampled common time on odd steps. Other sampling unchanged.',
        primitive_sampling='State calibration 40%, retained primitives 10%, navigation/color 50%.',
        minimum_free_gib_before_training=7.4,minimum_free_gib_during_training=5.)
    plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train06_en',
        training=training,previous_training_plan_sha256=sha(W/'protocol/train05_english.json'),
        prior_results=dict(development=[8,8],stress=[11,16],failed_cases=['H06','H09','H11','H14','H15'],selected=False),
        diagnosis_sha256=sha(W/'reports/stress_train05_en_phase_diagnostic.json'),
        teacher_source_sha256=sha(W/'scripts/teacher_flight06.py'),
        teacher=dict(scope='Training labels only; no runtime controller/gain/scorer changes.',
            takeoff_horizontal_zero_below_estimated_altitude_m=.25,
            airborne_hold_braking_coefficient=1.2,hold_tasks=[2,4,5,6],
            navigation_velocity_damping=.5,navigation_position_coefficient=.7,
            horizontal_command_cap_m_s=.2,teacher_standoff_m=1.,scoring_standoff_m=.9,
            navigation_deadband_m=.04,nonhorizontal_labels='Retain source labels byte-for-byte.',
            reason='Development logs show delayed initial settling and insufficient goal hold. Grounded velocity estimates must not request horizontal takeoff motion; approach labels now include deceleration.'),
        data=dict(source='data/dataset05_en',source_audit_sha256=sha(W/'data/dataset05_en/audit.json'),
            images=8408,added_images=0,layouts=20,evaluation_images_or_states_used_for_training=0,
            state_calibration='For every existing opposite-horizontal-velocity pair, append zero and half of the first velocity; preserve the image, task and other seven state values.',
            added_state_examples=80120,expected_total_examples=236170,
            unchanged='Pixels, layout split, instructions, action units, all nonhorizontal labels for existing examples.'),
        round_protocol_sha256=sha(W/'protocol/round02_english.json'),
        probe_protocol_sha256=sha(W/'protocol/static_probe_round02_english.json'),
        runtime_lock_sha256=sha(W/'protocol/runtime_english_lock.json'),
        original_protocol_sha256=sha(W/'protocol/plan.json'),
        storage_amendment_sha256=sha(W/'protocol/storage_migration_e.json'),
        fresh_final_policy_executions_before_training=0,final_step_only=True,
        evaluation='Unchanged: dev 8/8; exposed stress >=14/16, >=7/8 each color, >=3/4 each layout; regression 5/5; known failure 1/1; then fresh matched 16 per model and preregistered static probe.',
        hypotheses_not_results=['Teacher changes and state anchors improve settling; not an isolated ablation.',
            'The H15 detector-confirmation failure may remain; detector/mission logic is frozen.'],
        storage=dict(project_root=str(W.parent),free_bytes=shutil.disk_usage(W).free),
        registration_script_sha256=sha(Path(__file__)))
    out=W/'protocol/train06_english.json';assert not out.exists()
    out.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(plan_sha256=sha(out),steps=training['steps'],images=8408,added_images=0)))
if __name__=='__main__':main()
