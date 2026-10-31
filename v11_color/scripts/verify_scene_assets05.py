"""Read-only scene/score alignment audit. No render, inference, or trial."""
import bpy,json,hashlib,xml.etree.ElementTree as ET,datetime
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[1];P=W.parent

def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=P/'tmp/rescue_search/scenes/clear'
bpy.ops.wm.open_mainfile(filepath=str(source/'scene.blend'),load_ui=False,use_scripts=False)
base={o.name:dict(location=list(o.location),rotation=list(o.rotation_euler),scale=list(o.scale)) for o in bpy.data.objects if o.name.startswith(('blue_','red_'))}
assert len(base)==14
world=ET.parse(source/'physics/rescue_scene.xml').getroot().find('worldbody')
original={color:Vector([float(x) for x in world.find(f"body[@name='{color}_person']").get('pos').split()]) for color in ['blue','red']}
checks=[]
for protocol,groups in [('plan.json',['development_layouts','heldout_layouts']),('round02_english.json',['heldout_layouts'])]:
    planfile=W/'protocol'/protocol;plan=read(planfile)
    for layout in [l for g in groups for l in plan[g]]:
        folder=W/'scenes'/layout['name'];meta=read(folder/'provenance.json')
        assert meta['plan_sha256']==sha(planfile) and meta['layout']==layout
        assert meta['physics_sha256']==sha(folder/'physics/rescue_scene.xml')
        assert meta['blend_sha256']==sha(folder/'scene.blend')
        xml=ET.parse(folder/'physics/rescue_scene.xml').getroot().find('worldbody')
        for color in ['blue','red']:
            actor=layout['blue_actor'] if color=='blue' else 1-layout['blue_actor']
            position=[float(x) for x in xml.find(f"body[@name='{color}_person']").get('pos').split()]
            assert max(abs(a-b) for a,b in zip(position,layout['positions'][actor]))<1e-10
        bpy.ops.wm.open_mainfile(filepath=str(folder/'scene.blend'),load_ui=False,use_scripts=False)
        for actor,color in enumerate(['blue','red']):
            objects=[o for o in bpy.data.objects if o.name.startswith(color+'_')];assert len(objects)==7
            delta=Vector(layout['positions'][actor])-original[color]
            for o in objects:
                assert o.parent is None
                expected=Vector(base[o.name]['location'])+delta
                assert (o.location-expected).length<1e-6,(layout['name'],o.name)
                assert list(o.rotation_euler)==base[o.name]['rotation'] and list(o.scale)==base[o.name]['scale']
            shirt=bpy.data.objects[color+'_clothes'].data.materials[1].name
            expected_color='blue' if actor==layout['blue_actor'] else 'red'
            assert shirt==expected_color+'_v2_top',shirt
        checks.append(dict(scene=layout['name'],protocol=protocol,physics_and_render_colors_match=True,all_14_person_object_transforms_verified=True,scene_sha256=meta['blend_sha256']))
r=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,checks=checks,scope='Read-only inspection of saved Blender transforms/materials and physics target coordinates; no image rendering or model evaluation',rendered_images=0,policy_inferences=0)
out=W/'reports/train05_scene_assets_preflight_audit.json';assert not out.exists();out.write_text(json.dumps(r,indent=2),encoding='utf8');print(json.dumps(dict(passed=True,scenes=len(checks))),flush=True)
