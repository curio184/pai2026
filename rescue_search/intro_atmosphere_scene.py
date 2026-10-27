"""Cinematic inserts: tested dust scene, recorded drone poses, slow detail cameras."""
import bpy,sys,json,bisect,hashlib,math,random,time
from pathlib import Path
from mathutils import Vector,Quaternion
HERE=Path(__file__).resolve().parent;OUT=HERE/'intro_atmosphere';OUT.mkdir(exist_ok=True)
blend=HERE/'scenes/dust/scene.blend';bpy.ops.wm.open_mainfile(filepath=str(blend))
scene=bpy.context.scene;cam=bpy.data.objects['Presentation'];scene.camera=cam
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='OPTIX'
assert any(d.use for d in prefs.devices)
scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=24
scene.cycles.use_denoising=True;scene.cycles.denoiser='OPTIX';scene.render.use_persistent_data=True
scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=96
cam.data.clip_start=.005;cam.data.sensor_fit='AUTO';cam.data.shift_x=0
cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=5.6
rows=[json.loads(s) for s in (HERE/'runs/eval03/dust_blue/trace.jsonl').read_text().splitlines()]
times=[r['t'] for r in rows];drone=bpy.data.objects['DRONE']

# Fine physical motes in world space. Cinematic illumination only; no new control-success claim.
rng=random.Random(2710)
mat=bpy.data.materials.new('Intro suspended dust');mat.diffuse_color=(.58,.49,.35,1);mat.use_nodes=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.58,.49,.35,1);bsdf.inputs['Roughness'].default_value=.9
verts=[];faces=[];origins=[]
for n in range(650):
    p=Vector((rng.uniform(-.6,3.8),rng.uniform(-1.5,2.3),rng.uniform(.12,3.1)))
    radius=rng.uniform(.0005,.0018);start=len(verts)
    for v in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:verts.append(tuple(p+Vector(v)*radius))
    for f in [(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]:faces.append(tuple(start+j for j in f))
mesh=bpy.data.meshes.new('Fine dust mesh');mesh.from_pydata(verts,[],faces);mesh.materials.append(mat)
motes=bpy.data.objects.new('Intro drifting dust',mesh);scene.collection.objects.link(motes)
lightdata=bpy.data.lights.new('Intro daylight shaft','SPOT');lightdata.energy=420;lightdata.color=(1,.9,.74);lightdata.spot_size=math.radians(34);lightdata.spot_blend=.7;lightdata.shadow_soft_size=.18
light=bpy.data.objects.new('Intro daylight shaft',lightdata);scene.collection.objects.link(light)
light.location=(.6,2.6,3.4);light.rotation_euler=(Vector((1.5,.3,.2))-light.location).to_track_quat('-Z','Y').to_euler()

shots=[('ceiling',6),('rubble',6),('drone',8)];preview='--preview' in sys.argv
metadata=[];started=time.monotonic()
for name,duration in shots:
    dest=OUT/name;dest.mkdir(exist_ok=True);count=duration*24
    for i in ([0,count//2,count-1] if preview else range(count)):
        u=i/(count-1);ease=u*u*(3-2*u);t=i/24
        moment=34+t;idx=max(0,bisect.bisect_right(times,moment)-1);r=rows[idx];p=Vector(r['truth'][19:22])
        drone.location=p;drone.rotation_quaternion=Quaternion(r['truth'][22:26])
        if name=='ceiling':
            cam.location=Vector((-.85,-1.6,1.75)).lerp(Vector((-.52,-1.45,1.8)),ease)
            target=Vector((1.9,.65,2.9));lens=34;focus=3.7;fstop=8
        elif name=='rubble':
            cam.location=Vector((-.45,.0,.23)).lerp(Vector((-.15,.12,.27)),ease)
            target=Vector((1.5,1.85,.13));lens=46;focus=2.7;fstop=5.6
        else:
            cam.location=p+Vector((-.38,-.47,.12));target=p+Vector((0,0,-.015));lens=49;focus=(cam.location-target).length;fstop=4
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
        cam.data.dof.focus_distance=focus;cam.data.dof.aperture_fstop=fstop
        motes.location=(.018*t,.007*math.sin(t*.6),-.008*t)
        file=dest/f'{i:04d}.jpg'
        if not file.exists():scene.render.filepath=str(file);bpy.ops.render.render(write_still=True)
        metadata.append(dict(shot=name,frame=i,trace_index=idx,simulation_time=r['t'],phase=r['phase']))
        if i%48==0:print('ATMOSPHERE_RENDER',name,i,count,round(time.monotonic()-started,1),flush=True)
if not preview:
    (OUT/'scene_source.json').write_text(json.dumps(dict(blend_sha256=hashlib.sha256(blend.read_bytes()).hexdigest(),
      run='eval03/dust_blue',fps=24,shots=shots,frames=metadata,source_geometry_unchanged=True,
      cinematic_additions=['650 fine world-space dust motes','soft daylight spotlight','presentation cameras and depth of field'],
      role='Atmospheric introduction, not a new flight evaluation; recorded drone poses from the existing successful dust run',
      renderer='Cycles OptiX',samples=24),indent=2))
print('ATMOSPHERE_RENDER_COMPLETE',flush=True)
