import argparse
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(args):
    out=HERE/'movie';out.mkdir(exist_ok=True)
    records=HERE/'runs'/args.run
    scores={c:json.loads((records/(c+'_blue')/'search_score.json').read_text()) for c in ['clear','fog_light','fog_dense','dust']}
    assert all(s['success'] for s in scores.values()),'Cannot build a successful presentation from failed flights'
    trace=[json.loads(l) for l in (records/'clear_blue/trace.jsonl').read_text().splitlines()]
    start=16.;end=trace[-1]['t'];demo_duration=math.ceil((end-start)/2)+2
    timeline=[];at=0
    for name,length in [('title',4),('purpose',16),('mechanism',22),('demo',demo_duration),('conditions',24),('hardware',23),('closing',12)]:
        timeline.append(dict(name=name,start=at,end=at+length));at+=length
    assert 60<=at<=180
    segments=[dict(name='demo',condition='clear',record=str(records/'clear_blue'),sim_start=start,sim_end=end,
                   duration_s=demo_duration,speed=2,lead_s=0,render_fps=30)]
    for c in ['fog_light','fog_dense','dust']:
        s=scores[c]
        segments.append(dict(name=c,condition=c,record=str(records/(c+'_blue')),sim_start=s['discovery_time_s']-3,
                             sim_end=s['completion_time_s'],duration_s=8,speed=2,lead_s=0,render_fps=30))
    plan=dict(duration_s=at,frames=at*30,timeline=timeline,segments=segments,scores=scores,
              records=str(records),checkpoint_sha256=scores['clear']['checkpoint_sha256'],
              source_conditions=json.loads((HERE/'scene_conditions.json').read_text()),
              source_sha256={c:{f:digest(records/(c+'_blue')/f) for f in ['trace.jsonl','vla_link_events.json','notification.jpg','search_score.json']} for c in scores},
              render_size=[1280,800],panel_rectangle=[1332,266,1844,650],
              disclosure='External cameras reconstruct actual physics poses in the same frozen optical scene. Camera input panels are original JPEGs. One drone, one room. Search route stages selected by a program; VLA generates motion. No real flight.')
    (out/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(duration_s=at,timeline=timeline),indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',default='eval03');main(p.parse_args())
