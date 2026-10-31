"""Freeze a new training recipe and new training-only camera views before rendering."""
import copy
import datetime
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parents[1]
P = W.parent
sys.path.insert(0, str(P))
from make_revision_data import quaternion, visible


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    assert not path.exists(), str(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    assert not (W / 'models/train05_en').exists()
    assert not (W / 'protocol/selected_final_round02_english.json').exists()
    assert not list((W / 'runs').glob('heldout_round02_*'))
    assert not (W / 'probe_round02_english/outputs').exists()
    previous = read(W / 'runs/stress_train04_en/summary.json')
    assert previous['completed'] == 16 and previous['successes'] == 10
    static = read(W / 'probe_train04_english_dev_retry01/outputs/summary.json')['summary'][0]
    assert static['outputs'] == static['correct_goal'] == 64
    base = read(W / 'protocol/plan.json')
    model = read(W / 'models/train04_en/result.json')
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data = dict(seed=2026102905, layouts_source='protocol/plan.json:train_layouts',
        layouts=20, pose_pairs_per_layout=50, added_images=2000,
        view_groups=dict(edge_or_rear_pairs_per_layout=32, all_heading_pairs_per_layout=18),
        rear_edge=dict(x_m=[-.8,.4], y_m=[-1.,1.], height_m=[.9,1.15],
                      target_bearing_from_camera_degrees=[25.,33.], side='alternating left/right',
                      target_actor='alternating geometry identities; both clothing assignments rendered'),
        all_heading=dict(x_m=[-.6,.3], y_m=[-.6,.6], height_m=[.85,1.2], yaw_radians=[-math.pi,math.pi]),
        roll_pitch_radians=[-.02,.02], source_blend='tmp/rescue_search/scenes/clear/scene.blend',
        source_blend_sha256=sha(P / 'tmp/rescue_search/scenes/clear/scene.blend'),
        rendering=dict(engine='Cycles CUDA',samples=16,seed=0,width=320,height=240,jpeg_quality=70,density=.004),
        existing_images=6408, existing_samples=73712,
        visibility_rule='Existing visible() for navigation labels; never reject a rendered pose after seeing a model result',
        own_velocity_pairing=dict(tasks=[2,3,4,5,6], armed_images_only=True,
            image_domains=['original randomized training views','retained v1.0 views','new training views'],
            pairs_per_image_per_task=1, state_seed=2026102906,
            radius_m_s=[dict(probability=.2,value=0.),dict(probability=.5,uniform=[.02,.12]),dict(probability=.3,uniform=[.12,.35])],
            angle_radians=[-math.pi,math.pi],
            invariant='Same image, prompt and other own-state values; horizontal velocity changes sign only',
            teacher='Existing train04 teacher, including -0.8 times captured own velocity for tasks 2/4/5/6; landing unchanged'),
        teacher_source_sha256=sha(W / 'data/dataset04_en/teacher_source.py'),
        base_dataset_audit_sha256=sha(W / 'data/dataset04_en/audit.json'),
        evaluation_images_or_states_as_training_inputs=0)
    rng = np.random.default_rng(data['seed'])
    frames = []
    for layout_id, layout in enumerate(base['train_layouts']):
        positions = np.asarray(layout['positions'])
        for pair in range(50):
            edge = pair < 32
            recipe = data['rear_edge'] if edge else data['all_heading']
            x,y,z = [float(rng.uniform(*recipe[key])) for key in ['x_m','y_m','height_m']]
            if edge:
                actor=(pair//2)%2;side=-1 if pair%2==0 else 1
                bearing=math.atan2(positions[actor,1]-y,positions[actor,0]-x)
                yaw=bearing-side*math.radians(float(rng.uniform(25,33)))
            else:
                yaw=float(rng.uniform(-math.pi,math.pi))
            roll,pitch=rng.uniform(-.02,.02,2)
            qpos=[x,y,z,*quaternion(float(roll),float(pitch),yaw)]
            state=[*rng.uniform(-.15,.15,2).tolist(),float(rng.uniform(-.04,.04)),z,
                   float(roll),float(pitch),0.,float(rng.uniform(-.03,.03)),1.]
            for blue_actor in [0,1]:
                frames.append(dict(id=len(frames),layout=layout_id,blue_actor=blue_actor,
                    pose_pair=layout_id*50+pair,view_group='rear_edge' if edge else 'all_heading',
                    qpos=qpos,state=state))
    assert len(frames)==2000
    counts={key:0 for key in ['both_visible','one_visible','none_visible']}
    for frame in frames:
        positions=base['train_layouts'][frame['layout']]['positions']
        count=sum(visible(np.asarray(frame['qpos']),np.asarray(p)) for p in positions)
        counts[['none_visible','one_visible','both_visible'][count]]+=1
    for a,b in zip(frames[::2],frames[1::2]):
        assert a['qpos']==b['qpos'] and a['state']==b['state'] and a['blue_actor']!=b['blue_actor']
    training=copy.deepcopy(read(W/'protocol/train04_english.json')['training'])
    training.update(initial_checkpoint='v11_color/models/train04_en/final',
        initial_checkpoint_sha256=model['checkpoint_sha256'],steps=8000,seed=2026102907,
        output='models/train05_en',learning_rate=2e-5,source_dataset_audit_sha256=data['base_dataset_audit_sha256'],
        data='Existing 6408 images retained plus 2000 new training-only views; opposite-own-velocity pairs added without changing existing labels.',
        data_images=6000,retention_images=2408,
        loss='Flow matching on six normalized action channels, weights [8,8,1,1,1,1], divided by their sum; runtime units and normalization unchanged.',
        action_loss_weights=[8.,8.,1.,1.,1.,1.],
        sampling='Microbatch 0 alternates color quartets and four navigation rows. Quartets: 50% new views/50% retained quartets. Navigation rows: balanced colors, 70% original near-goal pools (equal randomized/retention domains), 30% visible new views. Microbatch 1 uses two opposite-velocity pairs except every fifth step, which retains takeoff, landing, turn and hover examples. Pair domains: 50% new views/25% original randomized/25% retained. Tasks cycle 2..6. Retained takeoff samples are 50% grounded. Color quartets share noise at t=1. Velocity pairs share noise/time within each pair, with t=1 on even steps and sampled time on odd steps.',
        primitive_sampling='40% of all examples are state pairs; 10% retained primitive examples; navigation is 50%.',
        image_domains='Explicit per-image domains; new views are appended after the 6408 existing image IDs.',
        minimum_free_gib_before_training=7.4,minimum_free_gib_during_training=5.)
    plan=dict(created_utc=stamp,candidate='train05_en',training=training,data_generation=data,
        original_protocol_sha256=sha(W/'protocol/plan.json'),
        previous_training_plan_sha256=sha(W/'protocol/train04_english.json'),
        previous_diagnosis_sha256=sha(W/'reports/train04_en_development_diagnostic.json'),
        previous_result=dict(development=8,development_n=8,stress=10,stress_n=16,
                             color_correct=64,color_n=64,selected=False),
        round_protocol_sha256=sha(W/'protocol/round02_english.json'),
        probe_protocol_sha256=sha(W/'protocol/static_probe_round02_english.json'),
        runtime_lock_sha256=sha(W/'protocol/runtime_english_lock.json'),
        reuse_final_round_reason='Round 2 has never been exposed to policy inference or flight. Its layouts, seeds, counts and criteria remain unchanged.',
        final_step_only=True,fresh_final_policy_executions_before_training=0,
        evaluation='dev 8/8, exposed stress >=14/16 with >=7/8 per color and >=3/4 per layout, regression 5/5, known-failure 1/1, then fixed final-step selection and fresh matched 16 per model plus 64 color outputs.',
        frozen=['Runtime controller, gains, detector, mission manager, scorer, action units and English instructions'],
        hypotheses_not_proven=['Additional rear/edge and all-heading training images improve coverage.',
            'Opposite-state pairs reduce appearance shortcuts and improve imitation of braking labels.'],
        storage=dict(free_bytes=shutil.disk_usage(W).free,train03_move_approval_pending=True,
                     preparation_only_until_training_space_requirement_met=True),
        registration_script_sha256=sha(Path(__file__)))
    write(W/'protocol/train05_english.json',plan)
    write(W/'protocol/train05_training_frames.json',frames)
    write(W/'protocol/train05_data_registration.json',dict(created_utc=stamp,
        plan_sha256=sha(W/'protocol/train05_english.json'),frames_sha256=sha(W/'protocol/train05_training_frames.json'),
        images=len(frames),paired_poses=len(frames)//2,visibility_counts=counts,
        rejection_or_model_based_selection=False,rendered=False,trained=False))
    print(json.dumps(dict(plan_sha256=sha(W/'protocol/train05_english.json'),
        frames_sha256=sha(W/'protocol/train05_training_frames.json'),images=len(frames),visibility_counts=counts)))


if __name__=='__main__':
    main()
