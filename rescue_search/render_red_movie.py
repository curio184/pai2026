"""Render the newly verified red-person flight without changing its scene or poses."""
import bpy,bisect,json,math,hashlib,sys,time
from pathlib import Path
import xml.etree.ElementTree as ET
from mathutils import Vector,Quaternion
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;OUT=HERE/'red_movie';DEST=OUT/'renders';DEST.mkdir(exist_ok=True)
plan=json.loads((OUT/'plan.json').read_text());record=Path(plan['record'])
rows=[json.loads(x) for x in (record/'trace.jsonl').read_text().splitlines()];times=[r['t'] for r in rows]
score=json.loads((record/'search_score.json').read_text());assert score['success']
blend=HERE/'scenes/clear/scene.blend'
expected=json.loads((HERE/'scenes/clear/physics/rescue_scene.render.json').read_text())['blend_sha256']
assert hashlib.sha256(blend.read_bytes()).hexdigest()==expected
bpy.ops.wm.open_mainfile(filepath=str(blend));scene=bpy.context.scene;cam=bpy.data.objects['Presentation'];scene.camera=cam;drone=bpy.data.objects['DRONE']
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='OPTIX'
assert any(device.use for device in prefs.devices)
scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=24
scene.cycles.use_denoising=True;scene.cycles.denoiser='OPTIX';scene.render.use_persistent_data=True
scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=95
cam.data.clip_start=.005;cam.data.dof.use_dof=False;cam.data.shift_x=0;cam.data.sensor_fit='AUTO'
body=ET.parse(HERE/'scenes/clear/physics/rescue_scene.xml').getroot().find("worldbody/body[@name='red_person']")
target_position=Vector([float(x) for x in body.get('pos').split()]);target_position.z=1.05
def look(loc,target,lens):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
def project(p):
 v=world_to_camera_view(scene,cam,Vector(p));return [1280*v.x,800*(1-v.y),v.z]
poses=[];projections=[];started=time.monotonic()
count=plan['render_frames'];preview='--preview' in sys.argv
selected={0,count//3,2*count//3,count-1} if preview else set(range(count))
for i in range(count):
 moment=min(plan['sim_end'],plan['sim_start']+i/plan['fps']*plan['speed'])
 idx=max(0,bisect.bisect_right(times,moment)-1);r=rows[idx];p=Vector(r['truth'][19:22])
 drone.location=p;drone.rotation_quaternion=Quaternion(r['truth'][22:26])
 if r['t']<score['discovery_time_s']:
  look(p+Vector((-.33,-.45,.28)),p+Vector((0,0,.01)),42)
 else:
  u=max(0,min(1,(r['t']-score['discovery_time_s'])/1.2));u=u*u*(3-2*u)
  near=p+Vector((-.33,-.45,.28));wide=p+Vector((-.75,-1.35,.65));target=p.lerp(target_position,.44)
  look(near.lerp(wide,u),(p+Vector((0,0,.01))).lerp(target,u),42*(1-u)+28*u)
 bpy.context.view_layer.update();center=project(p)
 poses.append(dict(frame=i,trace_index=idx,simulation_time=r['t'],phase=r['phase'],projected=center[:2]))
 points=[]
 for j in range(41):
  at=max(plan['sim_start'],r['t']-4+j*.1);rr=rows[max(0,bisect.bisect_right(times,at)-1)]
  points.append(project(rr['truth'][19:22]))
 front=p+Quaternion(r['truth'][22:26])@Vector((.12,0,0))
 projections.append(dict(frame=i,simulation_time=r['t'],center=center,front=project(front),past_points=points))
 file=DEST/f'{i:04d}.jpg'
 if i in selected and not file.exists():scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
 if i in selected and (i%24==0 or preview):print('RED_RENDER',i,count,round(time.monotonic()-started,1),flush=True)
(DEST/'poses.json').write_text(json.dumps(poses,separators=(',',':')))
(OUT/'trail_projection.json').write_text(json.dumps(dict(frames=projections,camera_matches_existing_render=True,history_s=4,trace_sha256=hashlib.sha256((record/'trace.jsonl').read_bytes()).hexdigest()),separators=(',',':')))
(OUT/'render_source.json').write_text(json.dumps(dict(scene_sha256=expected,render_size=[1280,800],samples=24,device='OPTIX',record=str(record),target_position=list(target_position),ground_truth_used_only_for_postflight_rendering=True,poses_are_recorded=True),indent=2))
print('RED_RENDER_COMPLETE',round(time.monotonic()-started,1),flush=True)
