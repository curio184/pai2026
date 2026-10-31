"""Measure VLA-only inference time on the RTX 3080 with nothing else using the GPU.

This is the inference term of the real-system latency budget (no Blender in a real system).
200 timed calls after 10 warm-up calls, 5 flow steps, same image/prompt/state.
"""
import sys,time,json,statistics as st,datetime,hashlib
from pathlib import Path
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W/'runtime_rebuild04'))
import torch
from PIL import Image
from smolvla_policy import DroneVLA
ck=W/'models/train16_en/final';img=W/'runs/rebuild04_final/R4F01/record/observations/00040.jpg'
p=DroneVLA(ck);p.policy.model.config.num_steps=5
im=Image.open(img).convert('RGB');s=[0.1,0,0,1,0,0,0,0,1];prompt='Approach the person wearing blue and stop.'
for _ in range(10):p.infer_chunk(im,prompt,s)
ts=[]
for _ in range(200):
    torch.cuda.synchronize();t=time.perf_counter();p.infer_chunk(im,prompt,s);torch.cuda.synchronize();ts.append(time.perf_counter()-t)
ts.sort()
r=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),gpu=torch.cuda.get_device_name(0),num_steps=5,calls=len(ts),
  median_s=st.median(ts),p10_s=ts[19],p90_s=ts[179],p99_s=ts[197],max_s=ts[-1],image=str(img),checkpoint_sha256=hashlib.sha256((ck/'model.safetensors').read_bytes()).hexdigest(),
  note='GPU otherwise idle (no Blender). In-flight inference times are longer because Blender renders on the same GPU.')
(W/'results/rebuild04_inference_benchmark.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=1))
