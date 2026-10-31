"""Preregister conservative teacher stand-off; the scorer and runtime stay fixed."""
import datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
previous=read(W/'protocol/train02.json');dev=read(W/'runs/dev_train02/summary.json')
assert dev['completed']==8 and dev['successes']==7
assert read(W/'reports/train02_all_records_verified.json')['records']==16
assert not (W/'protocol/selected_final.json').exists() and not (W/'probe/outputs').exists()
assert not list((W/'runs').glob('heldout_*'))
assert shutil.disk_usage(W).free>8*1024**3
training=dict(previous['training']);training.update(initial_checkpoint='v11_color/models/train02/final',
    initial_checkpoint_sha256=read(W/'models/train02/result.json')['checkpoint_sha256'],
    steps=4000,seed=2026102804,learning_rate=2e-5,vlm_layer_learning_rate=2e-6,warmup_steps=150,output='models/train03',
    teacher_standoff_m=1.0,scoring_standoff_m=.9,
    data='Same 6408 pixels and 73712 examples as train02. Recompute navigation labels with 1.0m teacher stand-off instead of 0.9m. Non-navigation labels byte-identical. Sampling pools unchanged.')
plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train03',training=training,
    previous_attempt=dict(candidate='train02',checkpoint_sha256=training['initial_checkpoint_sha256'],successes=7,planned=8,summary_sha256=sha(W/'runs/dev_train02/summary.json')),
    original_protocol_sha256=sha(W/'protocol/plan.json'),previous_training_plan_sha256=sha(W/'protocol/train02.json'),
    diagnosis=dict(failed_case='dev02_blue',hold_s=3.909499999985485,minimum_person_clearance_m=.4331938265173788,required_clearance_m=.45,
                   phase_end_forward_offsets_m=[.124,.150,.212,.148,.127,.104],
                   interpretation='All six navigation development cases ended toward the person relative to the scored goal. The only failure was subsequent drift during report/landing. Increase teacher stand-off by 0.10m as a conservative margin; not a claim of correcting the estimator or identifying a unique cause.'),
    teacher_change=dict(old_standoff_m=.9,new_standoff_m=1.0,changed_labels='Navigation horizontal components only',gain=.7,deadband_m=.04,
                        safety_margin_m=.1,scorer_goal_unchanged=True,scoring_goal_standoff_m=.9,scoring_tolerance_m=.25,
                        intended_behavior='Approach the requested color and hold slightly farther from the person, leaving room for drift while reporting and landing'),
    evaluation=previous['evaluation'],frozen=previous['frozen'],
    heldout_inference_or_flight_count_before_training=0,development_images_used_for_training=0,
    storage=dict(free_bytes=shutil.disk_usage(W).free,additional_estimated_gb=3,stop_free_gb=5),
    weights_selection='Completed train02 final followed by exactly 4000 steps; never choose intermediate weights by score')
out=W/'protocol/train03.json';assert not out.exists();out.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(plan=str(out),sha256=sha(out),steps=training['steps'],scoring_unchanged=True)))
