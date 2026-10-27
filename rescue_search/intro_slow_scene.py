"""One slow establishing shot, using recorded physical poses in the tested scene."""
import bpy,sys,json,bisect,hashlib,time
from pathlib import Path
from mathutils import Vector,Quaternion
HERE=Path(__file__).resolve().parent;OUT=HERE/'intro_slow';OUT.mkdir(exist_ok=True)
dest=OUT/'establish';dest.mkdir(exist_ok=True)
blend=HERE/'scenes/clear/scene.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend))
scene=bpy.context.scene;cam=bpy.data.objects['Presentation'];scene.camera=cam
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
assert any(d.use for d in prefs.devices)
scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=32
scene.cycles.use_denoising=True;scene.cycles.denoiser='OPTIX';scene.render.use_persistent_data=True
scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=96
cam.data.clip_start=.005;cam.data.sensor_fit='AUTO';cam.data.dof.use_dof=False;cam.data.shift_x=0
rows=[json.loads(s) for s in (HERE/'runs/eval03/clear_blue/trace.jsonl').read_text().splitlines()]
times=[r['t'] for r in rows];drone=bpy.data.objects['DRONE']
metadata=[];preview='--preview' in sys.argv;started=time.monotonic()
for i in ([0,180,359] if preview else range(360)):
    moment=50+i/30;idx=max(0,bisect.bisect_right(times,moment)-1);r=rows[idx]
    drone.location=r['truth'][19:22];drone.rotation_quaternion=Quaternion(r['truth'][22:26])
    u=i/359;u=u*u*(3-2*u)
    cam.location=Vector((-.55,-1.9,1.48)).lerp(Vector((-.12,-1.68,1.42)),u)
    target=Vector((2.25,.7,1.25))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=29
    file=dest/f'{i:04d}.jpg'
    if not file.exists():scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
    metadata.append(dict(frame=i,trace_index=idx,simulation_time=r['t'],phase=r['phase']))
    if i%60==0:print('SLOW_ESTABLISH',i,round(time.monotonic()-started,1),flush=True)
if not preview:
    (OUT/'establish_source.json').write_text(json.dumps(dict(blend_sha256=hashlib.sha256(blend.read_bytes()).hexdigest(),
        scene_geometry_unchanged=True,run='eval03/clear_blue',speed=1,fps=30,frames=metadata,
        renderer='Cycles OptiX',samples=32,role='Opening illustration from recorded flight; demonstration starts in the following scene'),indent=2))
print('SLOW_ESTABLISH_COMPLETE',flush=True)
