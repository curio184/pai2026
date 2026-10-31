import json,hashlib,datetime,math
from pathlib import Path
W=Path(__file__).resolve().parents[1]
plan=json.loads((W/'protocol/plan.json').read_text(encoding='utf-8'))
views=[(.4,0,1.,0),(.8,.1,1.02,.10),(1.,-.1,.95,-.10),(1.3,0,1.08,0)]
frames=[]
for layout in plan['heldout_layouts']:
    for j,(x,y,z,yaw) in enumerate(views):
        for actor in [0,1]:
            frames.append(dict(id=len(frames),scene=layout['name'],view=j,blue_actor=actor,qpos=[x,y,z,math.cos(yaw/2),0,0,math.sin(yaw/2)],state=[0,0,0,z,0,0,0,0,1]))
obj=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),purpose='Held-out static color and language interventions; no flight, no training selection',frames=frames,
    inference_gate='selected_final.json must exist; no model selection from these outputs',models=['v1.0','v1.1'],
    prompts={'runtime_bilingual':['Approach the person wearing blue and stop. 青い服の人の前で止まって。','Approach the person wearing red and stop. 赤い服の人の前で止まって。'],'japanese':['青い服の人の前で止まって','赤い服の人の前で止まって']},
    action_summary='Mean of first 10 steps of horizontal velocity in body frame, then rotate to world for posthoc scoring',
    stationary_speed_m_s=.02,primary='Angle to requested goal smaller than angle to other goal; stationary or exact tie counts as failure',
    secondary='Angle to requested person smaller than angle to other person, median goal angle for nonstationary outputs; all frames retained',
    paired='Both instructions must choose correctly in the same image; separately count quartets correct under both shirt assignments and both instructions',
    figure_ids=[0,1,8,9],limit='Correlated synthetic views in a single room; not independent flight trials and not a confidence estimate for arbitrary scenes')
dest=W/'protocol/static_probe.json'
with dest.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
print(hashlib.sha256(dest.read_bytes()).hexdigest())
