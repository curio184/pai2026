"""Prepare an exact-state training resume after a verified save/rename failure."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
src=W/'scripts/train13_en.py';out=W/'scripts/train13_resume01.py';assert not out.exists()
s=src.read_text(encoding='utf8')
s=s.replace('"""Train13 English: fixed 6,000 steps, no evaluation-based checkpoint selection."""','"""Resume train13 at step2000 after a save rename error; final step remains6000."""')
s=s.replace("assert sha(Path(__file__))==implementation['trainer_sha256']", "assert sha(W/'scripts/train13_en.py')==implementation['trainer_sha256']\n    amendment_file=W/'protocol/train13_resume01.json';amendment=json.loads(amendment_file.read_text())\n    assert sha(Path(__file__))==amendment['resume_trainer_sha256']\n    for name,h in implementation['scripts'].items():assert sha(W/'scripts'/name)==h,name")
s=s.replace("assert not out.exists(),'Never overwrite a training attempt'", "assert out.exists() and not (out/'final').exists() and not (out/'result.json').exists()\n    assert not (out/'resume01_started.json').exists()\n    recovery=out/amendment['recovery_file'];assert sha(recovery)==amendment['recovery_sha256']")
s=s.replace("out.mkdir(parents=True,exist_ok=False)\n    snapshot=out/'source_snapshot';snapshot.mkdir()", "snapshot=out/'resume01_source_snapshot';snapshot.mkdir(exist_ok=False)")
s=s.replace("W/'protocol/storage_migration_e.json']", "W/'protocol/storage_migration_e.json',amendment_file]")
s=s.replace("write(out/'started.json',started);log=(out/'training.jsonl').open('x');start=time.monotonic();step=0\n    noise_exposure={'runtime_fixed':0,'random':0}\n    batch_types={'color_quartet':0,'navigation':0,'state_calibration':0,'retained_primitive':0}", """original_started=json.loads((out/'started.json').read_text())
    assert original_started['frozen_vlm_parameters_sha256']==frozen_digest
    assert original_started['trainable_names']==names
    snap=torch.load(recovery,map_location='cpu',weights_only=False)
    step=int(snap['step']);assert step==amendment['resume_step']==2000
    assert snap['initial_checkpoint_sha256']==plan['initial_checkpoint_sha256']
    assert set(snap['trainable_state'])==set(names)
    with torch.no_grad():
        for name,p in model.policy.named_parameters():
            if name in snap['trainable_state']:
                t=snap['trainable_state'][name];assert t.shape==p.shape and t.dtype==p.dtype and torch.isfinite(t).all()
                p.copy_(t.to(p.device));assert torch.equal(p.detach().cpu(),t)
    for value in snap['optimizer']['state'].values():
        assert int(value['step'].item())==step
        assert all(torch.isfinite(v).all() for v in value.values() if torch.is_tensor(v))
    optimizer.load_state_dict(snap['optimizer'])
    optimizer.zero_grad(set_to_none=True)
    image_exposure=snap['image_exposure'].copy();task_exposure=snap['task_exposure'].copy();language_exposure=snap['language_exposure'].copy()
    assert image_exposure.sum()==task_exposure.sum()==language_exposure.sum()==step*8
    noise_exposure={'runtime_fixed':0,'random':0}
    batch_types={'color_quartet':0,'navigation':0,'state_calibration':0,'retained_primitive':0}
    for completed_step in range(1,step+1):
        for micro in range(2):
            noise_exposure['runtime_fixed' if (completed_step+micro)%4<2 else 'random']+=4
            kind=('color_quartet' if completed_step%2==0 else 'navigation') if micro==0 else ('state_calibration' if completed_step%5!=0 else 'retained_primitive')
            batch_types[kind]+=4
    assert sum(noise_exposure.values())==sum(batch_types.values())==step*8
    rng.bit_generator.state=snap['numpy_rng']
    torch.set_rng_state(snap['torch_rng']);torch.cuda.set_rng_state_all(snap['cuda_rng'])
    assert torch.equal(torch.get_rng_state(),snap['torch_rng'])
    assert all(torch.equal(a,b) for a,b in zip(torch.cuda.get_rng_state_all(),snap['cuda_rng']))
    started.update(resume_amendment_sha256=sha(amendment_file),resume_step=step,recovery_sha256=sha(recovery),
        original_started_sha256=sha(out/'started.json'),restored_trainable_parameters_exactly=True,
        optimizer_restored=True,numpy_cpu_cuda_rng_restored=True,restored_noise_exposure=noise_exposure.copy(),restored_batch_types=batch_types.copy())
    write(out/'resume01_started.json',started)
    del snap
    elapsed_before=json.loads((out/'failure.json').read_text())['elapsed_s']
    log=(out/'training_resume01.jsonl').open('x');start=time.monotonic()-elapsed_before
    print(json.dumps(dict(event='resume_state_restored',step=step,final_step=plan['steps'],optimizer_restored=True,rng_restored=True)),flush=True)""")
s=s.replace("for step in range(1,plan['steps']+1):", "for step in range(step+1,plan['steps']+1):")
s=s.replace("temp=out/'recovery.pt.tmp';torch.save(snap,temp);temp.replace(out/'recovery.pt');del snap", "recovery_out=out/f'recovery_resume01_step{step:05d}.pt';assert not recovery_out.exists();torch.save(snap,recovery_out);del snap\n                write(out/f'recovery_resume01_step{step:05d}.json',dict(step=step,sha256=sha(recovery_out),complete=True,selection='Recovery only; never evaluated'))")
s=s.replace("closed_loop_success_verified=False))", "closed_loop_success_verified=False,resumed=True,resume_step=amendment['resume_step'],resume_amendment_sha256=sha(amendment_file),training_logs=['training.jsonl','training_resume01.jsonl']))")
s=s.replace("write(out/'failure.json',dict", "write(out/'failure_resume01.json',dict")
assert "log=(out/'training_resume01.jsonl').open('x')" in s
assert 'temp.replace' not in s
assert "write(out/'started.json'" not in s
ast.parse(s);out.write_text(s,encoding='utf8')
print('Prepared a separate resume trainer; original scripts and records unchanged.')
