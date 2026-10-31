"""Train11 English: fixed 6,000 steps, no evaluation-based checkpoint selection."""
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
def frozen_vlm_digest(policy):
    digest=hashlib.sha256()
    for name,p in sorted(policy.named_parameters()):
        if name.startswith('model.vlm_with_expert.vlm.'):
            assert not p.requires_grad
            digest.update(name.encode('utf-8'));digest.update(p.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()
def weighted_loss(policy,batch,noise,t,weights):
    # Training-only loss weighting. No action encoding or runtime path is modified.
    assert not policy.config.adapt_to_pi_aloha and 'action_is_pad' not in batch
    assert policy.config.action_feature.shape[0]==6
    images,masks=policy.prepare_images(batch)
    losses=policy.model.forward(images,masks,batch['observation.language.tokens'],batch['observation.language.attention_mask'],policy.prepare_state(batch),policy.prepare_action(batch),noise,t)[:,:,:6]
    weights=torch.as_tensor(weights,device=losses.device,dtype=losses.dtype)
    return ((losses*weights).sum(-1)/weights.sum()).mean()

def train():
    planfile=W/'protocol/train11_english.json';full=json.loads(planfile.read_text(encoding='utf-8'));plan=full['training']
    implementation=json.loads((W/'protocol/train11_english_implementation.json').read_text());assert sha(planfile)==implementation['plan_sha256'];assert sha(Path(__file__))==implementation['trainer_sha256']
    data=W/'data/dataset10_en';out=W/plan['output'];checkpoint=P/plan['initial_checkpoint']
    assert not out.exists(),'Never overwrite a training attempt'
    assert sha(checkpoint/'model.safetensors')==plan['initial_checkpoint_sha256']
    audit=json.loads((data/'audit.json').read_text());manifest=json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    for f,h in audit['files'].items():assert sha(data/f)==h,f
    assert shutil.disk_usage(W).free>=plan['minimum_free_gib_before_training']*1024**3,'Insufficient free space; do not move existing data without approval'
    sources=json.loads((data/'image_sources.json').read_text(encoding='utf8'))
    for row in sources:assert sha(W/row['path'])==row['sha256'],row['id']
    with np.load(data/'audited_samples.npz') as a:
        assert set(a.files)=={'image','task','state','action'}
        images=a['image'];tasks=a['task'];states=normalized_state(a['state']);labels=a['action']
    quartets=np.load(data/'quartets.npy')
    with np.load(data/'sampling_metadata.npz') as m:domains=m['domain'];distances=m['goal_distance']
    state_quartets=np.load(data/'state_quartets.npy')
    image_domains=np.asarray([r['domain'] for r in sources],dtype=np.int8)
    quartet_domains=domains[quartets[:,0]]
    quartet_pools={d:np.flatnonzero(quartet_domains==d) for d in [0,2]}
    pair_pools={(d,t):np.flatnonzero((domains[state_quartets[:,0]]==d)&(tasks[state_quartets[:,0]]==t)) for d in range(3) for t in range(2,7)}
    original=np.arange(len(tasks))<manifest['original_sample_count']
    raw_armed=states[:,8]>.5
    prim={(d,t):np.flatnonzero(original&(domains==d)&(tasks==t)) for d in [0,1] for t in range(2,7)}
    takeoff={(d,ground):np.flatnonzero(original&(domains==d)&(tasks==2)&((~raw_armed) if ground else raw_armed)) for d in [0,1] for ground in [True,False]}
    pools={(d,t):np.flatnonzero((domains==d)&(tasks==t)&(states[:,3]>-.2)&((distances<=.65) if d<2 else True)) for d in range(3) for t in [0,1]}
    assert all(len(x) for x in [*quartet_pools.values(),*pair_pools.values(),*prim.values(),*takeoff.values(),*pools.values()])
    seed=plan['seed'];random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed);rng=np.random.default_rng(seed)
    model=DroneVLA(checkpoint,chunk_size=plan['action_chunk'])
    assert model.inference_seed==plan['runtime_noise_seed']==20261024
    assert plan['train_vlm_text_layers']==[]
    vlm=[];expert=[];names=[]
    for name,p in model.policy.named_parameters():
        if name.startswith('model.vlm_with_expert.vlm.'):p.requires_grad_(False)
        elif p.requires_grad:expert.append(p)
        if p.requires_grad:names.append(name)
    assert not vlm and expert
    frozen_digest=frozen_vlm_digest(model.policy)
    model.policy.train();model.policy.model.vlm_with_expert.vlm.eval()
    optimizer=torch.optim.AdamW([dict(params=expert,lr=plan['learning_rate'],base_lr=plan['learning_rate'])],betas=tuple(plan['betas']),eps=plan['epsilon'],weight_decay=plan['weight_decay'])
    flatprompts=[s for row in manifest['prompt_variants'] for s in row]
    tokens=model.tokenizer(flatprompts,padding='max_length',max_length=48,truncation=True,return_tensors='pt');tokens={k:v.cuda() for k,v in tokens.items()}
    # RGB host memory only; no model-visible scene metadata.
    rgb=np.stack([np.asarray(Image.open(W/r['path']).convert('RGB')) for r in sources])
    image_exposure=np.zeros(len(rgb),dtype=np.int64);task_exposure=np.zeros(7,dtype=np.int64);language_exposure=np.zeros(3,dtype=np.int64)
    out.mkdir(parents=True,exist_ok=False)
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for source in [Path(__file__),W/'scripts/build_dataset10_en.py',W/'scripts/register_train11_en.py',W/'scripts/teacher_flight10.py',W/'scripts/teacher_flight09.py',W/'scripts/teacher_flight08.py',W/'protocol/storage_migration_e.json']:
        shutil.copy2(source,snapshot/source.name)
    started=dict(started_utc=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(planfile),script_sha256=sha(Path(__file__)),dataset_audit_sha256=sha(data/'audit.json'),initial_checkpoint_sha256=plan['initial_checkpoint_sha256'],trainable_names=names,trainable_parameters=sum(p.numel() for p in expert+vlm),trained_vlm_parameters=sum(p.numel() for p in vlm),oracle_inputs=False,config=plan)
    started['frozen_vlm_parameters_sha256']=frozen_digest
    write(out/'started.json',started);log=(out/'training.jsonl').open('x');start=time.monotonic();step=0
    noise_exposure={'runtime_fixed':0,'random':0}
    batch_types={'color_quartet':0,'navigation':0,'state_calibration':0,'retained_primitive':0}
    try:
        for step in range(1,plan['steps']+1):
            if step%100==1 and shutil.disk_usage(W).free<plan['minimum_free_gib_during_training']*1024**3:raise RuntimeError('Disk reserve reached; user consultation required')
            frac=min(1.,step/plan['warmup_steps']) if step<=plan['warmup_steps'] else plan['final_learning_rate_fraction']+(1-plan['final_learning_rate_fraction'])*.5*(1+math.cos(math.pi*(step-plan['warmup_steps'])/(plan['steps']-plan['warmup_steps'])))
            for g in optimizer.param_groups:g['lr']=g['base_lr']*frac
            total=0.
            for micro in range(plan['gradient_accumulation']):
                counterfactual=micro==0 and step%2==0
                velocity_pair=micro==1 and step%5!=0
                if counterfactual:
                    domain=2 if rng.random()<.5 else 0
                    indices=quartets[rng.choice(quartet_pools[domain])];kind='color_quartet'
                elif micro==0:
                    chosen=[]
                    for t in [0,1,0,1]:
                        domain=int(rng.integers(2)) if rng.random()<.7 else 2
                        chosen.append(rng.choice(pools[domain,t]))
                    indices=np.asarray(chosen);kind='navigation'
                elif velocity_pair:
                    t=2+((step-1)-(step-1)//5)%5
                    domain=int(rng.choice(3,p=[.25,.25,.5]))
                    indices=state_quartets[rng.choice(pair_pools[domain,t])];kind='state_calibration'
                else:
                    chosen=[]
                    for t in [2,3,4+((step//5)%2),6]:
                        domain=int(rng.integers(2))
                        pool=takeoff[domain,bool(rng.random()<.5)] if t==2 else prim[domain,t]
                        chosen.append(rng.choice(pool))
                    indices=np.asarray(chosen);kind='retained_primitive'
                batch_types[kind]+=4
                variants=np.full(4,2,dtype=np.int64)
                np.add.at(image_exposure,images[indices],1);np.add.at(task_exposure,tasks[indices],1);np.add.at(language_exposure,variants,1)
                ti=torch.as_tensor(tasks[indices]*3+variants,device='cuda',dtype=torch.long)
                batch={'observation.images.camera1':torch.from_numpy(rgb[images[indices]]).permute(0,3,1,2).float().cuda()/255,
                       'observation.state':torch.from_numpy(states[indices]).cuda(),'observation.language.tokens':tokens['input_ids'][ti],
                       'observation.language.attention_mask':tokens['attention_mask'][ti].bool(),'action':torch.from_numpy(labels[indices]).cuda()}
                noise=model.policy.model.sample_noise((4,plan['action_chunk'],32),device='cuda');ft=model.policy.model.sample_time(4,device='cuda')
                fixed_noise=(step+micro)%4<2
                if fixed_noise:noise[:]=model.flow_noise.expand_as(noise)
                noise_exposure['runtime_fixed' if fixed_noise else 'random']+=len(indices)
                if counterfactual:noise[1:]=noise[0].clone();ft[:]=1.
                if velocity_pair:
                    noise[1:]=noise[0].clone()
                    if step%2==0:ft[:]=1.
                    else:ft[:]=ft[0].clone()
                if step==1 and micro==0:
                    model.policy.eval()
                    with torch.no_grad(),torch.autocast('cuda',dtype=torch.bfloat16):
                        reference,_=model.policy(batch,noise=noise,time=ft)
                        equivalent=weighted_loss(model.policy,batch,noise,ft,[1.]*6)
                    assert torch.allclose(reference.float(),equivalent.float(),rtol=1e-5,atol=1e-6)
                    write(out/'loss_implementation_preflight.json',dict(library_uniform_loss=float(reference),local_uniform_loss=float(equivalent),allclose=True,updates_before_check=0,inputs='Training batch only',registered_weights=plan['action_loss_weights']))
                    model.policy.train();model.policy.model.vlm_with_expert.vlm.eval()
                with torch.autocast('cuda',dtype=torch.bfloat16):loss=weighted_loss(model.policy,batch,noise,ft,plan['action_loss_weights'])
                if not torch.isfinite(loss):raise RuntimeError('Nonfinite loss')
                (loss/plan['gradient_accumulation']).backward();total+=float(loss.detach())/plan['gradient_accumulation']
            norm=torch.nn.utils.clip_grad_norm_(expert+vlm,plan['gradient_clip_norm'],error_if_nonfinite=True)
            if step==1:assert any(p.grad is not None and torch.count_nonzero(p.grad).item() for p in expert)
            optimizer.step();optimizer.zero_grad(set_to_none=True)
            row=dict(step=step,loss=total,gradient_norm=float(norm),elapsed_s=time.monotonic()-start,peak_cuda_memory_bytes=torch.cuda.max_memory_allocated(),expert_lr=optimizer.param_groups[0]['lr'],vlm_lr=0.0)
            if step==1 or step%10==0:log.write(json.dumps(row)+'\n');log.flush();write(out/'progress.json',row)
            if step==1 or step%100==0:print(json.dumps(row),flush=True)
            if step%1000==0:
                snap=dict(trainable_state={n:p.detach().cpu() for n,p in model.policy.named_parameters() if p.requires_grad},optimizer=optimizer.state_dict(),step=step,numpy_rng=rng.bit_generator.state,torch_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all(),initial_checkpoint_sha256=plan['initial_checkpoint_sha256'],image_exposure=image_exposure,task_exposure=task_exposure,language_exposure=language_exposure)
                temp=out/'recovery.pt.tmp';torch.save(snap,temp);temp.replace(out/'recovery.pt');del snap
        assert noise_exposure=={'runtime_fixed':24000,'random':24000}
        final_frozen_digest=frozen_vlm_digest(model.policy);assert final_frozen_digest==frozen_digest
        model.policy.save_pretrained(out/'final')
        write(out/'frozen_backbone_verification.json',dict(initial_parameters_sha256=frozen_digest,final_parameters_sha256=final_frozen_digest,equal=True,scope='All parameters below model.vlm_with_expert.vlm; expert and state/action projections were trained'))
        write(out/'sampling_exposure.json',dict(total_samples=int(image_exposure.sum()),unique_new_images=int(np.count_nonzero(image_exposure[image_domains!=1])),unique_retention_images=int(np.count_nonzero(image_exposure[image_domains==1])),domain_exposures=[int(image_exposure[image_domains==d].sum()) for d in range(3)],batch_type_counts=batch_types,image_counts=image_exposure.tolist(),task_counts=task_exposure.tolist(),language_counts=language_exposure.tolist(),language_order=['bilingual','Japanese','English'],noise_exposure=noise_exposure,runtime_noise_seed=model.inference_seed,note='Same audited dataset10 images, states, labels, sampler, loss weights and flow-time schedule. Half of training microbatches use the already frozen runtime Gaussian noise realization, half fresh random noise. No runtime changes or evaluation inputs in training. Vision-language backbone frozen. See preregistered train11 plan.'))
        write(out/'result.json',dict(optimizer_steps_completed=step,elapsed_s=time.monotonic()-start,checkpoint='final',checkpoint_sha256=sha(out/'final/model.safetensors'),selection='Final step only',plan_sha256=sha(planfile),closed_loop_success_verified=False))
    except BaseException as e:
        write(out/'failure.json',dict(error=repr(e),attempted_step=step,elapsed_s=time.monotonic()-start));raise
    finally:log.close()
if __name__=='__main__':train()

