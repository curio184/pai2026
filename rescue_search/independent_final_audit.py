"""Independent read-only audit; scorer writes only into a temporary C-side copy."""
import contextlib,hashlib,io,json,os,shutil,sys,tempfile
from pathlib import Path
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);HERE=ROOT/'tmp/rescue_search';RUN=HERE/'runs/eval03'
sys.path.insert(0,str(ROOT))
from score_mission import score
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(RUN/'manifest.json')
sources={n:dict(snapshot=sha(RUN/'source_snapshot'/n)==h,current=sha(HERE/n)==h) for n,h in manifest['source_sha256'].items()}
assert all(v['snapshot'] for v in sources.values())
rows=[];views=[]
for condition in ['clear','fog_light','fog_dense','dust']:
 d=RUN/(condition+'_blue');result=read(d/'result.json');stored=read(d/'physical_score.json');search=read(d/'search_score.json')
 packets={p['id']:p for p in read(d/'vla_link_events.json') if p.get('event')=='inference'}
 assert all(sha(d/'observations'/p['image_file'])==p['image_sha256'] for p in packets.values())
 assert all(p['checkpoint_sha256']==manifest['checkpoint_sha256'] for p in packets.values())
 assert all(len(p['estimated_state'])==9 and len(p['action_chunk'])==32 and all(len(a)==6 for a in p['action_chunk']) for p in packets.values())
 with tempfile.TemporaryDirectory(dir=HERE,prefix='audit_temp_') as temp:
  temp=Path(temp)
  for name in ['trace.jsonl','result.json','events.json','vla_link_events.json','last_messages.json']:shutil.copy2(d/name,temp/name)
  with contextlib.redirect_stdout(io.StringIO()):actual=score(temp,HERE/'scenes'/condition/'physics/rescue_scene.xml')
  assert actual==stored,condition
 discovery=read(d/'discovery.json');note=read(d/'notification.json');start=read(d/'search_start_observation.json');initial=result['first_observation']
 assert sha(d/'notification.jpg')==note['evidence']['image_sha256']
 assert packets[note['evidence']['id']]['image_sha256']==note['evidence']['image_sha256']
 assert len({e['id'] for e in discovery['evidence']})==3
 assert all(e['image_sha256']==packets[e['id']]['image_sha256'] and e['person'] in packets[e['id']]['perception']['persons'] for e in discovery['evidence'])
 assert note['evidence']['person'] in packets[note['evidence']['id']]['perception']['persons']
 events=read(d/'events.json');land=min(e['t'] for e in events if e.get('event')=='land_request')
 hold=stored['goal_holds']['blue']['physical_hold']
 assert start['t']<discovery['t']<hold['end_s']<=note['t']<land
 assert 0<=note['t']-note['evidence']['t']<=2.5
 camera=next(e for e in read(d/'vla_link_events.json') if e.get('event')=='camera_provenance')
 cond=next(c for c in manifest['scene_conditions'] if c['name']==condition)
 assert camera['blend_sha256']==cond['blend_sha256']==sha(HERE/'scenes'/condition/'scene.blend')
 assert camera['physics_scene_sha256']==sha(HERE/'scenes'/condition/'physics/rescue_scene.xml')
 rows.append(dict(condition=condition,physical_rescore_matches=True,search_success=search['success'],frames=len(packets),
  hold_s=hold['duration_s'],discovery_s=discovery['t'],notification_s=note['t'],land_request_s=land,
  normal_end=result['stop_reason'],minimum_person_clearance_m=stored['minimum_person_clearance_m'],
  initial_fov=search.get('initial_view_geometry'),image_hashes_match=True,model_matches=True))
 views.append(dict(condition=condition,initial=str(d/'observations'/initial['image_file']),search_start=str(d/'observations'/start['image_file']),
   discovery=str(d/'observations'/discovery['evidence'][-1]['image_file']),notification=str(d/'notification.jpg')))
report=dict(sources=sources,cases=rows,views=views)
(HERE/'reviews').mkdir(exist_ok=True)
(HERE/'reviews/independent_eval03_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
