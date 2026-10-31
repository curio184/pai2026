"""Align saved inference packets, camera states and executed chunks postflight."""
import hashlib
import json
from pathlib import Path
import numpy as np
from teacher_flight16 import teacher_chunk

W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rotation(q):
    w,x,y,z=np.asarray(q)/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def main():
    results=[];sources={}
    for failure in read(W/'reports/navfocus_failure_details.json')['failures']:
        if failure['case']['model']!='v1.1':continue
        record=W/failure['record']/'record'
        for name in ['trace.jsonl','vla_link_events.json','events.json','physical_score.json']:
            p=record/name;sources[str(p.relative_to(W))]=sha(p)
        rows=[json.loads(l) for l in (record/'trace.jsonl').open(encoding='utf-8')]
        times=np.asarray([r['t'] for r in rows])
        events=read(record/'events.json')
        end=next(e['t'] for e in events if e['event']=='vla_approach_completed')
        score=read(record/'physical_score.json');color=score['profile']
        goal=np.asarray(score['goal_holds'][color]['goal_scene_xy_m'])
        packets={e['sim_time_capture']:e for e in read(record/'vla_link_events.json') if e['event']=='inference'}
        matched=[];teacher_cache={}
        for r in rows:
            if not (end-4<=r['t']<=end and r['phase']==color and r['action_source']=='policy'):continue
            e=packets[r['model_capture_time']];capture=e['sim_time_capture'];idx=r['chunk_index']
            if capture not in teacher_cache:
                at=rows[int(np.argmin(abs(times-capture)))];qpos=np.asarray(at['truth'][19:26])
                targets={color:np.r_[goal+[.9,0.],0.]}
                teacher=teacher_chunk(['blue','red'].index(color),qpos,e['estimated_state'],targets,rotation,np.ones(6))
                teacher_cache[capture]=(teacher,at)
                img=record/'observations'/e['image_file'];assert sha(img)==e['image_sha256']
            teacher,at=teacher_cache[capture]
            chunk=np.asarray(e['action_chunk']);selected=chunk[idx,:2].copy()
            selected=np.clip(selected,-.2,.2)
            norm=np.linalg.norm(selected)
            if norm>.2:selected*=.2/norm
            # The trace updates packet and selected command on the same control tick.
            assert np.allclose(selected,r['model_action'][:2],rtol=0,atol=1e-7)
            matched.append(dict(t=r['t'],packet_id=e['id'],image=e['image_file'],
                capture_s=capture,capture_trace_delta_s=at['t']-capture,chunk_index=idx,
                age_s=r['t']-capture,
                capture_goal_distance_m=float(np.linalg.norm(np.asarray(at['truth'])[[2,1]]-goal)),
                actual_displacement_since_capture_m=float(np.linalg.norm(np.asarray(r['truth'])[[2,1]]-np.asarray(at['truth'])[[2,1]])),
                vlm_first_norm_m_s=float(np.linalg.norm(chunk[0,:2])),
                executed_norm_m_s=float(np.linalg.norm(selected)),
                teacher_first_norm_m_s=float(np.linalg.norm(teacher[0,:2])),
                teacher_selected_norm_m_s=float(np.linalg.norm(teacher[idx,:2])),
                first_command_teacher_error_m_s=float(np.linalg.norm(chunk[0,:2]-teacher[0,:2])),
                selected_command_teacher_error_m_s=float(np.linalg.norm(chunk[idx,:2]-teacher[idx,:2]))))
        keys=['age_s','capture_goal_distance_m','actual_displacement_since_capture_m',
              'vlm_first_norm_m_s','executed_norm_m_s','teacher_first_norm_m_s',
              'teacher_selected_norm_m_s','first_command_teacher_error_m_s','selected_command_teacher_error_m_s']
        results.append(dict(case=failure['case']['id'],sample_count=len(matched),
            packet_count=len(teacher_cache),medians={k:float(np.median([r[k] for r in matched])) for k in keys},
            final_sample=matched[-1],samples=matched))
    for p in (W/'scripts').glob('teacher_flight*.py'):
        sources[str(p.relative_to(W))]=sha(p)
    p=W/'runtime_navfocus/search_link.py';sources[str(p.relative_to(W))]=sha(p)
    for name,h in sources.items():assert sha(W/name)==h
    output=dict(scope='Postflight trace/packet alignment. Recomputes teacher labels only, never policy inference or flight. Original scores and runtime unchanged.',
        correction='Revision2 reconstructs person=score_goal+[.9,0], so teacher goal is score_goal+[-.1,0]. Revision1 incorrectly assumed identical teacher/scorer goals; its report and script are preserved as superseded. Saved VLA commands and execution timings are unaffected.',
        limitations=['Sample medians are trace-sample weighted, not independent flight trials.',
                    'Teacher input position/quaternion uses nearest saved trace to capture; exact supplied estimated_state is in inference packet.',
                    'This checks source semantics and output timing; it cannot establish counterfactual success under another execution origin.'],
        cases=results,source_sha256=sources)
    (W/'reports/navfocus_chunk_timing_audit.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps([{k:r[k] for k in ['case','sample_count','packet_count','medians']} for r in results],indent=2))
if __name__=='__main__':main()
