"""CC0 human revision: skeletal skinning, fitted clothes and measured grounding.

Rest weights and skeleton are from MakeHuman's CC0 default rig. Clothing uses
the author's barycentric proxy mapping to transfer the same skeletal weights.
No spatial arm mask or hand-drawn displacement is used for posing.
"""
import json, math, re
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector, Matrix
from civic_humans import obj_data, material, fitted, SRC, MH, BASE
import civic_humans as original
REST=BASE

RIG=json.loads((SRC/'rig/default.mhskel').read_text())
WEIGHTS=json.loads((SRC/'rig/default_weights.mhw').read_text())['weights']
NAMES=list(RIG['bones'])
W=np.zeros((len(BASE[0]),len(NAMES)))
for j,name in enumerate(NAMES):
    for i,w in WEIGHTS.get(name,[]): W[i,j]=w
W/=np.maximum(W.sum(axis=1,keepdims=True),1e-12)

def align(a,b):
    return np.asarray(Vector(a).rotation_difference(Vector(b)).to_matrix())

def skin_transforms(color):
    transforms={}
    shift=np.array([.24 if color=='blue' else -.20,-.08,0.0])
    def joint(name):return BASE[0][RIG['joints'][RIG['bones'][name]['head']]].mean(axis=0)
    knees={}
    for suffix in ('.L','.R'):
        hip0=joint('upperleg01'+suffix);knee0=joint('lowerleg01'+suffix);ankle=joint('foot'+suffix)
        hip=hip0+shift;delta=ankle-hip;distance=np.linalg.norm(delta);direction=delta/distance
        upper=np.linalg.norm(knee0-hip0);lower=np.linalg.norm(ankle-knee0)
        along=(upper*upper-lower*lower+distance*distance)/(2*distance)
        forward=np.array([0.,0.,1.]);forward-=direction*np.dot(forward,direction);forward/=np.linalg.norm(forward)
        knees[suffix]=hip+direction*along+forward*math.sqrt(max(0,upper*upper-along*along))
    def solve(name):
        if name in transforms:return transforms[name]
        bone=RIG['bones'][name]
        parent=solve(bone['parent']) if bone['parent'] else np.eye(4)
        h=BASE[0][RIG['joints'][bone['head']]].mean(axis=0)
        t=BASE[0][RIG['joints'][bone['tail']]].mean(axis=0)
        r=np.eye(3);side=1 if name.endswith('.L') else -1
        if name.startswith('upperleg01'):
            desired=knees[name[-2:]]-(parent@np.r_[h,1])[:3]
            r=align(joint('lowerleg01'+name[-2:])-h,parent[:3,:3].T@desired)
        elif name.startswith('lowerleg01'):
            desired=joint('foot'+name[-2:])-(parent@np.r_[h,1])[:3]
            r=align(joint('foot'+name[-2:])-h,parent[:3,:3].T@desired)
        elif name.startswith('foot.'):
            r=parent[:3,:3].T
        elif name=='spine02':
            r=np.asarray(Matrix.Rotation(math.radians(-1.2 if color=='blue' else 1.2),3,'Z'))
        elif name.startswith('upperarm01'):
            desired=np.array([side*(.13 if color=='blue' else .10),-1,.055])
            r=align(t-h,parent[:3,:3].T@desired)
        elif name.startswith('lowerarm01'):
            desired=np.array([side*.035,-1,.16 if (side==1)==(color=='blue') else .075])
            r=align(t-h,parent[:3,:3].T@desired)
        elif name.startswith('wrist'):
            desired=np.array([side*.02,-1,.05])
            r=align(t-h,parent[:3,:3].T@desired)
        elif name.startswith('finger') and not name.startswith('finger1'):
            # Gentle relaxed finger curl about the rest palm's transverse axis.
            r=np.asarray(Matrix.Rotation(math.radians(-9 if '-1.' in name else -13),3,'X'))
        elif name=='head':
            r=np.asarray(Matrix.Rotation(math.radians(4 if color=='blue' else -5),3,'Y'))
        local=np.eye(4);local[:3,:3]=r;local[:3,3]=h-r@h
        if name=='root':local[:3,3]+=shift
        transforms[name]=parent@local
        return transforms[name]
    return np.asarray([solve(name) for name in NAMES])

def proxy_weights(path):
    rows=[];started=False
    for line in path.with_suffix('.mhclo').read_text(encoding='utf8').splitlines():
        s=line.split()
        if not s or s[0].startswith('#'):continue
        if s[0]=='verts':started=True;continue
        if started:
            if not s[0].lstrip('-').isdigit():
                if rows:break
                continue
            if len(s)==1:rows.append(W[int(s[0])])
            elif len(s)>=9:
                weight=np.maximum(np.asarray(s[3:6],float),0);weight/=weight.sum()
                rows.append(weight@W[np.asarray(s[:3],int)])
    return np.asarray(rows)

def surface_detail(mat,path,cloth=False):
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;p=nodes['Principled BSDF']
    if path.exists():
        tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True);tex.image.colorspace_settings.name='Non-Color'
        normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.65
        links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],p.inputs['Normal'])
    if cloth:
        p.inputs['Roughness'].default_value=.83;p.inputs['Sheen'].default_value=.22
        p.inputs['Specular'].default_value=.24
        noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=480;noise.inputs['Detail'].default_value=2
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.00035
        links.new(noise.outputs['Fac'],bump.inputs['Height'])
        if p.inputs['Normal'].is_linked:links.new(p.inputs['Normal'].links[0].from_socket,bump.inputs['Normal'])
        links.new(bump.outputs['Normal'],p.inputs['Normal'])

def build_person(color,loc,height):
    global BASE
    sex='male' if color=='blue' else 'female'
    shaped=REST[0].copy()
    for age,weight in [('young',.8),('old',.2)]:
        for name in (f'asian-{sex}-{age}.target',f'universal-{sex}-{age}-averagemuscle-averageweight.target'):
            for line in (SRC/'rig'/name).read_text().splitlines():
                values=line.split()
                if values and values[0].isdigit():shaped[int(values[0])]+=weight*np.asarray(values[1:4],float)
    BASE=(shaped,*REST[1:]);original.BASE=BASE
    costume='male_casualsuit03'
    skinpath=MH/'skins'/('middleage_asian_male' if color=='blue' else 'middleage_asian_female')
    skin=material(color+'_v2_skin',next(skinpath.glob('*diffuse*.png')))
    skinshader=skin.node_tree.nodes['Principled BSDF']
    skinshader.inputs['Subsurface'].default_value=.12
    skinshader.inputs['Subsurface Radius'].default_value=(.004,.0018,.001)
    skinshader.inputs['Roughness'].default_value=.48
    folder=MH/'clothes'/costume;clothtex=folder/(costume+'_diffuse.png')
    denim=material(color+'_v2_denim',clothtex)
    top=material(color+'_v2_top',clothtex,(.055,.18,.36) if color=='blue' else (.40,.045,.035))
    tint=(.055,.18,.36) if color=='blue' else (.40,.045,.035)
    ramp=next(n for n in top.node_tree.nodes if n.type=='VALTORGB')
    ramp.color_ramp.elements[0].color=(*[v*(.38 if color=='blue' else .65) for v in tint],1)
    ramp.color_ramp.elements[1].color=(*[v*1.20 for v in tint],1)
    for mat in (denim,top):surface_detail(mat,folder/(costume+'_normal.png'),True)
    deleted=set()
    for name in (costume,'shoes01'):
        text=(MH/'clothes'/name/(name+'.mhclo')).read_text()
        if 'delete_verts' in text:
            for token in re.findall(r'\d+\s*-\s*\d+|\d+',text.split('delete_verts',1)[1]):
                ids=list(map(int,re.findall(r'\d+',token)));deleted.update(range(ids[0],ids[-1]+1))
    transforms=skin_transforms(color);scale=height/16.9455;objects=[]
    def add(name,path,mat,body=False,clothing=False):
        vertices,uv,faces,tex=BASE if body else obj_data(path)
        if body:
            keep=[i for i,f in enumerate(faces) if not all(v in deleted for v in f)]
            faces=[faces[i] for i in keep];tex=[tex[i] for i in keep];weights=W
        else:vertices=fitted(path,vertices);weights=proxy_weights(path)
        rest=vertices.copy();v4=np.column_stack((vertices,np.ones(len(vertices))))
        posed=np.zeros((len(vertices),3))
        for j,tr in enumerate(transforms):
            posed+=weights[:,j,None]*(v4@tr.T)[:,:3]
        world=np.column_stack((-posed[:,2],posed[:,0],posed[:,1]+8.4488))*scale+loc
        used=sorted({v for f in faces for v in f});mapping={v:i for i,v in enumerate(used)}
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(world[used],[],[[mapping[v] for v in f] for f in faces]);mesh.update()
        obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj);mesh.materials.append(mat)
        if clothing:mesh.materials.append(top)
        layer=mesh.uv_layers.new(name='UVMap')
        # Shirt and trousers are separate islands in both source outfits.
        shirt=set()
        if clothing:
            adjacency={v:set() for v in used}
            for f in faces:
                for v in f:adjacency[v].update(f)
            pending=set(used)
            while pending:
                seed=pending.pop();component={seed};stack=[seed]
                while stack:
                    for v in adjacency[stack.pop()]:
                        if v in pending:pending.remove(v);component.add(v);stack.append(v)
                if rest[list(component),1].max()>2.8:shirt.update(component)
        for i,p in enumerate(mesh.polygons):
            p.use_smooth=True
            for li,ti in zip(p.loop_indices,tex[i]):layer.data[li].uv=uv[ti]
            if clothing and faces[i][0] in shirt:p.material_index=1
        if body or clothing:
            sub=obj.modifiers.new('Smooth fitted surface','SUBSURF');sub.levels=1;sub.render_levels=2
        obj['physical_role']='person_visual';obj['person_color']=color;obj['pose_method']='MakeHuman CC0 skeletal weights + proxy transfer'
        objects.append(obj);return obj
    add(color+'_anatomy',SRC/'base.obj',skin,body=True)
    add(color+'_clothes',folder/(costume+'.obj'),denim,clothing=True)
    hairstyle='short02' if color=='blue' else 'bob01';path=MH/'hair'/hairstyle
    add(color+'_hair',path/(hairstyle+'.obj'),material(color+'_v2_hair',path/(hairstyle+'_diffuse.png'),alpha=True))
    eye=material(color+'_v2_eyes',MH/'eyes/materials/brown_eye.png',alpha=True);eye.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.2
    add(color+'_eyes',MH/'eyes/high-poly/high-poly.obj',eye)
    for category,part in [('eyebrows','eyebrow001'),('eyelashes','eyelashes01')]:
        path=MH/category/part
        add(color+'_'+part,path/(part+'.obj'),material(color+'_v2_'+part,path/(part+'.png'),alpha=True))
    path=MH/'clothes/shoes01';shoe=add(color+'_shoes',path/'shoes01.obj',material(color+'_v2_leather',path/'shoes01_diffuse.png'))
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();evaluated=shoe.evaluated_get(deps)
    zmin=min((evaluated.matrix_world@v.co).z for v in evaluated.data.vertices)
    for obj in objects:obj.location.z-=zmin
    bpy.context.view_layer.update()
    top=max((o.evaluated_get(deps).matrix_world@v.co).z for o in objects for v in o.evaluated_get(deps).data.vertices)
    factor=height/top;pivot=Vector((loc[0],loc[1],0))
    for obj in objects:
        for vertex in obj.data.vertices:
            vertex.co=pivot+(obj.matrix_world@vertex.co-pivot)*factor
        obj.location=(0,0,0)
    # Keep an inspectable metric record on the person, rather than eyeballing.
    shoe['grounding_translation_m']=-zmin;shoe['floor_z_m']=0.0
    original.BASE=REST;BASE=REST
    return objects
