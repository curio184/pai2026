"""Lock a continuous edit only after all four actual rich-world flights pass."""
import argparse,bisect,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def build(record):
    record=record.resolve();summary=json.loads((record/'result.json').read_text());assert summary['success']
    verification=json.loads((record/'verification_manifest.json').read_text());optical=json.loads((record/'rescue_scene.render.json').read_text())
    blend=ROOT/optical['blend_relative'];assert sha(blend)==optical['blend_sha256']
    profiles=['blue','red','turns','left'];sources={};flights=[]
    for profile in profiles:
        case=record/profile;score=json.loads((case/'physical_score.json').read_text());assert score['success'] and score['checkpoints']==[summary['checkpoint_sha256']]
        events=json.loads((case/'events.json').read_text());link=json.loads((case/'vla_link_events.json').read_text())
        assert any(e.get('event')=='camera_provenance' and e['blend_sha256']==optical['blend_sha256'] for e in link)
        for e in link:
            if e.get('image_file'):assert sha(case/'observations'/e['image_file'])==e['image_sha256']
        rows=[json.loads(s) for s in (case/'trace.jsonl').read_text().splitlines()]
        first=max(0,min(e['t'] for e in events if e['event']=='policy_takeoff_request')-1)
        flights.append(dict(profile=profile,sim_start=first,sim_end=rows[-1]['t'],score=score))
        sources[profile]={name:sha(case/name) for name in ['trace.jsonl','events.json','vla_link_events.json','physical_score.json']}
    speed=2.
    while 50+sum((f['sim_end']-f['sim_start'])/speed+2 for f in flights)>180:speed+=.5
    timeline=[dict(name='hero',start=0,end=8),dict(name='world',start=8,end=15),dict(name='architecture',start=15,end=28)]
    t=28
    for f in flights:
        duration=math.ceil(((f['sim_end']-f['sim_start'])/speed+2)*30)/30
        f.update(start=t,end=t+duration,speed=speed,lead_s=.7,tail_s=1.3)
        timeline.append(dict(name=f['profile'],start=t,end=t+duration));t+=duration
    timeline.extend([dict(name='results',start=t,end=t+12),dict(name='outro',start=t+12,end=t+22)])
    plan=dict(records=record.relative_to(ROOT).as_posix(),checkpoint_sha256=summary['checkpoint_sha256'],blend_sha256=optical['blend_sha256'],physics_scene_sha256=sha(record/'rescue_scene.xml'),fps=30,width=1920,height=1080,duration_s=t+22,frames=round((t+22)*30),flights=flights,timeline=timeline,evidence_sha256=sources,scene_file=optical['blend_relative'],disclosure='Actual new-world camera/VLA/physics runs. External cameras reconstruct their exact poses in the identical frozen optical scene; no scene replacement or invented action. Only pre-takeoff initialization is trimmed. Flight playback is continuous at one declared speed.')
    out=ROOT/'tmp/realism_movie';out.mkdir(exist_ok=True)
    dest=out/'plan.json'
    if dest.exists():raise FileExistsError(dest)
    dest.write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf8');print(json.dumps(dict(duration=plan['duration_s'],speed=speed,frames=plan['frames'])),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('record',type=Path);build(p.parse_args().record)
