"""Build frozen optical variants; no physics parameters or person placement change."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Quaternion
ROOT=Path.cwd();OUT=ROOT/'tmp/rescue_search';source=ROOT/'assets/civic_realism/revision03.blend'
conditions=[('clear',.004,(.8,.8,.8,1)),('fog_light',.06,(.85,.88,.9,1)),('fog_dense',.12,(.85,.88,.9,1)),('dust',.12,(.62,.52,.38,1))]
manifest=[]
for name,density,color in conditions:
    bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
    node=bpy.data.materials['Thin airborne dust'].node_tree.nodes['Volume Scatter']
    if name!='clear':node.inputs['Density'].default_value=density;node.inputs['Color'].default_value=color
    scene.camera=bpy.data.objects['front_rgb'];drone=bpy.data.objects['DRONE']
    bpy.context.preferences.filepaths.save_version=0
    dest=OUT/'scenes'/name;dest.mkdir(parents=True,exist_ok=True)
    file=dest/'scene.blend';assert not file.exists()
    bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='CUDA'
    scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=16;scene.render.resolution_x=320;scene.render.resolution_y=240;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    for pose,yaw in [('initial',math.pi/2),('forward',0)]:
        drone.location=(0,0,1);drone.rotation_quaternion=Quaternion((math.cos(yaw/2),0,0,math.sin(yaw/2)))
        scene.render.filepath=str(dest/(pose+'.png'));bpy.ops.render.render(write_still=True)
    manifest.append(dict(name=name,scatter_density=density,color=list(node.inputs['Color'].default_value),blend_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),physical_aerosol_calibrated=False))
(OUT/'scene_conditions.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('SEARCH_SCENES_PREPARED',flush=True)
