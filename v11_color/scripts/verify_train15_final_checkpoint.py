"""Prove the final model equals the registered final optimizer-step snapshot."""
import datetime,hashlib,json
from pathlib import Path
import torch
from safetensors import safe_open
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
def main():
    root=W/'models/train15_en';start=read(root/'started.json');result=read(root/'result.json')
    saved=read(W/'reports/train15_en_saved_training_verification.json');assert saved['passed']
    steps=start['config']['steps'];assert steps==6000==result['optimizer_steps_completed']
    source=root/f'recovery_step{steps:05d}.pt';receipt=read(source.with_suffix('.json'))
    assert receipt['step']==steps and receipt['bytes']==source.stat().st_size and receipt['sha256']==sha(source)
    state=torch.load(source,map_location='cpu',weights_only=False)
    assert state['step']==steps and state['plan_sha256']==start['plan_sha256']
    assert state['initial_checkpoint_sha256']==start['initial_checkpoint_sha256']
    assert state['noise_exposure']=={'runtime_fixed':24000,'random':24000}
    assert int(state['image_exposure'].sum())==48000
    assert state['language_exposure'].tolist()==[0,0,48000]
    trained=set(start['trainable_names']);assert set(state['trainable_state'])==trained
    final=root/'final/model.safetensors';assert sha(final)==result['checkpoint_sha256']==saved['checkpoint_sha256']
    with safe_open(final,framework='pt',device='cpu') as target:
        assert trained<=set(target.keys())
        for name,tensor in state['trainable_state'].items():
            assert torch.equal(tensor,target.get_tensor(name)),name
            assert torch.isfinite(tensor).all(),name
    optimizer_steps=sorted(set(int(x['step']) for x in state['optimizer']['state'].values()))
    assert optimizer_steps==[steps]
    logs=[json.loads(x) for x in (root/'training.jsonl').read_text().splitlines()]
    assert [x['step'] for x in logs]==[1]+list(range(10,6001,10))
    assert all(x['loss']>=0 for x in logs)
    report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,
        candidate='train15_en',optimizer_steps=steps,exposures=48000,trainable_tensors_equal=len(trained),
        final_sha256=sha(final),recovery_sha256=sha(source),plan_sha256=start['plan_sha256'],
        saved_weight_audit_sha256=sha(W/'reports/train15_en_saved_training_verification.json'),
        scope='CPU comparison of final optimizer snapshot and all saved trainable tensors, plus registered step/exposure/log continuity; no policy inference or updates.')
    out=W/'reports/train15_final_checkpoint_completion_audit.json';assert not out.exists()
    out.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
if __name__=='__main__':main()
