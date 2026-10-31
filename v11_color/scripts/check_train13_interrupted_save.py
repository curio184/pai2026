"""Read-only integrity check of an interrupted save; no model inference."""
import datetime,hashlib,json,zipfile
from pathlib import Path
import torch
W=Path(__file__).resolve().parents[1]; M=W/'models/train13_en'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()
torch.set_num_threads(2)
rows=[]
for name,expected in [('recovery.pt',1000),('recovery.pt.tmp',2000)]:
    p=M/name
    with zipfile.ZipFile(p) as z:assert z.testzip() is None
    s=torch.load(p,map_location='cpu',weights_only=False)
    assert s['step']==expected
    assert all(torch.isfinite(t).all().item() for t in s['trainable_state'].values())
    states=s['optimizer']['state'];assert states
    optimizer_steps=sorted({int(v['step'].item()) for v in states.values()})
    assert optimizer_steps==[expected]
    assert int(s['image_exposure'].sum())==int(s['task_exposure'].sum())==int(s['language_exposure'].sum())==expected*8
    assert s['initial_checkpoint_sha256']==json.loads((M/'started.json').read_text())['initial_checkpoint_sha256']
    assert s['numpy_rng'] and s['torch_rng'].numel()>0 and len(s['cuda_rng'])==1
    rows.append(dict(file=name,sha256=sha(p),step=expected,zip_crc_ok=True,finite_trainable_parameters=True,
        trainable_tensors=len(s['trainable_state']),optimizer_steps=optimizer_steps,
        exposures=int(s['image_exposure'].sum()),cpu_and_cuda_rng_present=True))
    del s
out=W/'reports/train13_interrupted_save_integrity.json'; assert not out.exists()
r=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=rows,
    latest_complete_step=2000,chosen_by_step_only=True,policy_inferences=0,optimizer_updates=0,
    original_files_modified=False,cause='Observed WinError5 during os.replace after torch.save. The holder/cause of the denial is not established.')
out.write_text(json.dumps(r,indent=2),encoding='utf8'); print(json.dumps(r))
