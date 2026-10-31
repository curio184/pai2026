"""Wait for the existing trainer, then verify saved final tensors on CPU.

Never resumes orchestration, runs inference, launches a flight or starts training.
"""
import os
os.environ['OMP_NUM_THREADS'] = '2'
os.environ['MKL_NUM_THREADS'] = '2'
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import psutil

W=Path(__file__).resolve().parents[1]
PID=23276
CREATED=1793353729.345009
DEADLINE=datetime.datetime.fromisoformat('2026-10-30T10:56:36+00:00')
STATUS=W/'reports/train16_final_save_verification_status.json'

def now():
    return datetime.datetime.now(datetime.timezone.utc)

def status(stage, **extra):
    obj=dict(updated_utc=now().isoformat(), stage=stage, existing_trainer_pid=PID,
             no_inference=True, no_flight=True, no_training_started=True, **extra)
    STATUS.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(obj),flush=True)

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not STATUS.exists()
    status('waiting_existing_training')
    while True:
        try:
            p=psutil.Process(PID)
            assert abs(p.create_time()-CREATED)<.01,'PID reused'
            alive=p.is_running()
        except psutil.NoSuchProcess:
            alive=False
        if not alive:
            break
        if now()>=DEADLINE:
            status('deadline_reached_without_final_verification')
            return
        time.sleep(10)
    model=W/'models/train16_en'
    if not (model/'result.json').exists():
        status('trainer_terminal_no_result', action='Preserve files; no restart')
        return
    plan=json.loads((W/'protocol/train16_english_implementation.json').read_text())
    for name,h in plan['scripts'].items():
        assert digest(W/'scripts'/name)==h,name
    status('verifying_saved_final_step', pinned_scripts=len(plan['scripts']))
    commands=[('verify_saved_training.py',['--candidate','train16_en']),
              ('verify_train16_final_checkpoint.py',[])]
    for script,args in commands:
        if now()>=DEADLINE:
            status('deadline_before_next_cpu_audit', pending=script)
            return
        path=str(W/'scripts'/script)
        code=('import torch,runpy,sys; torch.set_num_threads(2); '
              'torch.set_num_interop_threads(1); sys.argv='+repr([path,*args])+'; '
              'runpy.run_path('+repr(path)+',run_name="__main__")')
        log=W/'logs'/('save_only_'+script.removesuffix('.py')+'_train16.log')
        with log.open('x',encoding='utf-8') as stream:
            result=subprocess.run([sys.executable,'-B','-X','utf8','-c',code],
                                  stdout=stream,stderr=subprocess.STDOUT)
        if result.returncode:
            status('cpu_audit_failed',script=script,log=str(log),returncode=result.returncode)
            return
    audit=json.loads((W/'reports/train16_final_checkpoint_completion_audit.json').read_text())
    assert audit['passed'] and audit['optimizer_steps']==6000
    status('saved_final_step_verified',final_sha256=audit['final_sha256'],
           optimizer_steps=6000,trainable_tensors_equal=audit['trainable_tensors_equal'],
           flight_success_unverified=True,automatic_flight_pipeline_remains_suspended=True)
    checkpoint=W/'reports/current_work_checkpoint.json'
    old=json.loads(checkpoint.read_text(encoding='utf-8'))
    old.update(updated_utc=now().isoformat(),training_completed=True,
               trained_checkpoint_sha256=audit['final_sha256'],
               final_snapshot_verification='reports/train16_final_checkpoint_completion_audit.json',
               save_only_verification_status=str(STATUS),
               current_candidate_flight_success_unverified=True)
    checkpoint.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    try:
        main()
    except BaseException as exc:
        status('verification_error',error=repr(exc))
        raise
