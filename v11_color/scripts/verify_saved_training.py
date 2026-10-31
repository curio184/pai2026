"""Independently check saved final tensors and the recorded training schedule on CPU."""
import argparse
import hashlib
import json
from pathlib import Path

import torch
from safetensors import safe_open

W = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', default='train04_en')
    args = parser.parse_args()
    root = W / 'models' / args.candidate
    start, result = read(root / 'started.json'), read(root / 'result.json')
    exposure = read(root / 'sampling_exposure.json')
    frozen = read(root / 'frozen_backbone_verification.json')
    initial = W.parent / start['config']['initial_checkpoint'] / 'model.safetensors'
    final = root / 'final/model.safetensors'
    assert sha(initial) == start['initial_checkpoint_sha256']
    assert sha(final) == result['checkpoint_sha256']
    assert result['optimizer_steps_completed'] == start['config']['steps']
    assert result['selection'] == 'Final step only'
    assert exposure['language_counts'] == [0, 0, exposure['total_samples']]
    assert exposure['total_samples'] == (result['optimizer_steps_completed']
                                         * start['config']['micro_batch']
                                         * start['config']['gradient_accumulation'])
    digest_before, digest_after = hashlib.sha256(), hashlib.sha256()
    frozen_names, changed_names, unexpected_changes = [], [], []
    trainable = set(start['trainable_names'])
    with safe_open(initial, framework='pt', device='cpu') as source, \
            safe_open(final, framework='pt', device='cpu') as target:
        assert set(source.keys()) == set(target.keys())
        for name in sorted(source.keys()):
            a, b = source.get_tensor(name), target.get_tensor(name)
            assert a.shape == b.shape and a.dtype == b.dtype
            equal = torch.equal(a, b)
            if not equal:
                changed_names.append(name)
                if name not in trainable:
                    unexpected_changes.append(name)
            if name.startswith('model.vlm_with_expert.vlm.'):
                frozen_names.append(name)
                for digest, value in [(digest_before, a), (digest_after, b)]:
                    digest.update(name.encode('utf-8'))
                    digest.update(value.contiguous().view(torch.uint8).numpy().tobytes())
    assert frozen_names and changed_names and not unexpected_changes
    assert digest_before.hexdigest() == digest_after.hexdigest()
    # SafeTensor serialization may omit tied aliases. The recorded digest uses
    # named_parameters, which likewise omits duplicate parameters.
    assert digest_before.hexdigest() == frozen['initial_parameters_sha256']
    assert digest_after.hexdigest() == frozen['final_parameters_sha256']
    proof = dict(candidate=args.candidate, passed=True, checkpoint_sha256=sha(final),
                 initial_checkpoint_sha256=sha(initial),
                 final_step=result['optimizer_steps_completed'],
                 language_counts=exposure['language_counts'],
                 frozen_tensors=len(frozen_names), changed_tensors=len(changed_names),
                 unexpected_changed_tensors=unexpected_changes,
                 frozen_parameter_sha256=digest_after.hexdigest(),
                 changed_names=changed_names,
                 scope='Saved initial and final tensor comparison on CPU; no model inference')
    output = W / 'reports' / (args.candidate + '_saved_training_verification.json')
    output.write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in proof.items() if key != 'changed_names'}))


if __name__ == '__main__':
    main()
