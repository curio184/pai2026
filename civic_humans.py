"""Build clothed, relaxed-pose humans from CC0 MakeHuman art assets in Blender."""
import math,re
from pathlib import Path
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent;SRC=ROOT/'assets/civic_sources';MH=SRC/'makehuman'

def obj_data(path,group=None):
    vs=[];uv=[];faces=[];tex=[];current=''
    for l in path.read_text(encoding='utf8').splitlines():
        s=l.split()
        if not s:continue
        if s[0]=='v':vs.append(list(map(float,s[1:4])))
        elif s[0]=='vt':uv.append(list(map(float,s[1:3])))
        elif s[0]=='g':current=s[1]
        elif s[0]=='f' and (group is None or current==group):
            parts=[v.split('/') for v in s[1:]]
            faces.append([int(p[0])-1 for p in parts]);tex.append([int(p[1])-1 if len(p)>1 and p[1] else 0 for p in parts])
    return np.asarray(vs),uv,faces,tex

BASE=obj_data(SRC/'base.obj','body')

def fitted(path,vertices):
    mhclo=path.with_suffix('.mhclo')
    if not mhclo.exists():return vertices
    source=BASE[0];rows=[];started=False;scales=np.ones(3)
    for line in mhclo.read_text(encoding='utf8').splitlines():
        s=line.split()
        if not s or s[0].startswith('#'):continue
        if s[0] in ('x_scale','y_scale','z_scale'):
            axis='xyz'.index(s[0][0]);scales[axis]=abs(source[int(s[1]),axis]-source[int(s[2]),axis])/float(s[3])
        if s[0]=='verts':started=True;continue
        if started:
            if not s[0].lstrip('-').isdigit():
                if rows:break
                continue
            if len(s)==1:rows.append(source[int(s[0])])
            elif len(s)>=9:rows.append(np.asarray(s[3:6],float)@source[np.asarray(s[:3],int)]+np.asarray(s[6:9],float)*scales)
    if len(rows)!=len(vertices):raise ValueError((path,len(rows),len(vertices)))
    return np.asarray(rows)

def material(name,texture=None,tint=None,alpha=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;nodes=m.node_tree.nodes;links=m.node_tree.links
    p=nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.76
    if texture:
        tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(texture),check_existing=True)
        color=tex.outputs['Color']
        if tint:
            gray=nodes.new('ShaderNodeRGBToBW');links.new(color,gray.inputs[0])
            ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*[x*.16 for x in tint],1)
            ramp.color_ramp.elements[1].position=.95;ramp.color_ramp.elements[1].color=(*[min(1,c*1.65) for c in tint],1)
            links.new(gray.outputs[0],ramp.inputs[0]);color=ramp.outputs[0]
        links.new(color,p.inputs['Base Color'])
        if alpha:
            links.new(tex.outputs['Alpha'],p.inputs['Alpha']);m.blend_method='HASHED';m.use_screen_refraction=False;m.shadow_method='HASHED'
    if name.endswith('skin'):
        p.inputs['Subsurface'].default_value=.055;p.inputs['Roughness'].default_value=.62
    return m

def relaxed(v):
    a=v.copy();side=np.sign(a[:,0]);w=np.clip((np.abs(a[:,0])-1.25)/.7,0,1)
    w*=np.clip((a[:,1]+1.0)/1.4,0,1)*np.clip((6.1-a[:,1])/1.0,0,1)
    angle=-side*w*math.radians(21);dx=a[:,0]-side*1.55;dy=a[:,1]-4.35
    a[:,0]=side*1.55+dx*np.cos(angle)-dy*np.sin(angle)
    a[:,1]=4.35+dx*np.sin(angle)+dy*np.cos(angle)
    return a

def mesh(name,path,loc,height,mat,base=False,clothing=False,topmat=None):
    vertices,uv,faces,tex=BASE if base else obj_data(path)
    if not base:vertices=fitted(path,vertices)
    # Drop body surfaces hidden by clothes to avoid skin poke-through.
    if base:
        deleted=set()
        for costume in ['male_casualsuit05','shoes01']:
            content=(MH/'clothes'/costume/(costume+'.mhclo')).read_text(encoding='utf8')
            if 'delete_verts' not in content:continue
            for token in re.findall(r'\d+\s*-\s*\d+|\d+',content.split('delete_verts',1)[1]):
                ids=[int(x) for x in re.findall(r'\d+',token)]
                deleted.update(range(ids[0],ids[-1]+1))
        keep=[i for i,f in enumerate(faces) if not all(v in deleted for v in f)]
        faces=[faces[i] for i in keep];tex=[tex[i] for i in keep]
    rest=vertices.copy();vertices=relaxed(vertices)
    scale=height/16.9455
    transformed=np.column_stack((-vertices[:,2],vertices[:,0],vertices[:,1]+8.4488))*scale+loc
    used=sorted({v for face in faces for v in face});mapping={old:new for new,old in enumerate(used)}
    newfaces=[[mapping[v] for v in face] for face in faces]
    data=bpy.data.meshes.new(name);data.from_pydata(transformed[used],[],newfaces);data.update()
    o=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(o);data.materials.append(mat)
    if topmat:data.materials.append(topmat)
    # Connected mesh islands identify the jacket independently from trouser
    # height; a horizontal threshold would incorrectly paint the upper jeans.
    topfaces=set()
    if clothing:
        adjacency={v:set() for v in used}
        for face in faces:
            for v in face:adjacency[v].update(face)
        unvisited=set(used)
        while unvisited:
            seed=unvisited.pop();component={seed};stack=[seed]
            while stack:
                for v in adjacency[stack.pop()]:
                    if v in unvisited:unvisited.remove(v);component.add(v);stack.append(v)
            if rest[list(component),1].max()>2.8:topfaces.update(component)
    layer=data.uv_layers.new(name='UVMap')
    for i,p in enumerate(data.polygons):
        p.use_smooth=True
        for loop,ti in zip(p.loop_indices,tex[i]):layer.data[loop].uv=uv[ti]
        if clothing and topmat and faces[i][0] in topfaces:p.material_index=1
    if base or clothing:
        sub=o.modifiers.new('Human surface refinement','SUBSURF');sub.levels=1;sub.render_levels=1
    return o

def build_person(color,loc,height):
    skinpath=MH/'skins'/('middleage_asian_male' if color=='blue' else 'middleage_asian_female')
    skintex=next(skinpath.glob('*diffuse*.png'))
    skin=material(color+'_skin',skintex)
    clothes=MH/'clothes/male_casualsuit05'
    clothtex=clothes/'male_casualsuit05_diffuse.png'
    denim=material(color+'_denim',clothtex)
    jacket=material(color+'_jacket',clothtex,(.045,.19,.51) if color=='blue' else (.43,.045,.025))
    objects=[mesh(color+'_anatomy',SRC/'base.obj',loc,height,skin,base=True),
             mesh(color+'_clothes',clothes/'male_casualsuit05.obj',loc,height,denim,clothing=True,topmat=jacket)]
    hairstyle='short02' if color=='blue' else 'bob01';path=MH/'hair'/hairstyle
    objects.append(mesh(color+'_hair',path/(hairstyle+'.obj'),loc,height,material(color+'_hairmat',path/(hairstyle+'_diffuse.png'),alpha=True)))
    eyes=mesh(color+'_eyes',MH/'eyes/high-poly/high-poly.obj',loc,height,material(color+'_irises',MH/'eyes/materials/brown_eye.png'))
    eyes.location.x=-.0015;eyes.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.18
    objects.append(eyes)
    path=MH/'clothes/shoes01'
    objects.append(mesh(color+'_shoes',path/'shoes01.obj',loc,height,material(color+'_shoe_leather',path/'shoes01_diffuse.png')))
    for o in objects:o['physical_role']='person_visual';o['person_color']=color
    return objects
