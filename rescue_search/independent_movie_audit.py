"""Independent lightweight audit of decoded final panels and pose provenance."""
import bisect,hashlib,json,os
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);HERE=ROOT/'tmp/rescue_search';MOV=HERE/'movie'
def read(p):return json.loads(p.read_text(encoding='utf8'))
qa=read(MOV/'final_qa.json');plan=read(MOV/'plan.json');rows=[]
for check in qa['input_panels']['checks']:
    i=qa['extracted_times_s'].index(check['video_time'])+1
    frame=Image.open(MOV/'final_qa'/f'frame_{i:03d}.png').convert('RGB')
    record=HERE/'runs/eval03'/f"{check['condition']}_blue"
    packets=[p for p in read(record/'vla_link_events.json') if p.get('event')=='inference']
    p=next(p for p in packets if p['image_sha256']==check['input_sha256'])
    original=record/'observations'/p['image_file'];assert hashlib.sha256(original.read_bytes()).hexdigest()==p['image_sha256']
    x1,y1,x2,y2=check['rectangle']
    expected=Image.open(original).convert('RGB').resize((x2-x1,y2-y1),Image.Resampling.NEAREST)
    mae=float(np.mean(np.abs(np.array(frame.crop((x1,y1,x2,y2)),dtype=float)-np.array(expected,dtype=float))))
    assert abs(mae-check['pixel_mae'])<1e-9
    rows.append(mae)
poses=[]
for seg in plan['segments']:
    record=Path(seg['record']);trace=[json.loads(s) for s in (record/'trace.jsonl').read_text().splitlines()];times=[r['t'] for r in trace]
    ps=read(MOV/'renders'/seg['name']/'poses.json');assert len(ps)==seg['duration_s']*30
    for p in ps:
        moment=min(seg['sim_end'],seg['sim_start']+p['frame']/30*seg['speed'])
        index=max(0,bisect.bisect_right(times,moment)-1)
        assert p['trace_index']==index and p['simulation_time']==trace[index]['t'] and p['phase']==trace[index]['phase']
    poses.append(dict(name=seg['name'],frames=len(ps),matches=True))
voices=read(MOV/'voice_manifest.json');clear=read(HERE/'runs/eval03/clear_blue/search_score.json')
discovery_video=42+(clear['discovery_time_s']-16)/2
notification_video=42+(clear['notification_time_s']-16)/2
assert voices[7]['start']>=discovery_video and voices[8]['start']>=notification_video
assert all(v['start']+v['duration_s']<=voices[i+1]['start'] for i,v in enumerate(voices[:-1]))
report=dict(panel_count=len(rows),max_mae=max(rows),panel_checks_independently_match=True,pose_segments=poses,
            discovery_video_s=discovery_video,notification_video_s=notification_video,
            discovery_narration_s=voices[7]['start'],notification_narration_s=voices[8]['start'],audio_listened=False)
(HERE/'reviews/independent_movie_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
