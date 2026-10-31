"""Verify final-step weights against the resumed optimizer save, without inference."""
import datetime,hashlib,json
from pathlib import Path
import numpy as np
import torch
from safetensors import safe_open
W=Path(__file__).resolve().parents[1];M=W/'models/train13_en'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()
def main():
    out=W/'reports/train13_resume01_completion_audit.json';assert not out.exists()
    torch.set_num_threads(2)
    original=read(M/'started.json');result=read(M/'result.json');resume=read(M/'resume01_started.json')
    amendment=W/'protocol/train13_resume01.json';a=read(amendment)
    assert result['optimizer_steps_completed']==original['config']['steps']==a['final_step']==6000
    assert result['resume_step']==resume['resume_step']==a['resume_step']==2000
    assert result['resume_amendment_sha256']==resume['resume_amendment_sha256']==sha(amendment)
    assert result['selection']=='Final step only' and result['resumed']
    assert all(resume[k] for k in ['restored_trainable_parameters_exactly','optimizer_restored','numpy_cpu_cuda_rng_restored'])
    assert sha(M/'failure.json')==a['failure_sha256'] and sha(M/'training.jsonl')==a['original_training_log_sha256']
    segments=[]
    for name,low,high in [('training.jsonl',1,2000),('training_resume01.jsonl',2010,6000)]:
        rows=[json.loads(line) for line in (M/name).read_text().splitlines()]
        steps=[r['step'] for r in rows];assert steps==sorted(set(steps)) and min(steps)==low and max(steps)==high
        expected=([1] if low==1 else [])+list(range(10 if low==1 else low,high+1,10))
        assert steps==expected
        segments.append(dict(file=name,sha256=sha(M/name),first_recorded_step=low,last_recorded_step=high,logged_steps=len(steps)))
    recovery=M/'recovery_resume01_step06000.pt';receipt=read(M/'recovery_resume01_step06000.json')
    assert receipt['step']==6000 and receipt['complete'] and receipt['sha256']==sha(recovery)
    s=torch.load(recovery,map_location='cpu',weights_only=False);assert s['step']==6000
    assert sorted({int(v['step'].item()) for v in s['optimizer']['state'].values()})==[6000]
    final=M/'final/model.safetensors';assert sha(final)==result['checkpoint_sha256']
    checked=0
    with safe_open(final,framework='pt',device='cpu') as f:
        for name,tensor in s['trainable_state'].items():
            assert name in f.keys(),name
            saved=f.get_tensor(name);assert saved.dtype==tensor.dtype and torch.equal(saved,tensor),name
            checked+=1
    assert checked==len(original['trainable_names'])==155
    exposure=read(M/'sampling_exposure.json')
    for key,outputkey in [('image_exposure','image_counts'),('task_exposure','task_counts'),('language_exposure','language_counts')]:
        assert np.array_equal(s[key],exposure[outputkey])
    assert exposure['total_samples']==int(s['image_exposure'].sum())==48000
    assert exposure['noise_exposure']=={'runtime_fixed':24000,'random':24000}
    saved_audit=W/'reports/train13_en_saved_training_verification.json';v=read(saved_audit)
    assert v['passed'] and v['final_step']==6000 and v['checkpoint_sha256']==result['checkpoint_sha256'] and not v['unexpected_changed_tensors']
    proof=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,candidate='train13_en',
        final_step=6000,resume_step=2000,checkpoint_sha256=result['checkpoint_sha256'],
        amendment_sha256=sha(amendment),final_recovery_sha256=receipt['sha256'],
        final_trainable_tensors_equal_recovery=checked,optimizer_step=6000,exposures=48000,
        training_segments=segments,original_error_and_log_preserved=True,
        frozen_backbone_verification_sha256=sha(saved_audit),policy_inferences=0,optimizer_updates=0,
        scope='Saved-state and log provenance check only; not a flight-performance test or intermediate checkpoint selection.')
    out.write_text(json.dumps(proof,indent=2),encoding='utf8');print(json.dumps(proof))
if __name__=='__main__':main()
