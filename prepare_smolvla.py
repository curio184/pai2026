"""Download the pinned foundation VLA and verify its configuration; no training."""
import hashlib
import importlib.metadata
import json
from pathlib import Path

from huggingface_hub import snapshot_download
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
import torch

REVISION = "5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6"


def main():
    base = Path(snapshot_download("lerobot/smolvla_base", revision=REVISION))
    config = SmolVLAConfig.from_pretrained(base)
    hashes = {}
    for file in base.glob("*.safetensors"):
        digest = hashlib.sha256()
        with file.open("rb") as handle:
            for block in iter(lambda: handle.read(4*1024*1024), b""):
                digest.update(block)
        hashes[file.name] = digest.hexdigest()
    result = dict(model="lerobot/smolvla_base", revision=REVISION, local_cache=str(base),
                  weights_sha256=hashes, config_type=config.type,
                  cuda_available=torch.cuda.is_available(),
                  device=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
                  versions={p:importlib.metadata.version(p) for p in
                            ["lerobot","torch","torchvision","transformers","huggingface-hub"]},
                  training_runs=0, inference_verified=False,
                  note="Downloaded weights and parsed config only; no learned drone capability claimed.")
    output = Path(__file__).parent/"outputs/smolvla_setup.json"
    output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
