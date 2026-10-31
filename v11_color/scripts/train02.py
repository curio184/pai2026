"""Train02: fixed 6,000 steps, no evaluation-based checkpoint selection."""
import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONUTF8='1')
import sys,json,hashlib,random,math,time,shutil
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parents[1];P=W.parent;sys.path.insert(0,str(P))
import numpy as np
from PIL import Image
import torch
from finetune_smolvla import normalized_state
from smolvla_policy import DroneVLA
def sha(p):
    d=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):d.update(b)
    return d.hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def train():
    planfile=W/'protocol/train02.json';full=json.loads(planfile.read_text(encoding='utf-8'));plan=full['training']
    assert sha(planfile)=='a86ce9228f8ccaa900351600fb733bb027534332644bb3cae9df0e81a35cc1a3'
    data=W/'data/dataset02';out=W/plan['output'];checkpoint=P/plan['initial_checkpoint']
    assert not out.exists(),'Never overwrite a training attempt'
    assert sha(checkpoint/'model.safetensors')==plan['initial_checkpoint_sha256']
    audit=json.loads((data/'audit.json').read_text());manifest=json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    for f,h in audit['files'].items():assert sha(data/f)==h,f
    image_dir=W/'data/dataset/images'
    for f,h in json.loads((W/'data/dataset/image_checksums.json').read_text()).items():assert sha(image_dir/f)==h,f
    with np.load(data/'audited_samples.npz') as a:
        assert set(a.files)=={'image','task','state','action'}
        images=a['image'];tasks=a['task'];states=normalized_state(a['state']);labels=a['action']
    quartets=np.load(data/'quartets.npy')
    with np.load(data/'sampling_metadata.npz') as m:domains=m['domain'];distances=m['goal_distance']
    prim={t:np.flatnonzero((tasks==t)&(domains==1)) for t in range(2,7)}
    pools={(domain,t,near):np.flatnonzero((domains==domain)&(tasks==t)&(states[:,3]>-.2)&((distances<=.65) if near else np.ones(len(tasks),dtype=bool))) for domain in [0,1] for t in [0,1] for near in [True,False]}
    assert all(len(pool)>100 for pool in pools.values())
    seed=plan['seed'];random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed);rng=np.random.default_rng(seed)
    model=DroneVLA(checkpoint,chunk_size=plan['action_chunk'])
    prefixes=tuple(f'model.vlm_with_expert.vlm.model.text_model.layers.{l}.' for l in plan['train_vlm_text_layers'])
    vlm=[];expert=[];names=[]
    for name,p in model.policy.named_parameters():
        if name.startswith(prefixes):p.requires_grad_(True);vlm.append(p)
        elif p.requires_grad:expert.append(p)
        if p.requires_grad:names.append(name)
    assert vlm and expert
    model.policy.train()
    optimizer=torch.optim.AdamW([dict(params=expert,lr=plan['learning_rate'],base_lr=plan['learning_rate']),dict(params=vlm,lr=plan['vlm_layer_learning_rate'],base_lr=plan['vlm_layer_learning_rate'])],betas=tuple(plan['betas']),eps=plan['epsilon'],weight_decay=plan['weight_decay'])
    flatprompts=[s for row in manifest['prompt_variants'] for s in row]
    tokens=model.tokenizer(flatprompts,padding='max_length',max_length=48,truncation=True,return_tensors='pt');tokens={k:v.cuda() for k,v in tokens.items()}
    # 1.48 GB in host RAM; no model-visible scene metadata.
    rgb=np.stack([np.asarray(Image.open(image_dir/f'{i:05d}.jpg').convert('RGB')) for i in range(manifest['new_images']+manifest['retention_images'])])
    image_exposure=np.zeros(len(rgb),dtype=np.int64);task_exposure=np.zeros(7,dtype=np.int64);language_exposure=np.zeros(3,dtype=np.int64)
    out.mkdir(parents=True,exist_ok=False)
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for source in [Path(__file__),W/'scripts/build_dataset02.py',W/'scripts/register_train02.py']:
        shutil.copy2(source,snapshot/source.name)
    started=dict(started_utc=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(planfile),script_sha256=sha(Path(__file__)),dataset_audit_sha256=sha(data/'audit.json'),initial_checkpoint_sha256=plan['initial_checkpoint_sha256'],trainable_names=names,trainable_parameters=sum(p.numel() for p in expert+vlm),trained_vlm_parameters=sum(p.numel() for p in vlm),oracle_inputs=False,config=plan)
    write(out/'started.json',started);log=(out/'training.jsonl').open('x');start=time.monotonic();step=0
    try:
        for step in range(1,plan['steps']+1):
            if step%100==1 and shutil.disk_usage(W).free<5*1024**3:raise RuntimeError('Disk reserve reached; user consultation required')
            frac=min(1.,step/plan['warmup_steps']) if step<=plan['warmup_steps'] else plan['final_learning_rate_fraction']+(1-plan['final_learning_rate_fraction'])*.5*(1+math.cos(math.pi*(step-plan['warmup_steps'])/(plan['steps']-plan['warmup_steps'])))
            for g in optimizer.param_groups:g['lr']=g['base_lr']*frac
            total=0.
            for micro in range(plan['gradient_accumulation']):
                number=(step-1)*plan['gradient_accumulation']+micro
                counterfactual=micro==0 and step%2==0
                if counterfactual:indices=quartets[rng.integers(len(quartets))]
                elif micro==0:
                    indices=np.asarray([rng.choice(pools[rng.integers(2),t,True]) for t in [0,1,0,1]])
                else:
                    paired=[rng.choice(pools[rng.integers(2),t,bool(rng.random()<.8)]) for t in [0,1]]
                    indices=np.asarray([*paired,*[rng.choice(prim[2+(2*number+i)%5]) for i in range(2)]])
                variants=rng.choice(3,size=4,p=plan['prompt_probabilities'])
                # Counterparts use the same language format, preventing a prompt-format shortcut.
                if counterfactual:variants[:]=variants[0]
                else:variants[1]=variants[0]
                np.add.at(image_exposure,images[indices],1);np.add.at(task_exposure,tasks[indices],1);np.add.at(language_exposure,variants,1)
                ti=torch.as_tensor(tasks[indices]*3+variants,device='cuda',dtype=torch.long)
                batch={'observation.images.camera1':torch.from_numpy(rgb[images[indices]]).permute(0,3,1,2).float().cuda()/255,
                       'observation.state':torch.from_numpy(states[indices]).cuda(),'observation.language.tokens':tokens['input_ids'][ti],
                       'observation.language.attention_mask':tokens['attention_mask'][ti].bool(),'action':torch.from_numpy(labels[indices]).cuda()}
                noise=model.policy.model.sample_noise((4,plan['action_chunk'],32),device='cuda');ft=model.policy.model.sample_time(4,device='cuda')
                if counterfactual:noise[1:]=noise[0].clone();ft[:]=1.
                with torch.autocast('cuda',dtype=torch.bfloat16):loss,_=model.policy(batch,noise=noise,time=ft)
                if not torch.isfinite(loss):raise RuntimeError('Nonfinite loss')
                (loss/plan['gradient_accumulation']).backward();total+=float(loss.detach())/plan['gradient_accumulation']
            norm=torch.nn.utils.clip_grad_norm_(expert+vlm,plan['gradient_clip_norm'],error_if_nonfinite=True)
            if step==1:assert any(p.grad is not None and torch.count_nonzero(p.grad).item() for p in vlm)
            optimizer.step();optimizer.zero_grad(set_to_none=True)
            row=dict(step=step,loss=total,gradient_norm=float(norm),elapsed_s=time.monotonic()-start,peak_cuda_memory_bytes=torch.cuda.max_memory_allocated(),expert_lr=optimizer.param_groups[0]['lr'],vlm_lr=optimizer.param_groups[1]['lr'])
            if step==1 or step%10==0:log.write(json.dumps(row)+'\n');log.flush();write(out/'progress.json',row)
            if step==1 or step%100==0:print(json.dumps(row),flush=True)
            if step%1000==0:
                snap=dict(trainable_state={n:p.detach().cpu() for n,p in model.policy.named_parameters() if p.requires_grad},optimizer=optimizer.state_dict(),step=step,numpy_rng=rng.bit_generator.state,torch_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all(),initial_checkpoint_sha256=plan['initial_checkpoint_sha256'],image_exposure=image_exposure,task_exposure=task_exposure,language_exposure=language_exposure)
                temp=out/'recovery.pt.tmp';torch.save(snap,temp);temp.replace(out/'recovery.pt');del snap
        model.policy.save_pretrained(out/'final')
        write(out/'sampling_exposure.json',dict(total_samples=int(image_exposure.sum()),unique_new_images=int(np.count_nonzero(image_exposure[:manifest['new_images']])),unique_retention_images=int(np.count_nonzero(image_exposure[manifest['new_images']:])),image_counts=image_exposure.tolist(),task_counts=task_exposure.tolist(),language_counts=language_exposure.tolist(),language_order=['bilingual','Japanese','English'],note='No new pixels. State-augmented new and retained near-goal navigation emphasized; retained primitives and new shirt/language counterfactuals remain. See preregistered train02 plan.'))
        write(out/'result.json',dict(optimizer_steps_completed=step,elapsed_s=time.monotonic()-start,checkpoint='final',checkpoint_sha256=sha(out/'final/model.safetensors'),selection='Final step only',plan_sha256=sha(planfile),closed_loop_success_verified=False))
    except BaseException as e:
        write(out/'failure.json',dict(error=repr(e),attempted_step=step,elapsed_s=time.monotonic()-start));raise
    finally:log.close()
if __name__=='__main__':train()
