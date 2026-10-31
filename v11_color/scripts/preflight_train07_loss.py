"""Training-only weighted-loss preflight. No optimizer steps or evaluation inputs."""
import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONUTF8='1')
import hashlib,json,sys,datetime
from pathlib import Path
import numpy as np
import torch
from PIL import Image
W=Path(__file__).resolve().parents[1];P=W.parent
sys.path.insert(0,str(P));sys.path.insert(0,str(W/'scripts'))
from train07_en import weighted_loss,sha,frozen_vlm_digest
from finetune_smolvla import normalized_state
from smolvla_policy import DroneVLA

def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
    out=W/'reports/train07_loss_preflight_audit.json';assert not out.exists()
    full=read(W/'protocol/train07_english.json');plan=full['training'];lock=read(W/'protocol/train07_english_implementation.json')
    assert sha(W/'scripts/train07_en.py')==lock['trainer_sha256']
    data=W/'data/dataset07_en';assert sha(data/'audit.json')==lock['dataset_audit_sha256']
    sources=read(data/'image_sources.json');manifest=read(data/'manifest.json')
    with np.load(data/'audited_samples.npz') as a:
        indices=np.asarray([np.flatnonzero(a['task']==t)[0] for t in [0,1,4,6]])
        state=normalized_state(a['state'][indices]);labels=a['action'][indices];tasks=a['task'][indices];images=a['image'][indices]
    assert set(tasks.tolist())=={0,1,4,6}
    checkpoint=P/plan['initial_checkpoint'];assert sha(checkpoint/'model.safetensors')==plan['initial_checkpoint_sha256']
    torch.manual_seed(plan['seed']);torch.cuda.manual_seed_all(plan['seed'])
    model=DroneVLA(checkpoint,chunk_size=32)
    for name,p in model.policy.named_parameters():
        if name.startswith('model.vlm_with_expert.vlm.'):p.requires_grad_(False)
    before=frozen_vlm_digest(model.policy);model.policy.eval()
    rgb=np.stack([np.asarray(Image.open(W/sources[int(i)]['path']).convert('RGB')) for i in images])
    prompts=[manifest['prompt_variants'][int(t)][2] for t in tasks]
    assert all(x.isascii() for x in prompts)
    tokens=model.tokenizer(prompts,padding='max_length',max_length=48,truncation=True,return_tensors='pt')
    batch={'observation.images.camera1':torch.from_numpy(rgb).permute(0,3,1,2).float().cuda()/255,'observation.state':torch.from_numpy(state).cuda(),'observation.language.tokens':tokens['input_ids'].cuda(),'observation.language.attention_mask':tokens['attention_mask'].bool().cuda(),'action':torch.from_numpy(labels).cuda()}
    noise=model.policy.model.sample_noise((4,32,32),device='cuda');t=torch.tensor([.1,.4,.7,1.],device='cuda')
    with torch.no_grad(),torch.autocast('cuda',dtype=torch.bfloat16):
        reference,_=model.policy(batch,noise=noise,time=t)
        uniform=weighted_loss(model.policy,batch,noise,t,[1.]*6)
    assert torch.allclose(reference.float(),uniform.float(),rtol=1e-5,atol=1e-6)
    model.policy.train();model.policy.model.vlm_with_expert.vlm.eval()
    with torch.autocast('cuda',dtype=torch.bfloat16):weighted=weighted_loss(model.policy,batch,noise,t,plan['action_loss_weights'])
    assert torch.isfinite(weighted)
    weighted.backward();active=[]
    for name,p in model.policy.named_parameters():
        if name.startswith('model.vlm_with_expert.vlm.'):assert p.grad is None
        elif p.grad is not None:
            assert torch.isfinite(p.grad).all(),name
            if torch.count_nonzero(p.grad):active.append(name)
    assert active
    assert frozen_vlm_digest(model.policy)==before
    r=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope='Training-only forward/backward preflight; no optimizer updates, flight, validation, or checkpoint selection',optimizer_steps=0,checkpoint_sha256=plan['initial_checkpoint_sha256'],training_indices=indices.tolist(),tasks=tasks.tolist(),prompts=prompts,library_uniform_loss=float(reference),local_uniform_loss=float(uniform),weighted_loss=float(weighted.detach()),gradient_parameters=len(active),frozen_parameters_unchanged=True,trainer_sha256=lock['trainer_sha256'],dataset_audit_sha256=lock['dataset_audit_sha256'])
    out.write_text(json.dumps(r,indent=2),encoding='utf8');print(json.dumps(r),flush=True)
if __name__=='__main__':main()
