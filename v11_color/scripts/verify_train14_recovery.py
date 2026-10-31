"""Read a completed recovery save on CPU; never evaluate or select its model."""
import argparse,datetime,hashlib,json,zipfile
from pathlib import Path
import torch

W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--step',type=int,required=True);a=ap.parse_args()
    torch.set_num_threads(1)
    root=W/'models/train14_en';start=read(root/'started.json');plan=read(W/'protocol/train14_english.json')['training']
    assert a.step in range(plan['recovery_interval_steps'],plan['steps']+1,plan['recovery_interval_steps'])
    path=root/f'recovery_step{a.step:05d}.pt'
    receipt=read(path.with_suffix('.json'))
    digest=sha(path)
    assert receipt['step']==a.step and receipt['sha256']==digest and receipt['bytes']==path.stat().st_size
    assert receipt['plan_sha256']==start['plan_sha256']==sha(W/'protocol/train14_english.json')
    with zipfile.ZipFile(path) as archive:assert archive.testzip() is None
    state=torch.load(path,map_location='cpu',weights_only=False)
    assert state['step']==a.step and state['plan_sha256']==receipt['plan_sha256']
    assert state['initial_checkpoint_sha256']==start['initial_checkpoint_sha256']
    assert set(state['trainable_state'])==set(start['trainable_names'])
    assert all(torch.isfinite(p).all().item() for p in state['trainable_state'].values())
    optimizer_steps=sorted({int(x['step']) for x in state['optimizer']['state'].values()})
    assert optimizer_steps==[a.step]
    exposures=8*a.step
    assert int(state['image_exposure'].sum())==int(state['task_exposure'].sum())==exposures
    assert state['language_exposure'].tolist()==[0,0,exposures]
    assert state['noise_exposure']=={'runtime_fixed':exposures//2,'random':exposures//2}
    assert sum(state['batch_type_counts'].values())==exposures
    assert state['numpy_rng'] and state['torch_rng'].numel() and len(state['cuda_rng'])==1
    assert sha(path)==digest
    result=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        passed=True,candidate='train14_en',step=a.step,source=path.relative_to(W).as_posix(),
        source_sha256=digest,receipt_sha256=sha(path.with_suffix('.json')),bytes=path.stat().st_size,
        zip_crc_ok=True,finite_trainable_tensors=len(state['trainable_state']),optimizer_steps=optimizer_steps,
        exposures=exposures,noise_exposure=state['noise_exposure'],cpu_and_cuda_rng_present=True,
        plan_sha256=receipt['plan_sha256'],audit_script_sha256=sha(Path(__file__)),
        policy_inferences=0,optimizer_updates=0,original_files_modified=False,
        scope='Serialization integrity and saved metadata only. No flight, model-performance comparison, or checkpoint selection. The registered final8000 weights remain the only evaluation candidate.')
    dest=W/'reports'/f'train14_recovery_step{a.step:05d}_completion_audit.json'
    assert not dest.exists();dest.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result))

if __name__=='__main__':main()
