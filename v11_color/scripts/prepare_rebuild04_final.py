"""Register rebuild04 final cases, thresholds and the runtime lock before any evaluation run.

Cases: 4 fresh layouts x blue/red x 2 jittered starts (v1.1 only), plus the 10 video-scene cases.
Thresholds are copied from rebuild03 and fixed here, before flights:
  held-out >= 14/16, each colour >= 7/8, each layout >= 3/4; video-scene 9/9 (known_T3_blue reported separately).
If they are not met, the report falls back to the rebuild03 configuration (documented as such).
"""
import datetime,hashlib,json
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=W/'protocol/rebuild04_final.json';assert not out.exists()
    smoke=read(W/'runs/rebuild04_smoke/summary.json')
    layouts=read(W/'protocol/rebuild04_layouts.json')['heldout_layouts']
    rng=np.random.default_rng(202610311902);cases=[]
    for layout in layouts:
        for color in ['blue','red']:
            for repeat in [1,2]:
                n=len(cases)
                cases.append(dict(id=f'R4F{n+1:02d}',scene=layout['name'],color=color,repeat=repeat,seed=202610317000+n,
                    initial_offset=[float(rng.uniform(-.05,.05)),float(rng.uniform(-.05,.05)),float(rng.uniform(-5,5))],
                    kind='search',jitter=True,group='matched_unseen',model='v1.1'))
    video=read(W/'protocol/navfocus_receipt.json')['cases'][32:];assert len(video)==10
    cases+=[dict(c) for c in video]
    rt=W/'runtime_rebuild04'
    runtime={str(p.relative_to(rt)).replace('\\','/'):sha(p) for p in sorted(rt.rglob('*.py'))}
    plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),configuration='rebuild04',
        candidate='train16_en',checkpoint_sha256='83ad870ea46901861bcb4d58f94fa4f04d24602a1442210913d4a19d74589f26',
        fixed_latency_s=0.4,chunk_origin='capture',plan_tracker_used=False,flow_steps=5,
        cases=cases,runtime_sha256=runtime,runner_sha256=sha(W/'scripts/run_suite_rebuild04.py'),scorer_sha256=sha(W/'scripts/score_rebuild04.py'),
        layout_protocol_sha256=sha(W/'protocol/rebuild04_layouts.json'),static_probe_sha256=sha(W/'protocol/static_probe_rebuild04.json'),
        jitter_bounds=dict(position_m=.05,heading_deg=5,seed=202610311902),
        criteria=dict(physical='Unchanged: hover band, <=0.25 m and <=0.08 m/s for >=3 s, clearance >=0.45 m, landing and motors off; fixed latency 0.40-0.45 s on every delivery; VLA chunk step executed unchanged.',
            heldout_total_min=14,heldout_each_color_min=7,heldout_each_layout_min=3,video_scene_required='9/9 (known_T3_blue reported separately)',
            static_probe=dict(correct_goal_min=60,outputs=64)),
        fallback='If any threshold is not met, the report uses the rebuild03 configuration and its existing records, stated as such.',
        smoke_reference=dict(path='runs/rebuild04_smoke/summary.json',completed=smoke['completed'],note='development layouts only; mechanics check'),
        no_retries=True,selection='train16_en final step. No weights selected on rebuild04 results.')
    out.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    (W/'protocol/selected_rebuild04.json').write_text(json.dumps(dict(candidate='train16_en',checkpoint_sha256=plan['checkpoint_sha256'],configuration='rebuild04',flow_steps=5,created_utc=plan['created_utc']),indent=2),encoding='utf-8')
    print(json.dumps(dict(cases=len(cases),protocol_sha256=sha(out))))
if __name__=='__main__':main()
