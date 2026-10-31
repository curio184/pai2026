"""Windows Blender client for the running WSL simulation's forward camera."""
import bpy,sys,json,base64,socket,time,hashlib,tempfile,os
from pathlib import Path
from mathutils import Quaternion
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
# Keep the transport dependency tiny: Blender does not need torch/LeRobot.
import struct
def receive(sock):
    def exact(n):
        out=bytearray()
        while len(out)<n:
            part=sock.recv(n-len(out))
            if not part:raise ConnectionError('Camera server closed')
            out.extend(part)
        return bytes(out)
    n=struct.unpack('<I',exact(4))[0]
    if n>1024*1024:raise ValueError('Oversized camera pose')
    return json.loads(exact(n))
def send(sock,obj):
    data=json.dumps(obj,separators=(',',':'),allow_nan=False).encode();sock.sendall(struct.pack('<I',len(data))+data)

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
sessions=int(args[0]) if args else 4
blend=Path(args[2]).resolve() if len(args)>2 else ROOT/'assets/civic_world/civic_world.blend'
digest=hashlib.sha256(blend.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(blend));scene=bpy.context.scene;scene.camera=bpy.data.objects['front_rgb']
drone=bpy.data.objects['DRONE']
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='CUDA'
if not any(d.use for d in prefs.devices):raise RuntimeError('CUDA renderer unavailable')
scene.render.engine='CYCLES';scene.cycles.device='GPU';scene.cycles.samples=16
scene.render.use_persistent_data=True
scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
cache=Path(tempfile.gettempdir())/f'civic_live_camera_{os.getpid()}.png';scene.render.filepath=str(cache)
for warmup in range(3):
    at=time.monotonic();bpy.ops.render.render(write_still=True)
    print('OPTICAL_WARMUP',warmup,time.monotonic()-at,flush=True)
if len(args)>1:Path(args[1]).write_text(json.dumps({'blend_sha256':digest,'ready':True}))
print('OPTICAL_CLIENT_LOADED',digest,flush=True)
session=0;deadline=time.monotonic()+900
while session<sessions:
    sock=socket.socket();sock.settimeout(30)
    while True:
        try:sock.connect(('127.0.0.1',17867));break
        except (ConnectionRefusedError,TimeoutError,OSError):
            sock.close();sock=socket.socket();sock.settimeout(30)
            if time.monotonic()>deadline:raise TimeoutError('No simulation camera server within 900 seconds')
            time.sleep(.25)
    count=0
    try:
        send(sock,{'blend_sha256':digest,'renderer':'Blender Cycles CUDA','version':bpy.app.version_string})
        while True:
            request=receive(sock)
            if request.get('close'):break
            p=request['qpos'];drone.location=p[:3];drone.rotation_quaternion=Quaternion(p[3:])
            scene.render.resolution_x=int(request['width']);scene.render.resolution_y=int(request['height'])
            at=time.monotonic();bpy.ops.render.render(write_still=True)
            send(sock,{'id':request['id'],'qpos':p,'png_base64':base64.b64encode(cache.read_bytes()).decode(),'render_seconds':time.monotonic()-at})
            count+=1
            if count%20==0:print('LIVE_OPTICAL_FRAMES',session,count,flush=True)
    except (ConnectionError,OSError):print('OPTICAL_SESSION_CLOSED',session,count,flush=True)
    finally:sock.close()
    if count:
        print('OPTICAL_SESSION_COMPLETE',session,count,flush=True)
        session+=1;deadline=time.monotonic()+900
    elif time.monotonic()>deadline:raise TimeoutError('No optical request before connection deadline')
    time.sleep(.4)
print('OPTICAL_CLIENT_COMPLETE',flush=True)
