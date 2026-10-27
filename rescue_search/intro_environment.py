"""Establishing views of the unchanged tested scene, without a flight claim."""
import bpy,sys,json,hashlib,time
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
OUT=HERE/'intro_preview';OUT.mkdir(exist_ok=True)
blend=HERE/'scenes/clear/scene.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend))
scene=bpy.context.scene;cam=bpy.data.objects['Presentation'];scene.camera=cam
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
assert any(d.use for d in prefs.devices)
scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=24
scene.cycles.use_denoising=True;scene.cycles.denoiser='OPTIX';scene.render.use_persistent_data=True
scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=95
cam.data.clip_start=.005;cam.data.sensor_fit='AUTO';cam.data.dof.use_dof=False;cam.data.shift_x=0
bpy.data.objects['DRONE'].location=(0,0,.033)
bpy.data.objects['DRONE'].rotation_quaternion=(1,0,0,0)
preview='--preview' in sys.argv
shots={
 'ceiling':((-1,-1.8,1.65),(-.55,-1.65,1.60),(2.3,.35,2.45),27),
 'debris':((-.65,.3,.36),(-.25,.38,.38),(2,1.7,.28),30),
}
started=time.monotonic()
for name,(a,b,target,lens) in shots.items():
    dest=OUT/name;dest.mkdir(exist_ok=True)
    for i in ([67] if preview else range(135)):
        p=dest/f'{i:04d}.jpg'
        if p.exists():continue
        u=i/134;u=u*u*(3-2*u)
        cam.location=Vector(a).lerp(Vector(b),u)
        cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
        scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
        if i%30==0:print('INTRO_RENDER',name,i,round(time.monotonic()-started,1),flush=True)
(OUT/'environment_source.json').write_text(json.dumps(dict(blend_sha256=hashlib.sha256(blend.read_bytes()).hexdigest(),
    shots=shots,frames_per_shot=135,fps=30,scene_geometry_unchanged=True,
    role='Establishing imagery only; presentation camera is not a drone flight',renderer='Cycles OptiX',samples=24),indent=2))
print('INTRO_ENVIRONMENT_COMPLETE',round(time.monotonic()-started,1),flush=True)
