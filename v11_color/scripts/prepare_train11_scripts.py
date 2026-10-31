"""Prepare a new, separate training attempt; no training or evaluation here."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for name in ['train10_en.py','preflight_train10_loss.py','pipeline_train10_en.py','freeze_train10_implementation.py','monitor_train10.py']:
    out=W/'scripts'/name.replace('train10','train11');assert not out.exists()
    s=(W/'scripts'/name).read_text(encoding='utf8')
    s=s.replace('train10','train11').replace('Train10','Train11').replace('pipeline10_en_','pipeline11_en_')
    # Reuse the audited training data and teacher without copying or changing them.
    s=s.replace('build_dataset10_en.py','build_dataset10_en.py')
    if name=='train10_en.py':
        s=s.replace('fixed 4,000 steps','fixed 6,000 steps')
        s=s.replace("W/'scripts/build_dataset10_en.py',W/'scripts/register_train11_en.py'", "W/'scripts/build_dataset10_en.py',W/'scripts/register_train11_en.py'")
        s=s.replace("batch_types={'color_quartet':0", "noise_exposure={'runtime_fixed':0,'random':0}\n    batch_types={'color_quartet':0")
        old="if counterfactual:noise[1:]=noise[0].clone();ft[:]=1."
        new="""fixed_noise=(step+micro)%4<2
                if fixed_noise:noise[:]=model.flow_noise.expand_as(noise)
                noise_exposure['runtime_fixed' if fixed_noise else 'random']+=len(indices)
                if counterfactual:noise[1:]=noise[0].clone();ft[:]=1."""
        assert old in s;s=s.replace(old,new)
        # Preserve all existing time draws, sampler and loss. Only the noise mixture changes.
        s=s.replace("language_order=['bilingual','Japanese','English'],note=", "language_order=['bilingual','Japanese','English'],noise_exposure=noise_exposure,runtime_noise_seed=model.inference_seed,note=")
        s=s.replace('All pixels and inputs preserved. Only armed airborne rotation yaw labels use a tighter 0.03rad deadband; yaw loss weight 4. All non-yaw labels and navigation/landing labels are byte-identical to train09. No runtime changes.',
            'Same audited dataset10 images, states, labels, sampler, loss weights and flow-time schedule. Half of training microbatches use the already frozen runtime Gaussian noise realization, half fresh random noise. No runtime changes or evaluation inputs in training.')
    if name=='freeze_train10_implementation.py':
        s=s.replace("assert read(audit)['plan_sha256']==sha(plan)", "assert sha(audit)==read(plan)['training']['source_dataset_audit_sha256']\nassert read(audit)['plan_sha256']==sha(W/'protocol/train10_english.json')")
    if name=='preflight_train10_loss.py':
        s=s.replace("noise=model.policy.model.sample_noise((4,32,32),device='cuda');t=", "noise=model.flow_noise.expand(4,-1,-1).clone();assert model.inference_seed==20261024;t=")
    ast.parse(s);out.write_text(s,encoding='utf8')
print('Prepared train11 scripts; dataset10 and runtime unchanged.')
