"""Collect rebuild05 results into results/rebuild05_summary.json (read by the report builder).

Every registered case is included; nothing is filtered. Threshold evaluation uses the
values registered in protocol/rebuild05_final.json.
"""
import json,math,statistics as st
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def main():
    plan=read(W/'protocol/rebuild05_final.json');root=W/'runs/rebuild05_final'
    summary=read(root/'summary.json');assert summary['completed']==len(plan['cases'])==26
    rows=[]
    for o in summary['cases']:
        case=o['case'];rec=Path(o['record'])
        phys=read(rec/'physical_score.json') if (rec/'physical_score.json').exists() else None
        color=case.get('color') or (case.get('profile') if case.get('profile') in ('blue','red') else None)
        hold=phys['goal_holds'][color]['physical_hold']['duration_s'] if phys and color and color in phys.get('goal_holds',{}) else None
        rows.append(dict(id=case['id'],group=case['group'],scene=case['scene'],color=color,success=bool(o['success']),error=o.get('error'),
            record=str(rec),hold_s=hold,latency=phys.get('fixed_latency') if phys else None,
            vla_preserved=phys.get('vla_continuous_actions_preserved') if phys else None,
            minimum_goal_distance_m=(phys['goal_holds'][color].get('minimum_goal_distance_m') if phys and color and color in phys.get('goal_holds',{}) else None)))
    held=[r for r in rows if r['group']=='matched_unseen'];video=[r for r in rows if r['group']=='video_regression'];known=[r for r in rows if r['group']=='known_failure']
    by_color={c:sum(r['success'] for r in held if r['color']==c) for c in ('blue','red')}
    by_layout={}
    for r in held:by_layout.setdefault(r['scene'],[]).append(r['success'])
    by_layout={k:sum(v) for k,v in by_layout.items()}
    holds=[r['hold_s'] for r in held if r['success']]
    c=plan['criteria']
    gate=dict(heldout_total=sum(by_color.values())>=c['heldout_total_min'],each_color=all(v>=c['heldout_each_color_min'] for v in by_color.values()),
        each_layout=all(v>=c['heldout_each_layout_min'] for v in by_layout.values()),video=all(r['success'] for r in video) and len(video)==9)
    total=sum(by_color.values())
    if total==16:sentence=f'4配置とも4回すべて成功し、停止は{min(holds):.1f}〜{max(holds):.1f}秒続いた。'
    else:sentence=None  # written by hand after inspecting the failures
    # latency: VLA-only inference time measured during the primitive flights (no detector in that worker)
    inf=[]
    for r in video:
        if r['id'].startswith('primitive_'):
            for e in read(Path(r['record'])/'vla_link_events.json'):
                if e.get('event')=='inference':inf.append(e['inference_s'])
    inf.sort()
    latency=dict(inference_median=float(np.median(inf)),inference_p90=float(inf[int(.9*len(inf))]),inference_n=len(inf),source='vla_worker inference_s during the four primitive flights (renderer idle while inferring)')
    ages=[a for r in rows if r['latency'] for a in (r['latency']['min_age_s'],r['latency']['max_age_s'])]
    # probe
    probe=read(W/'probe_rebuild05/outputs/summary.json');v11=next(s for s in probe['summary'] if s['model']=='v1.1')
    sp=read(W/'protocol/static_probe_rebuild05.json');fid=1;f=next(x for x in sp['frames'] if x['id']==fid)
    lay={l['name']:l for l in read(W/'protocol/rebuild05_layouts.json')['heldout_layouts']}[f['scene']]
    raw=[json.loads(s) for s in (W/'probe_rebuild05/outputs/raw_outputs.jsonl').read_text(encoding='utf-8').splitlines()]
    raw=[r for r in raw if r['model']=='v1.1' and r['frame']['id']==fid];assert len(raw)==2
    pos=np.asarray(lay['positions'])[:,:2];arrows=[]
    for r in raw:
        actor=f['blue_actor'] if r['color']=='blue' else 1-f['blue_actor']
        arrows.append(dict(color=r['color'],target_xy=(pos[actor]+[-.9,0]).tolist(),world_horizontal=r['world_horizontal'],correct=r['correct_goal']))
    out=dict(configuration='rebuild05',protocol_sha256=__import__('hashlib').sha256((W/'protocol/rebuild05_final.json').read_bytes()).hexdigest(),
        cases=rows,video_cases=video,known_failure_cases=known,
        heldout=dict(blue=by_color['blue'],red=by_color['red'],total=total,by_layout=by_layout,hold_min=min(holds) if holds else None,hold_max=max(holds) if holds else None,sentence=sentence),
        gate=gate,gate_passed=all(gate.values()),latency=latency,delivery_age_range=[min(ages),max(ages)] if ages else None,
        probe=dict(correct=v11['correct_goal'],outputs=v11['outputs'],median_deg=v11['median_goal_angle_deg'],v10_correct=next(s for s in probe['summary'] if s['model']=='v1.0')['correct_goal']),
        probe_figure=dict(frame_id=fid,image=str(W/'probe_rebuild05/images'/f'{fid:05d}.jpg'),drone_xy=f['qpos'][:2],arrows=arrows))
    (W/'results').mkdir(exist_ok=True)
    (W/'results/rebuild05_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(heldout=out['heldout'],gate=gate,video=[(r['id'],r['success'],r['hold_s']) for r in video],known=[(r['id'],r['success']) for r in known],latency=latency,ages=out['delivery_age_range'],probe=out['probe']),ensure_ascii=False,indent=1))
if __name__=='__main__':main()
