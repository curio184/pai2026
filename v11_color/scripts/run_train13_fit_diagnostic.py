"""Run the preregistered training-data fit diagnostic; never changes flight inference."""
import os,sys,json,hashlib,datetime
from pathlib import Path
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONUTF8='1')
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W.parent))
import numpy as np
import torch
from PIL import Image
import psutil
from smolvla_policy import DroneVLA,ACTION_SCALE
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=W/'protocol/train13_fit_diagnostic.json';plan=read(p)
    assert sha(Path(__file__))==plan['runner_sha256']
    status=read(W/'pipeline_train13_resume01_status.json');assert status['stage']=='development_review'
    try:
        process=psutil.Process(904)
        assert process.create_time()!=1793335480.9748113,'Wait until the existing pipeline exits'
    except psutil.NoSuchProcess:pass
    data=W/'data/dataset13_en';assert sha(data/'audit.json')==plan['dataset_audit_sha256']
    for f,h in read(data/'audit.json')['files'].items():assert sha(data/f)==h
    modeldir=W/'models/train13_en/final';assert sha(modeldir/'model.safetensors')==plan['checkpoint_sha256']
    with np.load(data/'audited_samples.npz') as a:arrays={k:a[k] for k in a.files}
    sources=read(data/'image_sources.json');manifest=read(data/'manifest.json')
    out=W/'reports/train13_fit_diagnostic';assert not out.exists();out.mkdir()
    (out/'started.json').write_text(json.dumps(dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(p)),indent=2),encoding='utf8')
    torch.manual_seed(20261024);torch.cuda.manual_seed_all(20261024)
    model=DroneVLA(modeldir);assert model.policy.config is model.policy.model.config
    assert model.policy.config.num_steps==10 and model.inference_seed==plan['runtime_noise_seed']
    rows=[]
    with (out/'raw_outputs.jsonl').open('x',encoding='utf8') as raw:
        for selection in plan['selected']:
            i=selection['sample_index'];source=sources[selection['image_index']]
            assert int(arrays['image'][i])==selection['image_index'] and int(arrays['task'][i])==selection['task']
            file=W/source['path'];assert sha(file)==source['sha256']
            image=Image.open(file).convert('RGB');prompt=manifest['prompt_variants'][selection['task']][2]
            teacher=arrays['action'][i]*ACTION_SCALE
            for steps in plan['inference_steps']:
                model.policy.config.num_steps=steps
                try:action=model.infer_chunk(image,prompt,arrays['state'][i])
                finally:model.policy.config.num_steps=10
                err=action-teacher
                row=dict(**selection,inference_steps=steps,image_sha256=source['sha256'],prompt=prompt,
                    state=arrays['state'][i].tolist(),action_chunk=action.tolist(),teacher_chunk=teacher.tolist(),
                    first10_axis_mae=np.abs(err[:10]).mean(0).tolist(),full32_axis_mae=np.abs(err).mean(0).tolist(),
                    first10_horizontal_vector_rmse=float(np.sqrt(np.mean(np.sum(err[:10,:2]**2,axis=1)))))
                raw.write(json.dumps(row)+'\n');raw.flush();rows.append(row)
            print(json.dumps(dict(completed=len(rows)//2,planned=112)),flush=True)
    groups=[]
    for steps in plan['inference_steps']:
        for task in range(7):
            rr=[r for r in rows if r['inference_steps']==steps and r['task']==task]
            assert len(rr)==16
            groups.append(dict(inference_steps=steps,task=task,samples=len(rr),
                mean_first10_axis_mae=np.mean([r['first10_axis_mae'] for r in rr],axis=0).tolist(),
                median_horizontal_vector_rmse=float(np.median([r['first10_horizontal_vector_rmse'] for r in rr]))))
    assert sha(modeldir/'model.safetensors')==plan['checkpoint_sha256']
    report=dict(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),complete=True,samples=112,outputs=len(rows),
        plan_sha256=sha(p),checkpoint_sha256=plan['checkpoint_sha256'],groups=groups,
        no_updates=True,no_flights=True,runtime_configuration_unchanged=True,
        scope=plan['limitations'])
    (out/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
if __name__=='__main__':main()
