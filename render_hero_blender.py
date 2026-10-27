"""Studio illustration of the actual upstream StampFly meshes; no flight claims."""
import bpy
import math
import os
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'tmp/premium'
OUT.mkdir(parents=True,exist_ok=True)
MESH=Path(os.environ.get('STAMPFLY_MESH_DIR',r'\\wsl.localhost\Ubuntu-22.04\home\curio\physical_ai_stampfly\stampfly_ecosystem\simulator\shared\assets\meshes\parts'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=96
scene.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='CUDA'
    prefs.get_devices()
    for dev in prefs.devices:
        dev.use=dev.type=='CUDA'
    if any(d.type=='CUDA' for d in prefs.devices):scene.cycles.device='GPU'
except Exception as exc:print('CPU_FALLBACK',exc,flush=True)
scene.render.resolution_x=2560
scene.render.resolution_y=1440
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.world.color=(.025,.035,.055)
scene.view_settings.view_transform='Filmic'
scene.view_settings.look='Medium High Contrast'
scene.view_settings.exposure=.5

def material(name,color,metal=.0,rough=.3,emission=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    node=m.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Metallic'].default_value=metal
    node.inputs['Roughness'].default_value=rough
    if emission:
        node.inputs['Emission'].default_value=(*color,1)
        node.inputs['Emission Strength'].default_value=emission
    return m
white=material('Pearl polymer',(.72,.79,.82),.15,.24)
black=material('Carbon electronics',(.013,.024,.03),.45,.28)
orange=material('Stamp orange',(.98,.21,.025),.2,.24)
rotor=material('Coral rotors',(.94,.08,.09),.15,.24)
silver=material('Brushed motor cans',(.65,.72,.76),.82,.22)
green=material('Camera PCB',(.035,.21,.13),.25,.3)
lens=material('Optical glass',(.025,.1,.14),.7,.1)
teal=material('Signal cyan',(.02,.55,.6),.2,.22,3)
floor=material('Midnight studio',(.008,.019,.028),.35,.33)
root=bpy.data.objects.new('StampFly studio model',None)
scene.collection.objects.link(root)
for file in sorted(MESH.glob('*.stl')):
    if file.stem not in {'frame','pcb','m5stamps3','battery','battery_adapter','motor_fl','motor_fr','motor_rl','motor_rr','propeller_fl','propeller_fr','propeller_rl','propeller_rr'}:continue
    bpy.ops.import_mesh.stl(filepath=str(file))
    obj=bpy.context.object;obj.name=file.stem
    obj.scale=(.1,.1,.1)
    obj.rotation_mode='QUATERNION';obj.rotation_quaternion=(.5,.5,.5,.5)
    obj.parent=root
    m=white if file.stem=='frame' else orange if file.stem=='m5stamps3' else rotor if file.stem.startswith('propeller') else silver if file.stem.startswith('motor') else black
    obj.data.materials.append(m)
    for polygon in obj.data.polygons:polygon.use_smooth=True
    bevel=obj.modifiers.new('Small manufactured edge highlights','BEVEL');bevel.width=.018;bevel.segments=2
    obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')

def cube(name,loc,scale,mat,bevel=.035):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name;o.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat);o.parent=root
    if bevel:
        mod=o.modifiers.new('Edge radius','BEVEL');mod.width=bevel;mod.segments=3
        o.modifiers.new('Normals','WEIGHTED_NORMAL')
    return o
cube('RGB camera package - schematic', (0,0,2.2),(2.1,1.78,1.5),green)
cube('Camera face', (1.08,0,2.2),(.2,1.2,1.0),black)
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.32,depth=.28,location=(1.25,0,2.2),rotation=(0,math.pi/2,0))
bpy.context.object.data.materials.append(lens);bpy.context.object.parent=root
cube('Optical flow package - schematic',(0,0,-2), (2.16,1.6,.65),black)
for x in (-2.5,2.5):
    for y in (-2.5,2.5):cube('Stand-off',(x,y,-2),( .42,.42,2.0),black)
root.location=(2.3,0,2)
root.rotation_euler=(math.radians(4),math.radians(-8),math.radians(-16))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-2))
bpy.context.object.data.materials.append(floor)
for r in (5.2,5.3,8):
    bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.012,major_segments=128,minor_segments=6,location=(2.3,0,-1.97))
    bpy.context.object.data.materials.append(teal)

def area(name,loc,color,energy,size,target=(2,0,1)):
    data=bpy.data.lights.new(name,'AREA');data.color=color;data.energy=energy;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
area('Large soft key',(0,-7,15),(.74,.86,1),2400,9)
area('Cyan edge',(5,6,9),(.12,.8,1),3000,7)
area('Warm rim',(0,3,3),(1,.35,.12),1200,5)
area('Front fill',(-8,-5,5),(.8,.86,1),600,8)
camdata=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.lens=49
for label,loc,target in [('hero',(15,-22,16),(0,0,.8)),('detail',(11,-12,10),(2.3,0,1.3)),('top',(3,-.5,25),(2.3,0,0))]:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/f'{label}.png')
    bpy.ops.render.render(write_still=True)
    print('STUDIO_RENDER_COMPLETE',label,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'stampfly_studio.blend'))
