"""Make preregistered scene assets, without running any evaluation policy."""
import bpy,json,hashlib,shutil,xml.etree.ElementTree as ET
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1];P=W.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((W/'protocol/round02_english.json').read_text(encoding='utf-8'))
source=P/'tmp/rescue_search/scenes/clear'
for layout in plan['heldout_layouts']:
    dest=W/'scenes'/layout['name'];dest.mkdir(parents=True,exist_ok=False)
    shutil.copytree(source/'physics',dest/'physics')
    tree=ET.parse(source/'physics/rescue_scene.xml');world=tree.getroot().find('worldbody')
    persons=[world.find(f"body[@name='{c}_person']") for c in ['blue','red']]
    original=[Vector([float(x) for x in body.get('pos').split()]) for body in persons]
    for i,c in enumerate(['blue','red']):
        actor=layout['blue_actor'] if c=='blue' else 1-layout['blue_actor']
        persons[i].set('pos',' '.join(map(str,layout['positions'][actor])))
    tree.write(dest/'physics/rescue_scene.xml',encoding='utf-8',xml_declaration=True)
    bpy.ops.wm.open_mainfile(filepath=str(source/'scene.blend'),load_ui=False,use_scripts=False)
    shirts=[bpy.data.objects[c+'_clothes'].data.materials[1] for c in ['blue','red']]
    changes=[]
    for actor,c in enumerate(['blue','red']):
        objs=[o for o in bpy.data.objects if o.name.startswith(c+'_')];assert len(objs)==7
        for o in objs:
            assert o.parent is None
            o.location+=Vector(layout['positions'][actor])-original[actor]
        shirt=shirts[0 if actor==layout['blue_actor'] else 1]
        bpy.data.objects[c+'_clothes'].data.materials[1]=shirt
        changes.append(dict(actor=c,position=layout['positions'][actor],shirt_material=shirt.name))
    bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(dest/'scene.blend'),compress=True)
    desc=json.loads((dest/'physics/rescue_scene.render.json').read_text())
    desc.update(blend_sha256=sha(dest/'scene.blend'),blend_relative='../scene.blend')
    (dest/'physics/rescue_scene.render.json').write_text(json.dumps(desc,indent=2))
    (dest/'provenance.json').write_text(json.dumps(dict(layout=layout,visual_changes=changes,physics_color_positions={c:persons[i].get('pos') for i,c in enumerate(['blue','red'])},blend_sha256=desc['blend_sha256'],physics_sha256=sha(dest/'physics/rescue_scene.xml'),source_blend_sha256=sha(source/'scene.blend'),script_sha256=sha(Path(__file__)),plan_sha256=sha(W/'protocol/round02_english.json'),policy_executed=False),indent=2))
    print('SCENE_READY',layout['name'],flush=True)
