"""Record the next development attempt before constructing data or training."""
import datetime,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original=read(W/'protocol/plan.json');dev=read(W/'runs/dev_train01/summary.json')
assert dev['completed']==8 and dev['successes']==4
assert read(W/'reports/train01_records_verified.json')['evidence_consistent']
assert not (W/'protocol/selected_final.json').exists() and not (W/'probe/outputs').exists()
assert not list((W/'runs').glob('heldout_*'))
assert shutil.disk_usage(W).free>8*1024**3
training=dict(original['training']);training.update(initial_checkpoint='v11_color/models/train01/final',
    initial_checkpoint_sha256=read(W/'models/train01/result.json')['checkpoint_sha256'],
    steps=6000,seed=2026102803,learning_rate=3e-5,vlm_layer_learning_rate=5e-6,warmup_steps=200,output='models/train02',
    sampling='Alternate a counterfactual quartet and four near-goal navigation samples in microbatch 0; microbatch 1 has two navigation samples (80% near-goal) and two retained primitives. Every independent navigation sample chooses new/retained domain with equal probability, balanced blue/red. Approximately 45% near-goal, 25% counterfactual, 5% other navigation, 25% primitives.',
    data='Reuse unchanged 6408 JPEGs. Keep original examples; add zero-velocity and two disk-uniform velocity state variants to airborne visible navigation, recomputing the same frozen teacher. No development or held-out images used for gradients.')
plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train02',
    previous_attempt=dict(candidate='train01',final_sha256=training['initial_checkpoint_sha256'],successes=4,planned=8,summary_sha256=sha(W/'runs/dev_train01/summary.json')),
    rationale=['Correct-color approach occurred in the development flights, but stopping and continued safe stand-off were insufficient.',
               'Train01 independent new navigation velocities were limited to about +/-0.14 and +/-0.12 m/s, while development estimates reached over 0.20 m/s.',
               'Original-scene navigation was sampled much less often than new far-field counterfactuals; increase near-goal and original-scene retention.',
               'These are development diagnoses; this attempt does not isolate a single causal factor.'],
    original_protocol_sha256=sha(W/'protocol/plan.json'),training=training,
    augmentation=dict(additional_state_variants=3,variants=['zero horizontal velocity','uniform disk radius 0.26m/s','uniform disk radius 0.26m/s'],
                      horizontal_speed_radius_m_s=.26,navigation_heading_state_uniform_rad=[-.06,.06],near_goal_radius_m=.65,
                      counterpart_rule='Both shirt assignments share the same state variants; both instructions are generated for each visible target. No color can be inferred uniquely from the state variant.'),
    frozen=['Runtime code, controller gains, detector, success criteria, all original development and held-out layouts/seeds, static-probe conditions and thresholds'],
    evaluation='Final step only. Run the same eight development cases, then five original rescue regressions only if 8/8; held-out comparison only if all pass. Retain all previous and new failures.',
    heldout_inference_or_flight_count_before_training=0,development_images_used_for_training=0,
    storage=dict(free_bytes=shutil.disk_usage(W).free,additional_estimated_gb=4,stop_free_gb=5),
    weights_selection='Continue from completed train01 final; no intermediate step selected by score')
out=W/'protocol/train02.json';assert not out.exists();out.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(plan=str(out),sha256=sha(out),steps=training['steps'],heldout_unused=True)))
