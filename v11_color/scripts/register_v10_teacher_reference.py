"""Register a teacher-semantic compatibility check; do not alter the fixed batch."""
import ast,datetime,hashlib,json,shutil
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];P=W.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def main():
    teacher=P/'outputs/vla_data_realism_precision_02/teacher_source.py'
    text=teacher.read_text(encoding='utf-8')
    assert '@(.7*delta)' in text and 'a[:2]-=' not in text
    source=W/'runtime_rebuild03';dest=W/'runtime_rebuild03_v10ref'
    shutil.copytree(source,dest,ignore=shutil.ignore_patterns('__pycache__'))
    decoder=(source/'plan_endpoint.py').read_text(encoding='utf-8')
    decoder=decoder.replace('(a[:2]+.5*v)/1.4','a[:2]/.7')
    decoder=decoder.replace('v=np.array([[c,s],[-s,c]])@world_v','v=v  # Legacy teacher retains its simulated body-velocity components.')
    decoder=decoder.replace('The rollout matches the training action semantics;', 'The rollout matches the legacy v1.0 teacher action semantics (gain .7, no damping);')
    ast.parse(decoder);(dest/'plan_endpoint.py').write_text(decoder,encoding='utf-8')
    runner=(W/'scripts/run_suite_rebuild03_final.py').read_text(encoding='utf-8')
    runner=runner.replace('runtime_rebuild03','runtime_rebuild03_v10ref').replace('protocol/rebuild03_final.json','protocol/rebuild03_v10_reference.json')
    rp=W/'scripts/run_suite_rebuild03_v10ref.py';rp.write_text(runner,encoding='utf-8')
    original=read(W/'protocol/rebuild03_final.json')
    cases=[dict(c,group='v10_teacher_semantics_reference') for c in original['cases'] if c['model']=='v1.0']
    assert len(cases)==16
    plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=cases,
        scope='One additional v1.0 run per matched case using its own teacher velocity semantics. Not a retune of v1.1 or the ongoing42-case batch.',
        reason='The common decoder in rebuild03 is based on v1.1 gain1.4/damping.5, whereas legacy teacher has gain.7/no damping. Report both comparisons; do not attribute the common-decoder gap solely to learning.',
        selection='Decoder coefficients and rollout convention copied from the saved legacy teacher source, not fitted to reference-flight outcomes.',
        source_teacher_sha256=sha(teacher),source_teacher_relative='outputs/vla_data_realism_precision_02/teacher_source.py',
        reference_protocol_sha256=sha(W/'protocol/rebuild03_final.json'),
        checkpoint_sha256=original['old_checkpoint_sha256'],old_checkpoint_sha256=original['old_checkpoint_sha256'],
        runtime_sha256={n:sha(dest/n) for n in original['runtime_sha256']},
        score_sha256=original['score_sha256'],runner_sha256=sha(rp),flow_steps=5,
        unchanged=['Weights','All42 original outcomes retained','Same English instructions, camera, tracking gains, PI, ArduPilot, physics, starts and seeds','Physical success criteria'],
        decoder=dict(position_gain=.7,velocity_damping=0.,rollout_velocity_reorientation=False),
        execution='After the ongoing42 and static intervention complete. No concurrent GPU/WSL flight. All16 retained without retry.',
        acceptance='No success threshold for the old model. New-model completion criteria remain exactly as preregistered.',
        deadline_utc=original['deadline_utc'])
    write(W/'protocol/rebuild03_v10_reference.json',plan)
    print(json.dumps(dict(cases=16,registered=True,old_teacher_sha256=sha(teacher))))
if __name__=='__main__':main()
