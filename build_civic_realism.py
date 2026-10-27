"""Versioned naturalism revision; never overwrites the validated civic world."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from civic_humans_v2 import build_person
OUT=ROOT/'assets/civic_realism';OUT.mkdir(exist_ok=True)
PREVIEW=ROOT/'output/environment/realism';PREVIEW.mkdir(parents=True,exist_ok=True)
old=ROOT/'assets/civic_world/civic_world.blend'
bpy.ops.wm.open_mainfile(filepath=str(old));scene=bpy.context.scene
for obj in list(bpy.data.objects):
    if obj.get('physical_role')=='person_visual':bpy.data.objects.remove(obj,do_unlink=True)
people={'blue':[3.2410745738240734,.8084203589462445,0],'red':[3.1455626580655522,-.6848188536753865,0]}
for color,height in [('blue',1.70),('red',1.63)]:build_person(color,people[color],height)

# Match the light source's apparent size to a hazy daylight scene. Window
# silhouettes still cast physical shadows, but do not dominate the tiny craft.
sun=bpy.data.objects['Sun through damaged windows'];sun.data.energy=2.15;sun.data.angle=.13;sun.data.color=(1,.88,.73)
bpy.data.objects['Soft sky window light'].data.energy=340
bpy.data.objects['Interior diffuse bounce'].data.energy=65
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.42
scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=.25

# True tangent-space normal maps, with metric planar UVs on each surface.
for matname,asset,scale in [('Chipped aged plaster','worn_plaster_wall',.55),('Dusty concrete','concrete_floor_02',.48),('Exposed brick masonry','red_brick_03',.65)]:
    mat=bpy.data.materials[matname];nodes=mat.node_tree.nodes;links=mat.node_tree.links
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map='MetricSurfaceUV'
    for node in list(nodes):
        if node.type=='BUMP':nodes.remove(node)
        elif node.type=='TEX_IMAGE':
            node.projection='FLAT';links.new(uv.outputs['UV'],node.inputs['Vector'])
    normalpath=ROOT/'assets/civic_sources'/asset/'nor_gl.jpg'
    if normalpath.exists():
        tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(normalpath),check_existing=True);tex.image.colorspace_settings.name='Non-Color'
        normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.55;normal.uv_map='MetricSurfaceUV'
        links.new(uv.outputs['UV'],tex.inputs['Vector']);links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],nodes['Principled BSDF'].inputs['Normal'])
    for obj in scene.objects:
        if obj.type!='MESH' or mat not in list(obj.data.materials):continue
        layer=obj.data.uv_layers.get('MetricSurfaceUV') or obj.data.uv_layers.new(name='MetricSurfaceUV')
        for poly in obj.data.polygons:
            normalworld=obj.matrix_world.to_3x3()@poly.normal
            dominant=max(range(3),key=lambda i:abs(normalworld[i]));axes=[i for i in range(3) if i!=dominant]
            for li in poly.loop_indices:
                v=obj.matrix_world@obj.data.vertices[obj.data.loops[li].vertex_index].co
                layer.data[li].uv=(v[axes[0]]*scale,v[axes[1]]*scale)

prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='OPTIX'
scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=96;scene.cycles.use_denoising=True
scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
cam=bpy.data.objects['Presentation'];scene.camera=cam;cam.data.dof.use_dof=False
drone=bpy.data.objects['DRONE'];drone.location=(2.15,.65,1.0)
# Match the rounded capsule endpoints of the existing MuJoCo landing legs.
for x in (-.025,.025):
    for y in (-.025,.025):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.003,location=(x,y,-.029))
        cap=bpy.context.object;cap.name='Physical landing foot';cap.parent=drone;cap.data.materials.append(bpy.data.materials['Dark rubber'])
        for face in cap.data.polygons:face.use_smooth=True
def shoot(name,loc,target,lens=35,size=(1600,1000)):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.shift_x=0
    scene.render.resolution_x,scene.render.resolution_y=size;scene.render.filepath=str(PREVIEW/(name+'.png'));bpy.ops.render.render(write_still=True)
shoot('people',(.0,-1.8,1.45),(3.2,.10,.92),42)
shoot('blue_close',(1.25,-.25,1.6),(3.18,.82,1.25),58)
shoot('feet',(2.1,-.4,.30),(3.2,.15,.1),48)
drone.location=(0,0,.032);shoot('drone_ground',(-.20,-.28,.18),(0,0,.035),50,(1280,800))
drone.location=(0,0,.25);shoot('drone_air',(-.25,-.40,.40),(0,0,.12),36,(1280,800))
drone.location=(0,0,.04);drone.rotation_quaternion=(1,0,0,0)
scene.camera=bpy.data.objects['front_rgb'];scene.render.resolution_x=320;scene.render.resolution_y=240;scene.cycles.samples=16
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'revision02.blend'))
report={'source_scene_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'people':people,'grounding':{c:dict(bpy.data.objects[c+'_shoes'].items()) for c in people},'policy_success_claimed':False,'preview_only_until_new_live_validation':True}
(OUT/'design.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('REALISM_REVISION_BUILT',flush=True)
