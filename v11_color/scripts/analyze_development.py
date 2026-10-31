"""Postflight diagnostics only. Never feed truth into the flight process."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import numpy as np

W=Path(__file__).resolve().parents[1];P=W.parent;sys.path.insert(0,str(P))
from make_revision_data import rotation,SCALE,scene_targets

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',default='train01');a=parser.parse_args()
    config=read(W/'models'/a.candidate/'started.json')['config']
    teacher_file=W/'data/dataset/teacher_source.py'
    if config.get('teacher_standoff_m',.9)!=.9:
        teacher_file=W/'data'/('dataset'+a.candidate.removeprefix('train'))/'teacher_source.py'
    exec(compile(teacher_file.read_text(encoding='utf-8'),str(teacher_file),'exec'),globals())
    suite=W/'runs'/('dev_'+a.candidate);summary=read(suite/'summary.json');rows=[]
    for result in summary['cases']:
        case=result['case'];folder=suite/(case['id']+'_'+case['model']);record=folder/'record'
        row=dict(case=case,success=result['success'],error=result.get('error'),outcome_sha256=sha(folder/'outcome.json'))
        scorefile=record/('search_score.json' if case['kind']=='search' else 'physical_score.json')
        if not scorefile.exists():rows.append(row);continue
        score=read(scorefile);physical=score['physical'] if case['kind']=='search' else score
        row['physical']=physical
        color=case.get('color',case.get('profile'))
        if color not in ['blue','red']:rows.append(row);continue
        scene=W/'scenes'/case['scene']/'physics/rescue_scene.xml' if case['kind']=='search' else W/'scenes/primitive_regression/physics/rescue_scene.xml'
        targets=scene_targets(scene);goal=targets[color][:2]+[-.9,0]
        trace=[json.loads(line) for line in (record/'trace.jsonl').read_text().splitlines()]
        times=np.array([r['t'] for r in trace]);events=read(record/'vla_link_events.json');frames=[]
        for event in events:
            if event['event']!='inference' or not event['instruction'].startswith('Approach the person wearing '+color):continue
            r=trace[int(np.argmin(abs(times-event['sim_time_capture'])))];q=np.array(r['truth'][19:26]);state=np.array(event['estimated_state'])
            reference=teacher_chunk(['blue','red'].index(color),q,state,targets)*SCALE
            actual=np.array(event['action_chunk']);distance=float(np.linalg.norm(q[:2]-goal))
            frames.append(dict(image=event['image_file'],capture_time=event['sim_time_capture'],matched_trace_time=r['t'],goal_distance_m=distance,
                               own_horizontal_velocity=state[:2].tolist(),teacher_horizontal=reference[:, :2].tolist(),model_horizontal=actual[:,:2].tolist(),
                               mean_absolute_horizontal_error=float(np.abs(reference[:,:2]-actual[:,:2]).mean()),
                               indices_0_10_20_30=dict(teacher=reference[[0,10,20,30],:2].tolist(),model=actual[[0,10,20,30],:2].tolist())))
        row['approach_frames']=frames
        near=[r for r in frames if r['goal_distance_m']<=.5]
        row['near_goal_model_teacher_horizontal_mae']=float(np.mean([r['mean_absolute_horizontal_error'] for r in near])) if near else None
        row['navigation_state_velocity_abs_max']=np.max(np.abs([r['own_horizontal_velocity'] for r in frames]),axis=0).tolist() if frames else None
        row['phase_end_states']=[]
        for phase in read(record/'stages.json'):
            if phase['phase']!=color:continue
            r=trace[int(np.argmin(abs(times-phase['end'])))];q=r['truth'][19:26]
            row['phase_end_states'].append(dict(time=r['t'],phase=phase,position=q[:3],goal_distance_m=float(np.linalg.norm(np.asarray(q[:2])-goal)),horizontal_speed_m_s=float(np.linalg.norm(r['truth'][26:28]))))
        rows.append(row)
    report=dict(candidate=a.candidate,completed=summary['completed'],planned=summary['planned'],successes=summary['successes'],
                teacher_sha256=sha(teacher_file),teacher_standoff_m=config.get('teacher_standoff_m',.9),scoring_standoff_m=.9,
                scope='Postflight diagnostic on development cases only; no held-out images or policy evaluations',
                cause_status='Differences from teacher and training-state range are diagnostic evidence, not an isolated causal experiment.',cases=rows)
    out=W/'reports'/(a.candidate+'_development_diagnostic.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(completed=report['completed'],planned=report['planned'],successes=report['successes'],diagnostic=str(out)),ensure_ascii=False))

if __name__=='__main__':main()
