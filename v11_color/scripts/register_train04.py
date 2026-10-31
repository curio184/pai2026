"""Preregister learned braking and a fresh final evaluation before training."""
import copy,datetime,hashlib,json,shutil
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    assert not p.exists(),str(p)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    base=read(W/'protocol/plan.json');prior=read(W/'protocol/train03.json')
    completed=read(W/'runs/heldout_train03/summary.json');evidence=read(W/'results/all_trials.json')
    verified=read(W/'reports/all_records_verified.json')
    assert completed['completed']==completed['planned']==32
    assert not evidence['preregistered_goal_met'] and evidence['color_intervention_gate_met'] and evidence['known_failure_retest_passed']
    assert verified['evidence_consistent'] and verified['records']==62
    assert read(W/'post_pipeline_status.json')['stage']=='results_need_review'
    assert shutil.disk_usage(W).free>8*1024**3
    for name in ['train04.json','round02.json','static_probe_round02.json']:assert not (W/'protocol'/name).exists()
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Fixed seed; no policy call, success-dependent filtering, or scene preview.
    rng=np.random.default_rng(2026103001);layouts=[]
    for i in range(4):
        positions=[[float(rng.uniform(2.65,3.65)),float(rng.uniform(.52,1.10)),0.],
                   [float(rng.uniform(2.65,3.65)),-float(rng.uniform(.52,1.10)),0.]]
        layouts.append(dict(name=f'heldout_round02_{i+1:02d}',positions=positions,blue_actor=i%2))
    oldlayouts=base['train_layouts']+base['development_layouts']+base['heldout_layouts']
    for layout in layouts:
        assert all(layout['positions']!=old['positions'] for old in oldlayouts)
    cases=[]
    for layout in layouts:
        for color in ['blue','red']:
            for repeat in [1,2]:
                n=len(cases);seed=2026103100+n;rr=np.random.default_rng(seed)
                cases.append(dict(id=f'R2H{n+1:02d}',scene=layout['name'],color=color,repeat=repeat,seed=seed,
                    initial_offset=[float(rr.uniform(-.05,.05)),float(rr.uniform(-.05,.05)),float(rr.uniform(-5,5))]))
    stress=[dict(**c,kind='search',model='v1.1',jitter=True) for c in base['heldout_cases']]
    roundplan=dict(created_utc=stamp,round=2,initial_candidate='train04',
        reason='Round 1 was fully completed and failed. Its outcomes informed a new teacher; round 1 is preserved as a failed final evaluation, not presented as untouched validation for later candidates.',
        original_protocol_sha256=sha(W/'protocol/plan.json'),failed_round_summary_sha256=sha(W/'runs/heldout_train03/summary.json'),
        layout_seed=2026103001,layout_sampling=dict(x=[2.65,3.65],positive_y=[.52,1.10],negative_y=[-1.10,-.52],shirt_assignment='alternating actors; both instructions and two repetitions per layout',filtering='none; all four generated layouts retained'),
        heldout_layouts=layouts,heldout_cases=cases,heldout_model_order='v1.0 then v1.1 on even zero-based case index, reverse on odd',
        success_gate=base['success_gate'],scoring=base['scoring'],controller=base['controller'],
        jitter=dict(position_m=.05,heading_deg=5,plant_sensor_noise_seed='same as case seed',optical_sensor_seed=20261023,policy_noise_seed=20261024),
        development_stress_cases=stress,development_stress_gate=dict(total_minimum=14,per_color_minimum=7,per_layout_minimum=3,denominators=[16,8,4]),
        selection_rule='Final-step weights only. Original development 8/8, exposed round-1 stress >=14/16 with >=7/8 per color and >=3/4 per layout, original rescue regression 5/5, known T3 replay 1/1. No round-2 policy inference or flight until a checkpoint is fixed.',
        no_runtime_changes=True,training_examples_from_evaluation=0,
        final_additional_gates=dict(static_bilingual_correct_minimum=60,static_outputs=64,whole_quartets_minimum=14,quartets=16),
        publication='Report both final rounds separately, every development attempt and every failure. Do not pool candidates or delete the failed first round.')
    write(W/'protocol/round02.json',roundplan)
    probe=copy.deepcopy(read(W/'protocol/static_probe.json'))
    probe.update(created_utc=stamp,purpose='Fresh round-2 heldout language and shirt-color interventions',round_protocol_sha256=sha(W/'protocol/round02.json'),
        source_camera_and_metric_protocol_sha256=sha(W/'protocol/static_probe.json'),inference_gate='Only after selected_final_round02.json is created; no interim-weight evaluation')
    template=probe['frames'][:8];probe['frames']=[]
    for layout in layouts:
        for f in template:
            frame=copy.deepcopy(f);frame.update(id=len(probe['frames']),scene=layout['name']);probe['frames'].append(frame)
    write(W/'protocol/static_probe_round02.json',probe)
    training=copy.deepcopy(prior['training']);training.update(initial_checkpoint='v11_color/models/train03/final',
        initial_checkpoint_sha256=read(W/'models/train03/result.json')['checkpoint_sha256'],steps=6000,seed=2026102904,
        learning_rate=2e-5,vlm_layer_learning_rate=0.,train_vlm_text_layers=[],warmup_steps=200,output='models/train04',
        data='Same 6408 images and 73712 states as dataset03. Only airborne takeoff, turn and hover horizontal labels change. No navigation or landing relabeling.',
        braking_coefficient=.8,braking_proposal_sha256=sha(W/'scripts/teacher_braking_proposal.py'),
        source_dataset_audit_sha256=sha(W/'data/dataset03/audit.json'),
        primitive_sampling='Equal probability of original and randomized training-image domains; balanced tasks 2 through 6. Navigation/counterfactual sampling unchanged.',
        frozen_backbone='All vision-language parameters; train action expert and state/action projections only. Verify frozen parameter digest before and after training.')
    plan=dict(created_utc=stamp,candidate='train04',training=training,
        original_protocol_sha256=sha(W/'protocol/plan.json'),previous_training_plan_sha256=sha(W/'protocol/train03.json'),
        round_protocol_sha256=sha(W/'protocol/round02.json'),probe_protocol_sha256=sha(W/'protocol/static_probe_round02.json'),
        previous_attempt=dict(candidate='train03',heldout_successes=6,heldout_n=16,baseline_successes=2,baseline_n=16,
            bilingual_static_correct=64,bilingual_static_n=64,whole_quartets=16,known_failure_replay=True,
            all_records_verification_sha256=sha(W/'reports/all_records_verified.json'),phase_diagnostic_sha256=sha(W/'reports/heldout_train03_phase_diagnostic.json')),
        diagnosis='Color interventions pass, but full-mission stability fails under jitter/noise. Teacher horizontal requests during hover/turn are always zero. State-dependent braking is a hypothesis to test, not a proven unique cause.',
        teacher_change='For armed tasks 2,4,5,6: constant horizontal request -0.8 times captured estimated velocity across each chunk, norm limited to 0.2 m/s. Navigation, landing, yaw, vertical and request labels are unchanged.',
        frozen=prior['frozen'],evaluation=roundplan['selection_rule'],
        fresh_final_conditions_policy_executions_before_training=0,
        weights_selection='Exactly 6000 optimizer steps from completed train03 final; no intermediate checkpoint selection',
        storage=dict(free_bytes=shutil.disk_usage(W).free,stop_free_gb=5,previous_models_archived_with_user_approval=True))
    write(W/'protocol/train04.json',plan)
    print(json.dumps(dict(training_plan_sha256=sha(W/'protocol/train04.json'),round_protocol_sha256=sha(W/'protocol/round02.json'),steps=6000,layouts=layouts)))
if __name__=='__main__':main()
