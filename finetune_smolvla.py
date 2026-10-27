"""One fixed fine-tuning run of the actual SmolVLA flow-matching expert.

No oracle coordinates are loaded into model batches. The only training dataset
accepted here is the checksummed/audited artifact, with its instructions and own
state. Existing run evidence prevents accidentally starting another training run.
"""
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
from smolvla_policy import DroneVLA


def normalized_state(state):
    state=state.copy()
    state[:,:2]/=.2;state[:,2]/=.3;state[:,3]-=1
    state[:,4:6]/=.2;state[:,6]/=np.pi;state[:,7]/=.35
    return state


def train(args):
    here=Path(__file__).parent
    config=json.loads((here/"finetune_plan.json").read_text(encoding="utf-8"))
    root=args.dataset
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    audit=json.loads((root/"audit.json").read_text(encoding="utf-8"))
    file=root/"audited_samples.npz"
    if hashlib.sha256(file.read_bytes()).hexdigest()!=audit["sha256"]:raise ValueError("Dataset checksum mismatch")
    if not audit["all_tasks_present"]:raise ValueError("Missing required tasks")
    image_manifest=(root/"image_checksums.json").read_bytes()
    if hashlib.sha256(image_manifest).hexdigest()!=audit["image_manifest_sha256"]:
        raise ValueError("Image manifest checksum mismatch")
    for name,digest in json.loads(image_manifest).items():
        if hashlib.sha256((root/"images"/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f"Image checksum mismatch: {name}")
    arrays=np.load(file)
    # Explicit whitelist: teacher_position, pose, targets, and scene XML are never read into batches.
    image_ids=arrays["image"];tasks=arrays["task"];states=normalized_state(arrays["state"])
    labels=arrays["action"]
    seed=config["seed"];random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    out=here/"outputs/smolvla_training"
    out.mkdir(exist_ok=True)
    marker=out/"started.json"
    if marker.exists():raise RuntimeError("A training run already exists; no fresh run is permitted")
    model=DroneVLA()
    model.policy.train()
    params=[p for p in model.policy.parameters() if p.requires_grad]
    optimizer=torch.optim.AdamW(params,lr=config["learning_rate"],betas=tuple(config["betas"]),
                               eps=config["epsilon"],weight_decay=config["weight_decay"])
    tokens=model.tokenizer(manifest["prompts"],padding="max_length",max_length=48,truncation=True,return_tensors="pt")
    tokens={k:v.cuda() for k,v in tokens.items()}
    rng=np.random.default_rng(seed)
    plan_bytes=(here/"finetune_plan.json").read_bytes()
    record=dict(started_utc=datetime.now(timezone.utc).isoformat(),dataset_sha256=audit["sha256"],
                plan_sha256=hashlib.sha256(plan_bytes).hexdigest(),config=config,
                optimizer_steps_completed=0,oracle_runtime_input=False,
                image_manifest_sha256=audit["image_manifest_sha256"],
                model_parameters=sum(p.numel() for p in model.policy.parameters()),
                trainable_parameters=sum(p.numel() for p in params))
    with marker.open("x",encoding="utf-8") as handle:json.dump(record,handle,indent=2)
    started=time.monotonic();optimizer.zero_grad(set_to_none=True)
    log=(out/"loss.jsonl").open("x",encoding="utf-8")
    try:
        for step in range(config["steps"]):
            lr_ratio=min(1,(step+1)/config["warmup_steps"])
            if step>=config["warmup_steps"]:
                fraction=(step-config["warmup_steps"])/(config["steps"]-config["warmup_steps"])
                lr_ratio=.025+.975*.5*(1+math.cos(math.pi*fraction))
            for group in optimizer.param_groups:group["lr"]=config["learning_rate"]*lr_ratio
            total_loss=0
            for micro in range(config["gradient_accumulation"]):
                indices=rng.integers(len(tasks),size=config["micro_batch"])
                images=np.stack([np.asarray(Image.open(root/"images"/f"{image_ids[i]:05d}.jpg").convert("RGB")) for i in indices])
                task_tensor=torch.as_tensor(tasks[indices],device="cuda",dtype=torch.long)
                batch={"observation.images.camera1":torch.from_numpy(images).permute(0,3,1,2).float().cuda()/255,
                       "observation.state":torch.from_numpy(states[indices]).cuda(),
                       "observation.language.tokens":tokens["input_ids"][task_tensor],
                       "observation.language.attention_mask":tokens["attention_mask"][task_tensor].bool(),
                       "action":torch.from_numpy(labels[indices]).cuda()}
                with torch.autocast("cuda",dtype=torch.bfloat16):
                    loss,_=model.policy(batch)
                if not torch.isfinite(loss):raise RuntimeError("Nonfinite loss; preserve run, do not restart")
                (loss/config["gradient_accumulation"]).backward()
                total_loss+=float(loss.detach())/config["gradient_accumulation"]
            norm=torch.nn.utils.clip_grad_norm_(params,config["gradient_clip_norm"],error_if_nonfinite=True)
            optimizer.step();optimizer.zero_grad(set_to_none=True)
            row=dict(step=step+1,loss=total_loss,gradient_norm=float(norm),elapsed_s=time.monotonic()-started,
                     learning_rate=optimizer.param_groups[0]["lr"])
            if (step+1)%10==0 or step==0:
                log.write(json.dumps(row)+"\n");log.flush()
                (out/"progress.json").write_text(json.dumps(row,indent=2)+"\n",encoding="utf-8")
            if (step+1)%100==0 or step==0:print(json.dumps(row),flush=True)
            if (step+1)%1000==0:
                snapshot=dict(policy=model.policy.state_dict(),optimizer=optimizer.state_dict(),step=step+1,
                              numpy_rng=rng.bit_generator.state,torch_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all())
                temp=out/"recovery.pt.tmp";torch.save(snapshot,temp);temp.replace(out/"recovery.pt")
        model.policy.save_pretrained(out/"final")
        final=dict(optimizer_steps_completed=config["steps"],elapsed_s=time.monotonic()-started,
                   dataset_sha256=audit["sha256"],plan_sha256=record["plan_sha256"],
                   checkpoint="final",selection="Final step only",closed_loop_success_verified=False)
        (out/"result.json").write_text(json.dumps(final,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(final),flush=True)
    except BaseException as error:
        failure=dict(error=repr(error),elapsed_s=time.monotonic()-started,
                     last_completed_step=step if "step" in locals() else 0,
                     note="No automatic fresh run, seed change, parameter search or batch-size adjustment.")
        (out/"failure.json").write_text(json.dumps(failure,indent=2)+"\n",encoding="utf-8")
        raise
    finally:log.close()


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--dataset",type=Path,required=True);train(p.parse_args())
