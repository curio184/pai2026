"""Reuse atmosphere setup; render a fixed-position slow pan and focus pull to the survivor."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
source=(HERE/'intro_atmosphere_scene.py').read_text(encoding='utf8')
source=source.replace("OUT=HERE/'intro_atmosphere'","OUT=HERE/'intro_pan'")
source=source.replace("shots=[('ceiling',6),('rubble',6),('drone',8)]","shots=[('drone',8)]")
source=source.replace("([0,count//2,count-1] if preview else range(count))","([0,count//4,count//2,3*count//4,count-1] if preview else range(count))")
old="cam.location=p+Vector((-.38,-.47,.12));target=p+Vector((0,0,-.015));lens=49;focus=(cam.location-target).length;fstop=4"
new="""start_idx=max(0,bisect.bisect_right(times,34)-1)
            origin=Vector(rows[start_idx]['truth'][19:22])
            cam.location=origin+Vector((-.38,-.47,.12))
            first=origin+Vector((0,0,-.015));last=Vector((3.241,.808,1.35))
            # Slerp the camera orientation, not the target positions: constant angular progress.
            q0=(first-cam.location).to_track_quat('-Z','Y')
            q1=(last-cam.location).to_track_quat('-Z','Y')
            pan=max(0,min(1,(t-.45)/6.55));pan=pan*pan*(3-2*pan)
            tilt=max(0,min(1,(t-.45)/2.8));tilt=tilt*tilt*(3-2*tilt)
            a=first-cam.location;b=last-cam.location
            yaw=math.atan2(a.y,a.x)*(1-pan)+math.atan2(b.y,b.x)*pan
            pitch=math.atan2(a.z,math.hypot(a.x,a.y))*(1-tilt)+math.atan2(b.z,math.hypot(b.x,b.y))*tilt
            direction=Vector((math.cos(pitch)*math.cos(yaw),math.cos(pitch)*math.sin(yaw),math.sin(pitch)))
            target=cam.location+direction
            lens=49;focus=(first-cam.location).length*(1-pan)+(last-cam.location).length*pan;fstop=4"""
assert old in source;source=source.replace(old,new)
source=source.replace("phase=r['phase']))","phase=r['phase'],camera_position=list(cam.location),camera_quaternion=list(cam.rotation_euler.to_quaternion()),focus_distance=focus))")
exec(compile(source,str(HERE/'intro_atmosphere_scene.py'),'exec'))
