"""Postflight diagnosis of every candidate14 development case, no model calls."""
import datetime, hashlib, json, math, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
W=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(W.parent))
from make_revision_data import rotation
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
summary=read(W/'runs/dev_train14_en/summary.json')
assert summary['completed']==summary['planned']==8
diagnostic=W/'reports/dev_train14_en_postflight_development_diagnostic.json'
diagnoses={r['id']:r for r in read(diagnostic)['cases']}
dest=W/'reports/train14_failure_analysis.json';assert not dest.exists()
figdir=W/'figures/train14_rotation_diagnosis';figdir.mkdir(exist_ok=False)
cases=[]
for outcome in summary['cases']:
    case=outcome['case'];rec=W/'runs/dev_train14_en'/(case['id']+'_'+case['model'])/'record'
    score=read(rec/'physical_score.json');diag=diagnoses[case['id']]
    row=dict(id=case['id'],success=outcome['success'],kind=case['kind'],
        goal_hold_s=diag['goal_hold_s'],initial_hover_s=diag['initial_hover_s'],
        minimum_person_clearance_m=score['minimum_person_clearance_m'],
        score_sha256=sha(rec/'physical_score.json'),trace_sha256=sha(rec/'trace.jsonl'),
        record=str(rec),rotations=score['rotations'])
    if not outcome['success']:
        allrows=[json.loads(x) for x in (rec/'trace.jsonl').read_text().splitlines()]
        row['failed_rotation_details']={}
        for phase in ['right','left']:
            rows=[r for r in allrows if r['phase']==phase and r['estimated_state'] is not None]
            if not rows or score['rotations'][phase].get('stopped'):continue
            t=np.array([r['t'] for r in rows]);truth=np.array([r['truth'] for r in rows])
            own=np.array([r['estimated_state'] for r in rows]);act=np.array([r['model_action'] for r in rows])
            speed=np.linalg.norm(truth[:,4:6],axis=1);body=np.stack([rotation(r[22:26]).T@r[26:29] for r in truth])
            tail=t>=t[-1]-2
            detail=dict(physical_final2s_speed_max_m_s=float(speed[tail].max()),
                physical_final2s_yaw_rate_abs_max_rad_s=float(np.abs(truth[tail,31]).max()),
                estimated_final2s_speed_max_m_s=float(np.linalg.norm(own[tail,:2],axis=1).max()),
                teacher_imitation=diag['phases'][phase]['actual_execution'])
            fig,axs=plt.subplots(3,1,figsize=(10,8),sharex=True,layout='constrained')
            for k,label in [(0,'Forward'),(1,'Left')]:
                axs[k].plot(t,body[:,k],label='Physical velocity')
                axs[k].plot(t,own[:,k],label='Estimated velocity',alpha=.75)
                axs[k].plot(t,act[:,k],label='Executed request',alpha=.7)
                axs[k].set_ylabel(label+' [m/s]');axs[k].legend(fontsize=8)
            axs[2].plot(t,speed,label='Physical horizontal speed')
            axs[2].axhline(.08,color='red',ls='--',label='Unchanged scoring limit')
            axs[2].set_ylabel('Speed [m/s]');axs[2].set_xlabel('Simulation time [s]');axs[2].legend(fontsize=8)
            for ax in axs:ax.axvspan(t[-1]-2,t[-1],alpha=.1,color='red');ax.grid(alpha=.2)
            fig.suptitle(case['id']+': '+phase+'; shaded interval is the final 2 seconds')
            fp=figdir/(case['id']+'_'+phase+'.png');fig.savefig(fp,dpi=130);plt.close(fig)
            detail['figure']=str(fp);detail['figure_sha256']=sha(fp)
            row['failed_rotation_details'][phase]=detail
    cases.append(row)
report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    candidate='train14_en',checkpoint_sha256=read(W/'models/train14_en/result.json')['checkpoint_sha256'],
    completed=8,successes=summary['successes'],cases=cases,
    teacher_diagnostic_sha256=sha(diagnostic),
    findings=['Both failures have excessive translation at the end of a rotation, while angular rate is below the existing limit.',
        'All four search cases and both approach primitives satisfy requested-goal stopping; all eight satisfy initial hover.',
        'Executed horizontal requests broadly imitate the strong -1.6*captured-velocity teacher; delayed feedback is a plausible contributor, not a proven sole cause.'],
    analytical_context=dict(model='Illustrative linear approximation only: dv/dt=-v-k*v(t-delay). Not a new flight or physical identification.',
        k=1.6,critical_delay_s=math.acos(-1/1.6)/math.sqrt(1.6**2-1),
        note='For 0<=k<1 this simplified delay equation is stable for every constant delay. Real attitude dynamics, estimator error and policy bias are omitted.'),
    scope='All completed development cases retained. No new policy inference, relabeling of results, controller change, or final evaluation.',
    next_hypothesis='Reduce stationary teacher braking to 0.6 while preserving navigation and all other targets; preregister separately before any learning.')
dest.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(dict(report=str(dest),sha256=sha(dest),completed=8,successes=summary['successes'])))
