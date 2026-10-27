"""Authorized, fixed additional SmolVLA training; preserve the original run."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import random
import time

import numpy as np
from PIL import Image
import torch

from finetune_smolvla import normalized_state
from smolvla_policy import DroneVLA


def sha(file):
    digest=hashlib.sha256()
    with file.open("rb") as handle:
        for block in iter(lambda:handle.read(4*1024*1024),b""):digest.update(block)
    return digest.hexdigest()


def train(plan_file):
    root=Path(__file__).parent;plan=json.loads(plan_file.read_text(encoding="utf-8"))
    data=root/plan["dataset"];out=root/plan["output"];checkpoint=root/plan["initial_checkpoint"]
    authorization=json.loads((root/plan["authorization"]).read_text(encoding="utf-8"))
    if not authorization["additional_training_permitted_if_needed"]:raise ValueError("Additional training not authorized")
    if out.exists():raise FileExistsError("Revision output already exists; inspect its actual process/result before any recovery")
    if sha(checkpoint/"model.safetensors")!=plan["initial_checkpoint_sha256"]:raise ValueError("Initial weights differ")
    audit=json.loads((data/"audit.json").read_text(encoding="utf-8"));manifest=json.loads((data/"manifest.json").read_text(encoding="utf-8"))
    for file,key in [("audited_samples.npz","sha256"),("image_checksums.json","image_manifest_sha256"),("nav_pairs.npy","nav_pairs_sha256")]:
        if sha(data/file)!=audit[key]:raise ValueError("Dataset audit checksum mismatch")
    if not audit["all_tasks_present"]:raise ValueError("Missing task")
    hashes=json.loads((data/"image_checksums.json").read_text(encoding="utf-8"))
    for name,value in hashes.items():
        if sha(data/"images"/name)!=value:raise ValueError("Training JPEG changed")
    with np.load(data/"audited_samples.npz") as f:
        # Geometry is explicitly not loaded from the teacher archive.
        image_ids=f["image"];tasks=f["task"];states=normalized_state(f["state"]);labels=f["action"]
    pairs=np.load(data/"nav_pairs.npy")
    if labels.shape[1:]!=(plan["action_chunk"],6):raise ValueError("Label horizon differs from plan")
    primitives={task:np.flatnonzero(tasks==task) for task in range(2,7)}
    airborne_nav={task:np.flatnonzero((tasks==task)&(states[:,3]>-.2)) for task in [0,1]}
    seed=plan["seed"];random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    model=DroneVLA(checkpoint,chunk_size=plan["action_chunk"])
    prefixes=tuple(f"model.vlm_with_expert.vlm.model.text_model.layers.{layer}." for layer in plan["train_vlm_text_layers"])
    vlm=[];expert=[];trainable_names=[]
    for name,param in model.policy.named_parameters():
        if name.startswith(prefixes):param.requires_grad_(True);vlm.append(param)
        elif param.requires_grad:expert.append(param)
        if param.requires_grad:trainable_names.append(name)
    if not vlm or not expert:raise ValueError("Trainable module selection failed")
    model.policy.train()
    optimizer=torch.optim.AdamW([dict(params=expert,lr=plan["learning_rate"],base_lr=plan["learning_rate"]),
                                 dict(params=vlm,lr=plan["vlm_layer_learning_rate"],base_lr=plan["vlm_layer_learning_rate"])],
                                betas=tuple(plan["betas"]),eps=plan["epsilon"],weight_decay=plan["weight_decay"])
    tokens=model.tokenizer(manifest["prompts"],padding="max_length",max_length=48,truncation=True,return_tensors="pt")
    tokens={name:value.cuda() for name,value in tokens.items()};rng=np.random.default_rng(seed)
    out.mkdir(parents=True,exist_ok=False)
    record=dict(started_utc=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(plan_file),dataset_sha256=audit["sha256"],
                initial_checkpoint_sha256=plan["initial_checkpoint_sha256"],authorization_sha256=sha(root/plan["authorization"]),
                image_manifest_sha256=audit["image_manifest_sha256"],config=plan,
                model_parameters=sum(p.numel() for p in model.policy.parameters()),trainable_parameters=sum(p.numel() for p in expert+vlm),
                trained_vlm_parameters=sum(p.numel() for p in vlm),trainable_names=trainable_names,
                runtime_oracle_input=False,original_run_modified=False)
    (out/"started.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    log=(out/"training.jsonl").open("x");started=time.monotonic();step=0
    try:
        for step in range(1,plan["steps"]+1):
            fraction=min(1.,step/plan["warmup_steps"]) if step<=plan["warmup_steps"] else plan["final_learning_rate_fraction"]+(1-plan["final_learning_rate_fraction"])*.5*(1+math.cos(math.pi*(step-plan["warmup_steps"])/(plan["steps"]-plan["warmup_steps"])))
            for group in optimizer.param_groups:group["lr"]=group["base_lr"]*fraction
            total=0.
            for micro in range(plan["gradient_accumulation"]):
                number=(step-1)*plan["gradient_accumulation"]+micro
                paired=pairs[rng.integers(len(pairs))] if number%2==0 else [rng.choice(airborne_nav[task]) for task in [0,1]]
                extras=[rng.choice(primitives[2+(2*number+i)%5]) for i in range(2)]
                indices=np.asarray([*paired,*extras],dtype=np.int64)
                images=np.stack([np.asarray(Image.open(data/"images"/f"{image_ids[i]:05d}.jpg").convert("RGB")) for i in indices])
                task=torch.as_tensor(tasks[indices],device="cuda",dtype=torch.long)
                batch={"observation.images.camera1":torch.from_numpy(images).permute(0,3,1,2).float().cuda()/255,
                       "observation.state":torch.from_numpy(states[indices]).cuda(),
                       "observation.language.tokens":tokens["input_ids"][task],
                       "observation.language.attention_mask":tokens["attention_mask"][task].bool(),
                       "action":torch.from_numpy(labels[indices]).cuda()}
                noise=model.policy.model.sample_noise((4,plan["action_chunk"],32),device="cuda")
                flow_time=model.policy.model.sample_time(4,device="cuda")
                if number%2==0:noise[1]=noise[0];flow_time[:2]=1.
                with torch.autocast("cuda",dtype=torch.bfloat16):loss,_=model.policy(batch,noise=noise,time=flow_time)
                if not torch.isfinite(loss):raise RuntimeError("Nonfinite loss")
                (loss/plan["gradient_accumulation"]).backward();total+=float(loss.detach())/plan["gradient_accumulation"]
            norm=torch.nn.utils.clip_grad_norm_(expert+vlm,plan["gradient_clip_norm"],error_if_nonfinite=True)
            if step==1 and not any(p.grad is not None and torch.count_nonzero(p.grad).item() for p in vlm):raise RuntimeError("No VLM-layer gradient")
            optimizer.step();optimizer.zero_grad(set_to_none=True)
            row=dict(step=step,loss=total,gradient_norm=float(norm),elapsed_s=time.monotonic()-started,
                     expert_learning_rate=optimizer.param_groups[0]["lr"],vlm_learning_rate=optimizer.param_groups[1]["lr"],
                     peak_cuda_memory_bytes=torch.cuda.max_memory_allocated())
            if step%10==0 or step==1:
                log.write(json.dumps(row)+"\n");log.flush();(out/"progress.json").write_text(json.dumps(row,indent=2)+"\n",encoding="utf-8")
            if step%100==0 or step==1:print(json.dumps(row),flush=True)
            if step%1000==0:
                trainable={name:param.detach().cpu() for name,param in model.policy.named_parameters() if param.requires_grad}
                snapshot=dict(trainable_state=trainable,optimizer=optimizer.state_dict(),step=step,numpy_rng=rng.bit_generator.state,
                              torch_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all(),initial_checkpoint_sha256=plan["initial_checkpoint_sha256"])
                temporary=out/"recovery.pt.tmp";torch.save(snapshot,temporary);temporary.replace(out/"recovery.pt")
                del snapshot,trainable
        model.policy.save_pretrained(out/"final")
        result=dict(optimizer_steps_completed=plan["steps"],elapsed_s=time.monotonic()-started,dataset_sha256=audit["sha256"],
                    plan_sha256=record["plan_sha256"],checkpoint="final",selection="Final step only",closed_loop_success_verified=False)
        (out/"result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result),flush=True)
    except BaseException as error:
        (out/"failure.json").write_text(json.dumps(dict(error=repr(error),attempted_step=step,elapsed_s=time.monotonic()-started),indent=2)+"\n",encoding="utf-8")
        raise
    finally:log.close()


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--plan",type=Path,default=Path(__file__).parent/"finetune_plan_revision_02.json")
    train(p.parse_args().plan)
