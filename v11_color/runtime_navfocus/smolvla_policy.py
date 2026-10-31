"""Foundation VLA adapter: one real forward camera, own state, six flight actions.

This module never sends hardware packets or substitutes an oracle for the VLA.
Base-model inference checks only verify integration, not drone competence.
"""
import json
from pathlib import Path
import time

import numpy as np
from PIL import Image
import torch
from huggingface_hub import snapshot_download
from lerobot.configs.types import FeatureType, PolicyFeature
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy

REVISION="5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6"
ACTION_SCALE=np.array([.2,.2,.3,.35,1,1],dtype=np.float32)


class DroneVLA:
    def __init__(self, checkpoint=None, chunk_size=None):
        base=Path(checkpoint) if checkpoint else Path(snapshot_download("lerobot/smolvla_base",revision=REVISION))
        config=SmolVLAConfig.from_pretrained(base)
        config.device="cuda"
        config.load_vlm_weights=False  # Full policy checkpoint already contains VLM weights.
        config.input_features={"observation.state":PolicyFeature(type=FeatureType.STATE,shape=(9,)),
            "observation.images.camera1":PolicyFeature(type=FeatureType.VISUAL,shape=(3,240,320))}
        config.output_features={"action":PolicyFeature(type=FeatureType.ACTION,shape=(6,))}
        config.chunk_size=chunk_size if chunk_size is not None else config.chunk_size if checkpoint else 10
        config.n_action_steps=1
        config.empty_cameras=0
        config.push_to_hub=False
        self.policy=SmolVLAPolicy.from_pretrained(base,config=config,strict=True).to("cuda")
        self.policy.eval()
        self.tokenizer=self.policy.model.vlm_with_expert.processor.tokenizer
        # The task requests repeatable control, rather than a fresh behavior
        # sample on every camera response. Use one Gaussian seed realization,
        # preserving the flow model's documented noise interface and weights.
        self.inference_seed=20261024
        generator=torch.Generator(device="cuda").manual_seed(self.inference_seed)
        self.flow_noise=torch.randn((1,config.chunk_size,config.max_action_dim),
                                    generator=generator,device="cuda",dtype=torch.float32)

    def batch(self, rgb, instruction, state):
        rgb=np.asarray(rgb,dtype=np.uint8)
        state=np.asarray(state,dtype=np.float32).copy()
        if state.shape!=(9,) or not np.isfinite(state).all():
            raise ValueError("Expected nine finite onboard estimated state values")
        state[:2]/=.2;state[2]/=.3;state[3]-=1
        state[4:6]/=.2;state[6]/=np.pi;state[7]/=.35
        tokens=self.tokenizer([instruction],padding="max_length",max_length=48,truncation=True,return_tensors="pt")
        return {"observation.images.camera1":torch.from_numpy(rgb.copy()).permute(2,0,1).unsqueeze(0).float().cuda()/255,
                "observation.state":torch.from_numpy(state).unsqueeze(0).cuda(),
                "observation.language.tokens":tokens.input_ids.cuda(),
                "observation.language.attention_mask":tokens.attention_mask.bool().cuda()}

    @torch.inference_mode()
    def infer_chunk(self,rgb,instruction,state):
        with torch.autocast("cuda",dtype=torch.bfloat16):
            actions=self.policy.predict_action_chunk(self.batch(rgb,instruction,state),noise=self.flow_noise.clone())
        raw=actions[0,:,:6].float().cpu().numpy()
        if not np.isfinite(raw).all():raise ValueError("Nonfinite VLA output")
        # Signed velocity components and [0,1] request scores have different domains.
        result=np.clip(raw,-1,1)*ACTION_SCALE
        result[:,4:]=np.clip(raw[:,4:],0,1)
        norms=np.linalg.norm(result[:,:2],axis=1,keepdims=True)
        result[:,:2]*=np.minimum(1,.2/np.maximum(norms,1e-8))
        return result

    def infer(self,rgb,instruction,state):
        return self.infer_chunk(rgb,instruction,state)[0]


if __name__=="__main__":
    torch.manual_seed(20261024)
    model=DroneVLA()
    rgb=Image.open(Path(__file__).parent/"outputs/rescue_scene.png").convert("RGB")
    start=time.perf_counter()
    action=model.infer(rgb,"Approach the person wearing blue and stop.",[0,0,0,1,0,0,0,0,1])
    torch.cuda.synchronize()
    report=dict(base_revision=REVISION,action=action.tolist(),elapsed_s=time.perf_counter()-start,
                action_expert_structure_changed=False,training_runs=0,drone_task_success_claimed=False,
                parameters=sum(p.numel() for p in model.policy.parameters()),
                trainable_parameters=sum(p.numel() for p in model.policy.parameters() if p.requires_grad),
                note="Base-model smoke check only, no optimization step or hardware command.")
    (Path(__file__).parent/"outputs/smolvla_forward_check.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
