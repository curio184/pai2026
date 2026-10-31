import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Quaternion
W=Path(__file__).resolve().parents[1]
assert (W/'protocol/selected_final_round02_english.json').exists(),'Final candidate must be fixed first'
probe=json.loads((W/'protocol/static_probe_round02_english.json').read_text(encoding='utf-8'));out=W/'probe_round02_english/images';out.mkdir(parents=True,exist_ok=False)
for name in dict.fromkeys(f['scene'] for f in probe['frames']):
    src=W/'scenes'/name/'scene.blend';bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False)
    scene=bpy.context.scene;scene.camera=bpy.data.objects['front_rgb'];drone=bpy.data.objects['DRONE']
    shirts={}
    for c in ['blue','red']:
        m=bpy.data.objects[c+'_clothes'].data.materials[1]
        # Material name remains tied to its color, independently of its wearer.
        shirts['blue' if m.name.startswith('blue') else 'red']=m
    assert set(shirts)=={'blue','red'},list(shirts)
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='CUDA'
    scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=16;scene.cycles.seed=0
    scene.render.use_persistent_data=True;scene.render.resolution_x=320;scene.render.resolution_y=240;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    for f in [f for f in probe['frames'] if f['scene']==name]:
        for actor,c in enumerate(['blue','red']):bpy.data.objects[c+'_clothes'].data.materials[1]=shirts['blue' if actor==f['blue_actor'] else 'red']
        drone.location=f['qpos'][:3];drone.rotation_quaternion=Quaternion(f['qpos'][3:]);bpy.context.view_layer.update()
        scene.render.filepath=str(out/f"{f['id']:05d}.png");bpy.ops.render.render(write_still=True)
(W/'probe_round02_english/render_manifest.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),probe_plan_sha256=hashlib.sha256((W/'protocol/static_probe_round02_english.json').read_bytes()).hexdigest(),frames=len(probe['frames']),samples=16,width=320,height=240),indent=2))
