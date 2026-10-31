import bpy,sys,json,time,hashlib,shutil,argparse
from pathlib import Path
from mathutils import Vector,Quaternion
W=Path(__file__).resolve().parents[1];P=W.parent
a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int);args=parser.parse_args(a)
plan=json.loads((W/'protocol/plan.json').read_text(encoding='utf8'));frames=json.loads((W/'protocol/train05_training_frames.json').read_text(encoding='utf8'))
recipe=json.loads((W/'protocol/train05_english.json').read_text(encoding='utf8'))
registration=json.loads((W/'protocol/train05_data_registration.json').read_text(encoding='utf8'))
assert hashlib.sha256((W/'protocol/train05_training_frames.json').read_bytes()).hexdigest()==registration['frames_sha256']
assert hashlib.sha256((W/'protocol/train05_english.json').read_bytes()).hexdigest()==registration['plan_sha256']
source=P/'tmp/rescue_search/scenes/clear/scene.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()==recipe['data_generation']['source_blend_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
scene=bpy.context.scene;scene.camera=bpy.data.objects['front_rgb'];drone=bpy.data.objects['DRONE']
positions=[Vector((3.2410745738240734,.8084203589462445,0)),Vector((3.1455626580655522,-.6848188536753865,0))]
groups=[[o for o in bpy.data.objects if o.name.startswith(color+'_')] for color in ['blue','red']]
assert all(len(g)==7 for g in groups)
original_locs={o.name:o.location.copy() for g in groups for o in g}
shirts=[bpy.data.objects[c+'_clothes'].data.materials[1] for c in ['blue','red']]
assert all(m.name.endswith('_v2_top') for m in shirts)
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
for dev in prefs.devices:dev.use=dev.type=='CUDA'
assert any(d.use for d in prefs.devices)
scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=16;scene.cycles.seed=0
scene.render.use_persistent_data=True;scene.render.resolution_x=320;scene.render.resolution_y=240;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
out=W/'data/rendered05_png';out.mkdir(exist_ok=True)
meta=dict(train05_plan_sha256=registration['plan_sha256'],frames_sha256=registration['frames_sha256'],source_blend_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),plan_sha256=hashlib.sha256((W/'protocol/plan.json').read_bytes()).hexdigest(),engine='Cycles CUDA',samples=16,seed=0,width=320,height=240,clothing_swap='Exchange only shirt material slot 1, keeping identities/geometry/poses fixed in each pair',density=.004)
(W/'data/render05_manifest.json').write_text(json.dumps(meta,indent=2))
start=time.monotonic();done=0
for f in frames[:args.limit] if args.limit else frames:
 dest=out/f"{f['id']:05d}.png"
 if dest.exists():continue
 if shutil.disk_usage(W).free<5*1024**3:raise RuntimeError('Disk reserve reached; consult user before moving anything')
 layout=plan['train_layouts'][f['layout']]
 for actor,g in enumerate(groups):
  offset=Vector(layout['positions'][actor])-positions[actor]
  for o in g:o.location=original_locs[o.name]+offset
  bpy.data.objects[['blue','red'][actor]+'_clothes'].data.materials[1]=shirts[0 if actor==f['blue_actor'] else 1]
 drone.location=f['qpos'][:3];drone.rotation_quaternion=Quaternion(f['qpos'][3:]);bpy.context.view_layer.update()
 scene.render.filepath=str(dest);bpy.ops.render.render(write_still=True);done+=1
 if done%20==0 or done==1:
  result=dict(last_id=f['id'],new_images=done,elapsed_s=time.monotonic()-start,total=len(frames));(W/'data/render05_progress.json').write_text(json.dumps(result));print('COLOR_RENDER',json.dumps(result),flush=True)
print('COLOR_RENDER_FINISHED',done,flush=True)
