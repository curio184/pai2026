"""Remove a coplanar volume/floor boundary; keep the corrected scene separate."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=ROOT/'assets/civic_realism/revision02.blend';target=ROOT/'assets/civic_realism/revision03.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
fog=bpy.data.objects['Room air'];fog.location.z=1.55;fog.dimensions.z=3.3
scene.camera=bpy.data.objects['front_rgb'];scene.render.resolution_x=320;scene.render.resolution_y=240
bpy.ops.wm.save_as_mainfile(filepath=str(target))
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=96
scene.camera=bpy.data.objects['Presentation'];scene.render.resolution_x=1280;scene.render.resolution_y=800
bpy.data.objects['DRONE'].location=(0,0,.25)
scene.render.filepath=str(ROOT/'output/environment/realism/drone_air_volume_fixed.png');bpy.ops.render.render(write_still=True)
print('VOLUME_FIX_PREVIEW_READY',hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)
