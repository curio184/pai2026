"""Project recorded past positions through the exact existing presentation camera."""
import bpy,bisect,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent
OUT=HERE/'demo_movie';OUT.mkdir(exist_ok=True)
record=HERE/'runs/eval03/clear_blue'
rows=[json.loads(x) for x in (record/'trace.jsonl').read_text().splitlines()]
times=[r['t'] for r in rows]
score=json.loads((record/'search_score.json').read_text())
poses=json.loads((HERE/'movie/renders/demo/poses.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(HERE/'scenes/clear/scene.blend'))
scene=bpy.context.scene;cam=bpy.data.objects['Presentation'];scene.camera=cam
scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.resolution_percentage=100
cam.data.clip_start=.005;cam.data.dof.use_dof=False;cam.data.shift_x=0;cam.data.sensor_fit='AUTO'
def look(loc,target,lens):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
def proj(p):
 v=world_to_camera_view(scene,cam,Vector(p));return [1280*v.x,800*(1-v.y),v.z]
result=[]
for meta in poses:
 r=rows[meta['trace_index']];p=Vector(r['truth'][19:22]);t=r['t']
 if t<score['discovery_time_s']:
  look(p+Vector((-.33,-.45,.28)),p+Vector((0,0,.01)),42)
 else:
  u=max(0,min(1,(t-score['discovery_time_s'])/1.2));u=u*u*(3-2*u)
  near=p+Vector((-.33,-.45,.28));wide=p+Vector((-.75,-1.35,.65));target=p.lerp(Vector((3.241,.808,1.05)),.44)
  look(near.lerp(wide,u),(p+Vector((0,0,.01))).lerp(target,u),42*(1-u)+28*u)
 bpy.context.view_layer.update();center=proj(p)
 assert max(abs(a-b) for a,b in zip(center,meta['projected']))<.1
 points=[]
 for j in range(41):
  tt=max(16,t-4+j*.1);rr=rows[max(0,bisect.bisect_right(times,tt)-1)]
  points.append(proj(rr['truth'][19:22]))
 front=p+Quaternion(r['truth'][22:26])@Vector((.12,0,0))
 result.append(dict(frame=meta['frame'],simulation_time=t,center=center,front=proj(front),past_points=points))
(OUT/'trail_projection.json').write_text(json.dumps(dict(frames=result,camera_matches_existing_render=True,history_s=4,trace_sha256=hashlib.sha256((record/'trace.jsonl').read_bytes()).hexdigest()),separators=(',',':')))
print('TRAIL_PROJECTION_COMPLETE',len(result),flush=True)
