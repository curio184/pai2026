"""WSL-side live optical renderer bridge. Never sends world truth to the VLA.

Only this simulator rendering endpoint receives qpos, just like MuJoCo's camera.
The separate VLA link continues to send RGB, language and own estimated state.
"""
import base64,hashlib,io,json,socket,struct,time
from pathlib import Path
import numpy as np
from PIL import Image

def recv_exact(sock,n):
    blocks=bytearray()
    while len(blocks)<n:
        data=sock.recv(n-len(blocks))
        if not data:raise ConnectionError('Optical renderer disconnected')
        blocks.extend(data)
    return bytes(blocks)
def send(sock,obj):
    data=json.dumps(obj,separators=(',',':'),allow_nan=False).encode()
    sock.sendall(struct.pack('<I',len(data))+data)
def receive(sock):
    size=struct.unpack('<I',recv_exact(sock,4))[0]
    if size>2*1024*1024:raise ValueError('Oversized optical frame')
    return json.loads(recv_exact(sock,size))

class LiveCamera:
    def __init__(self,path,width=320,height=240):
        self.config=json.loads(Path(path).with_suffix('.render.json').read_text())
        self.width=width;self.height=height;self.counter=0
        self.listener=socket.socket();self.listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.listener.bind(('127.0.0.1',self.config['port']));self.listener.listen(1);self.listener.settimeout(75)
        self.connection,_=self.listener.accept();self.connection.settimeout(30)
        # Exactly one renderer belongs to this mission. Stop accepting immediately
        # so the next renderer session cannot attach to this old accept queue.
        self.listener.close()
        hello=receive(self.connection)
        if hello.get('blend_sha256')!=self.config['blend_sha256']:raise ValueError('Wrong live optical scene')
        self.provenance={'backend':'Blender Cycles CUDA live camera','blend_sha256':hello['blend_sha256'],'physics_scene_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'camera_calibration':self.config['camera'],'same_world_for_input_and_video':True}
    def render(self,qpos,qvel=None):
        self.counter+=1;pose=np.asarray(qpos,float)
        if pose.shape!=(7,) or not np.isfinite(pose).all():raise ValueError('Invalid physical camera pose')
        send(self.connection,{'id':self.counter,'qpos':pose.tolist(),'width':self.width,'height':self.height})
        data=receive(self.connection)
        if data.get('id')!=self.counter or data.get('qpos')!=pose.tolist():raise ValueError('Optical pose mismatch')
        raw=base64.b64decode(data['png_base64']);image=Image.open(io.BytesIO(raw)).convert('RGB')
        if image.size!=(self.width,self.height):raise ValueError('Optical frame size mismatch')
        return np.asarray(image).copy()
    def close(self):
        try:send(self.connection,{'close':True})
        except (OSError,AttributeError):pass
        for name in ('connection','listener'):
            item=getattr(self,name,None)
            if item:item.close()

