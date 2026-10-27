"""Offline studio camera orbit; separate illustration, never a flight replay."""
import bpy
import math
import sys
import time
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'tmp/premium'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'stampfly_studio.blend'))
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=48
scene.eevee.use_gtao=True;scene.eevee.gtao_distance=3;scene.eevee.gtao_factor=1.1
scene.eevee.use_soft_shadows=True;scene.eevee.use_bloom=True;scene.eevee.bloom_intensity=.025
scene.eevee.shadow_cube_size='2048';scene.eevee.shadow_cascade_size='4096'
scene.render.resolution_x=1920;scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=96
cam=scene.camera
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
test='--test' in args
start=time.monotonic()
for label,count,one,two,target in [
    ('opening',240,(15,-22,16),(12.8,-23,14),(0,0,.8)),
    ('closing',390,(11,-12,10),(13.2,-13.7,10.8),(2.3,0,1.3))]:
    dest=OUT/label;dest.mkdir(exist_ok=True)
    for i in ([0,count-1] if test else range(count)):
        u=i/(count-1);u=u*u*(3-2*u)
        cam.location=Vector(one).lerp(Vector(two),u)
        cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(dest/f'{i:04}.jpg')
        bpy.ops.render.render(write_still=True)
        if i%30==0:print('STUDIO_PROGRESS',label,i,count,round(time.monotonic()-start,1),flush=True)
print('STUDIO_ANIMATION_COMPLETE',round(time.monotonic()-start,1),flush=True)
