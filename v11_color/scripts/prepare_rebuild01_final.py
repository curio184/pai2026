"""Freeze final cases and source hashes, only after all26 development cases pass."""
import ast,datetime,hashlib,json,math
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def main():
    initial=read(W/'runs/rebuild01_dev/summary.json');expanded=read(W/'runs/rebuild01_expanded/summary.json')
    assert initial['completed']==3 and expanded['completed']==23
    assert all(r['success'] for r in initial['cases']+expanded['cases']),'Resolve development failures before final holdout'
    base=read(W/'protocol/rebuild01_dev.json');layouts=read(W/'protocol/rebuild_final_layouts.json')['heldout_layouts']
    cases=[];rng=np.random.default_rng(202610310602)
    for i,layout in enumerate(layouts):
        for color in ['blue','red']:
            for repeat in [1,2]:
                n=len(cases)//2
                case=dict(id=f'RF{n+1:02d}',scene=layout['name'],color=color,repeat=repeat,
                    seed=202610316000+n,initial_offset=[float(rng.uniform(-.05,.05)),float(rng.uniform(-.05,.05)),float(rng.uniform(-5,5))],
                    kind='search',jitter=True,group='matched_unseen')
                for model in (['v1.0','v1.1'] if n%2==0 else ['v1.1','v1.0']):cases.append(dict(case,model=model))
    old=read(W/'protocol/navfocus_receipt.json');cases+=old['cases'][32:];assert len(cases)==42
    frames=[]
    views=[(.4,0,1.,0),(.6,.05,1.02,.02),(.7,-.05,.95,-.02),(.8,0,1.08,0)]
    for layout in layouts:
        for j,(x,y,z,yaw) in enumerate(views):
            for actor in [0,1]:frames.append(dict(id=len(frames),scene=layout['name'],view=j,blue_actor=actor,qpos=[x,y,z,math.cos(yaw/2),0,0,math.sin(yaw/2)],state=[0,0,0,z,0,0,0,0,1]))
    probe=read(W/'protocol/static_probe_navfocus.json')
    probe.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frames=frames,
        purpose='Fresh reserved final layouts. Same image with both prompts, and both shirt assignments. Viewpoints fixed before rendering; no output-based filtering.',
        inference_gate='selected_rebuild01.json must exist; final weights/runtime fixed before any inference',
        round_protocol_sha256=sha(W/'protocol/rebuild_final_layouts.json'))
    write(W/'protocol/static_probe_rebuild01.json',probe)
    mappings=[('prepare_scenes_navfocus.py','prepare_scenes_rebuild01.py'),('render_probe_navfocus.py','render_probe_rebuild01.py'),
        ('run_probe_navfocus.py','run_probe_rebuild01.py'),('plot_probe_navfocus.py','plot_probe_rebuild01.py')]
    for before,after in mappings:
        s=(W/'scripts'/before).read_text(encoding='utf-8')
        for a,b in [('navfocus_layouts.json','rebuild_final_layouts.json'),('selected_navfocus','selected_rebuild01'),('probe_navfocus','probe_rebuild01'),('figures_navfocus','figures_rebuild01')]:s=s.replace(a,b)
        ast.parse(s);(W/'scripts'/after).write_text(s,encoding='utf-8')
    runner=(W/'scripts/run_suite_rebuild01.py').read_text(encoding='utf-8').replace('rebuild01_dev.json','rebuild01_final.json')
    (W/'scripts/run_suite_rebuild01_final.py').write_text(runner,encoding='utf-8')
    checkpoint_roots={'v1.0':W.parent/read(W/'protocol/plan.json')['training']['initial_checkpoint'],
        'v1.1':W/'models'/base['candidate']/'final'}
    checkpoint_metadata={v:{p.name:sha(p) for p in ck.glob('*.json')} for v,ck in checkpoint_roots.items()}
    plan=dict(base,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        scope='Final fixed confirmation on four reserved fresh layouts. All42 flights retained; no retries or configuration changes within batch.',
        deadline_utc=read(W/'protocol/rebuild10h_goal.json')['deadline_utc'],cases=cases,
        old_checkpoint_sha256=old['old_checkpoint_sha256'],configuration='rebuild01',
        checkpoint_metadata_sha256=checkpoint_metadata,
        original_physical_scorer_sha256=sha(W.parent/'score_mission.py'),
        renderer_sha256=sha(W.parent/'civic_render_client.py'),
        interpretation='VLA velocity-plan endpoint is decoded; own-state trajectory tracking converts it to commands. Raw instantaneous VLA velocities are not directly executed.',
        runtime_lock_sha256=sha(W/'protocol/rebuild01_dev.json'),
        runner_sha256=sha(W/'scripts/run_suite_rebuild01_final.py'),
        layout_protocol_sha256=sha(W/'protocol/rebuild_final_layouts.json'),
        static_probe_sha256=sha(W/'protocol/static_probe_rebuild01.json'),
        jitter_bounds=dict(position_m=.05,heading_deg=5,seed=202610310602),
        criteria=read(W/'protocol/rebuild10h_goal.json')['unchanged_acceptance'],
        static_criteria=dict(correct_goal_min=60,outputs=64,whole_quartet_min=14,quartets=16),
        selection='Existing final-step train16 checkpoint. No intermediate weights selected; the runtime was developed on previous layouts only.',
        source_scripts={n:sha(W/'scripts'/n) for n in ['run_rebuild01_final.py','score_rebuild01.py','audit_rebuild01_execution.py','prepare_scenes_rebuild01.py','render_probe_rebuild01.py','run_probe_rebuild01.py','plot_probe_rebuild01.py']})
    write(W/'protocol/rebuild01_final.json',plan)
    write(W/'protocol/selected_rebuild01.json',dict(candidate=plan['candidate'],checkpoint_sha256=plan['checkpoint_sha256'],configuration='rebuild01',selection=plan['selection'],created_utc=plan['created_utc']))
    print(json.dumps(dict(final_cases=42,reserved_layouts=4,probe_images=32,protocol_sha256=sha(W/'protocol/rebuild01_final.json'))))
if __name__=='__main__':main()
