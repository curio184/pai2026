"""Presentation views from recorded flight poses in each unchanged tested scene."""
import bpy
import bisect
import hashlib
import json
import math
from pathlib import Path
import sys
import time
from mathutils import Vector,Quaternion
from bpy_extras.object_utils import world_to_camera_view

HERE=Path(__file__).resolve().parent
OUT=HERE/'movie'
plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
preview='--preview' in args
chosen=next((a.split('=',1)[1] for a in args if a.startswith('--segment=')),None)
def look(cam,loc,target,lens):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
def setup(condition):
    blend=HERE/'scenes'/condition/'scene.blend'
    expected=json.loads((HERE/'scenes'/condition/'physics/rescue_scene.render.json').read_text())['blend_sha256']
    assert hashlib.sha256(blend.read_bytes()).hexdigest()==expected
    bpy.ops.wm.open_mainfile(filepath=str(blend));scene=bpy.context.scene
    cam=bpy.data.objects['Presentation'];scene.camera=cam
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    assert any(d.use for d in prefs.devices)
    scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=24
    scene.cycles.use_denoising=True;scene.cycles.denoiser='OPTIX';scene.render.use_persistent_data=True
    scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=95
    cam.data.clip_start=.005;cam.data.dof.use_dof=False;cam.data.shift_x=0;cam.data.sensor_fit='AUTO'
    return scene,cam,bpy.data.objects['DRONE']

started=time.monotonic()
for segment in plan['segments']:
    if chosen and chosen!=segment['name']:continue
    scene,cam,drone=setup(segment['condition'])
    record=Path(segment['record']);rows=[json.loads(s) for s in (record/'trace.jsonl').read_text().splitlines()]
    times=[r['t'] for r in rows];score=json.loads((record/'search_score.json').read_text())
    dest=OUT/('preview' if preview else 'renders')/segment['name'];dest.mkdir(parents=True,exist_ok=True)
    count=round(segment['duration_s']*30)
    indices=sorted(set([0,count//4,count//2,3*count//4,count-1])) if preview else range(count)
    metadata=[]
    for i in indices:
        moment=min(segment['sim_end'],segment['sim_start']+i/30*segment['speed'])
        index=max(0,bisect.bisect_right(times,moment)-1);r=rows[index];p=Vector(r['truth'][19:22])
        drone.location=p;drone.rotation_quaternion=Quaternion(r['truth'][22:26])
        # Initial shots frame the drone without revealing the unseen target.
        if r['t']<score['discovery_time_s']:
            look(cam,p+Vector((-.33,-.45,.28)),p+Vector((0,0,.01)),42)
        else:
            u=max(0,min(1,(r['t']-score['discovery_time_s'])/1.2));u=u*u*(3-2*u)
            near=p+Vector((-.33,-.45,.28));wide=p+Vector((-.75,-1.35,.65))
            target=p.lerp(Vector((3.241,.808,1.05)),.44)
            look(cam,near.lerp(wide,u),(p+Vector((0,0,.01))).lerp(target,u),42*(1-u)+28*u)
        bpy.context.view_layer.update();projected=world_to_camera_view(scene,cam,p)
        meta=dict(frame=i,trace_index=index,simulation_time=r['t'],phase=r['phase'],projected=[1280*projected.x,800*(1-projected.y)])
        metadata.append(meta);file=dest/f'{i:04d}.jpg'
        if not file.exists():scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
        if i%120==0:print('SEARCH_MOVIE_RENDER',segment['name'],i,count,round(time.monotonic()-started,1),flush=True)
    (dest/'poses.json').write_text(json.dumps(metadata,separators=(',',':')))
print('SEARCH_MOVIE_RENDER_COMPLETE',round(time.monotonic()-started,1),flush=True)
