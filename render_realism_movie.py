"""Render the same frozen optical room from presentation cameras and real logs."""
import bpy,bisect,hashlib,json,math,sys,time
from pathlib import Path
from mathutils import Vector,Quaternion
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'tmp/realism_movie'
plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'));blend=ROOT/plan['scene_file']
assert hashlib.sha256(blend.read_bytes()).hexdigest()==plan['blend_sha256']
bpy.ops.wm.open_mainfile(filepath=str(blend));scene=bpy.context.scene;drone=bpy.data.objects['DRONE'];cam=bpy.data.objects['Presentation'];scene.camera=cam
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
assert any(d.use for d in prefs.devices)
scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=32;scene.render.use_persistent_data=True
scene.cycles.denoiser='OPTIX'
scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=94
cam.data.clip_start=.005;cam.data.sensor_fit='AUTO';cam.data.dof.use_dof=False
records={f['profile']:[json.loads(s) for s in (ROOT/plan['records']/f['profile']/'trace.jsonl').read_text().splitlines()] for f in plan['flights']}
times={p:[r['t'] for r in rows] for p,rows in records.items()}
people=json.loads((ROOT/'assets/civic_world/design.json').read_text())['people']
def look(loc,target,lens):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
def prepare(profile,local):
    cam.data.shift_x=.12
    f=next(f for f in plan['flights'] if f['profile']==profile)
    moment=min(f['sim_end'],f['sim_start']+max(0,local-f['lead_s'])*f['speed'])
    index=max(0,bisect.bisect_right(times[profile],moment)-1);row=records[profile][index]
    p=Vector(row['truth'][19:22]);drone.location=p;drone.rotation_quaternion=Quaternion(row['truth'][22:26])
    phase=row['phase']
    if phase in ['blue','red']:
        u=max(0,min(1,p.x/2.3));u=u*u*(3-2*u)
        loc=Vector((-1.0,-2.3,1.8)).lerp(Vector((1.15,-1.55,1.38)),u)
        target=Vector((1.55,.1,1.0)).lerp(Vector((3.0,people[phase][1]*.55,1.1)),u)
        look(loc,target,24+4*u)
    elif phase in ['right','left']:look(p+Vector((-.23,-.31,.26)),p,44)
    else:look(p+Vector((-.27,-.36,.17)),p+Vector((0,0,-.008)),46)
    bpy.context.view_layer.update();projected=world_to_camera_view(scene,cam,p)
    trail=[]
    for past in records[profile][max(0,index-450):index:24]:
        q=world_to_camera_view(scene,cam,Vector(past['truth'][19:22]))
        if q.z>0:trail.append([q.x*1920,(1-q.y)*1080])
    return dict(row_index=index,sim_time=row['t'],phase=phase,projected=[projected.x*1920,(1-projected.y)*1080],trail=trail)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];preview='--preview' in args
signature=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();guard=OUT/'render_source.json'
if not preview:
    if guard.exists():assert json.loads(guard.read_text())['sha256']==signature
    guard.write_text(json.dumps(dict(sha256=signature,plan_sha256=hashlib.sha256((OUT/'plan.json').read_bytes()).hexdigest())))
projection={};started=time.monotonic()
for f in plan['flights']:
    profile=f['profile'];dest=(OUT/'preview'/profile) if preview else (OUT/profile);dest.mkdir(parents=True,exist_ok=True);items=[]
    count=round((f['end']-f['start'])*30)
    indices=sorted({min(count-1,max(0,i)) for i in [90,count//2,count-50]+list(range(count//2,count//2+12))+list(range(count-50,count-38))}) if preview else range(count)
    for i in indices:
        info=prepare(profile,i/30);items.append(info);file=dest/f'{i:04d}.jpg'
        if not file.exists():scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
        if i%90==0:print('CIVIC_MOVIE_RENDER',profile,i,count,round(time.monotonic()-started,1),flush=True)
    projection[profile]=items
    if not preview:(OUT/'projection.json').write_text(json.dumps(projection,separators=(',',':')))
dest=OUT/'world_final';dest.mkdir(exist_ok=True);drone.location=(0,0,.033);drone.rotation_quaternion=(1,0,0,0)
cam.data.shift_x=0
for i in ([105] if preview else range(210)):
    u=i/209;u=u*u*(3-2*u)
    look(Vector((-1,-2.1,1.5)).lerp(Vector((-.5,-1.8,1.35)),u),(2.3,.25,1.25),26)
    file=dest/f'{i:04d}.jpg'
    if not file.exists():scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
print('CIVIC_MOVIE_RENDER_COMPLETE',round(time.monotonic()-started,1),flush=True)
