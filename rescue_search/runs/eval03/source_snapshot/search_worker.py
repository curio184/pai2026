"""Connect the Windows GPU policy to the loopback Linux simulation server."""
import sys, os
sys.path.insert(0,os.environ["RESCUE_PROJECT_ROOT"])
import argparse
import base64
import io
import json
from pathlib import Path
import socket
import time
import hashlib

from PIL import Image
import torch
from smolvla_policy import DroneVLA
from perception import PersonPerception
from vla_link import receive,send


def run(args):
    torch.manual_seed(20261024)
    torch.cuda.manual_seed_all(20261024)
    perception=PersonPerception()
    policy=DroneVLA(args.checkpoint)
    digest=hashlib.sha256()
    with (args.checkpoint/"model.safetensors").open("rb") as handle:
        for block in iter(lambda:handle.read(4*1024*1024),b""):digest.update(block)
    checkpoint_hash=digest.hexdigest()
    if args.ready_file:
        with args.ready_file.open("x",encoding="utf-8") as handle:
            json.dump(dict(loaded=True,policy_kind="SmolVLA",checkpoint_sha256=checkpoint_hash,inference_seed=20261024),handle,indent=2)
    session=0
    deadline=time.monotonic()+args.connect_timeout
    while session<args.sessions:
        while True:
            try:
                sock=socket.create_connection(("127.0.0.1",args.port),timeout=2)
                break
            except OSError:
                if time.monotonic()>=deadline:raise
                time.sleep(.25)
        processed=0
        with sock:
            sock.settimeout(120)
            while True:
                try:request=receive(sock)
                except ConnectionError:break
                if request.get("version")!=1:raise ValueError("Unknown simulator protocol")
                rgb=Image.open(io.BytesIO(base64.b64decode(request["rgb_jpeg_base64"]))).convert("RGB")
                start=time.monotonic()
                chunk=policy.infer_chunk(rgb,request["instruction"],request["state"])
                response=dict(perception=perception.detect(rgb),id=request["id"],action=chunk[0].tolist(),action_chunk=chunk.tolist(),action_dt_s=.1,inference_s=time.monotonic()-start,
                              policy_kind="SmolVLA",checkpoint_sha256=checkpoint_hash)
                try:send(sock,response)
                except (BrokenPipeError,ConnectionResetError):break
                print(json.dumps(dict(session=session,id=request["id"],inference_s=response["inference_s"])),flush=True)
                processed+=1
        # A loopback forwarder can accept then close a stale connection between
        # WSL servers. Only a session with actual inference counts as completed.
        if processed:
            session+=1
            deadline=time.monotonic()+args.connect_timeout
        else:
            if time.monotonic()>=deadline:
                raise TimeoutError("No policy request received before connection deadline")
            time.sleep(.25)


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--checkpoint",type=Path,required=True)
    p.add_argument("--port",type=int,default=17866)
    p.add_argument("--ready-file",type=Path)
    p.add_argument("--connect-timeout",type=float,default=60)
    p.add_argument("--sessions",type=int,default=1)
    run(p.parse_args())
