"""Plot all initial-hover failures; saved telemetry only, no new flight."""
import json,hashlib,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W.parent))
from make_revision_data import rotation
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
diag=read(W/'reports/stress_train13_en_phase_diagnostic.json');assert diag['completed']==16
selected=[r for r in diag['cases'] if 'initial_hover_3s' in r['failed_physical_components']]
out=W/'figures/train13_hover_diagnosis';assert not out.exists();out.mkdir(parents=True)
stats=[]
for case in selected:
    id=case['case']['id'];rec=W/'runs/stress_train13_en'/(id+'_v1.1')/'record'
    allrows=[json.loads(line) for line in (rec/'trace.jsonl').read_text().splitlines()]
    rows=[r for r in allrows if r['phase']=='hover' and r['estimated_state'] is not None]
    t=np.array([r['t'] for r in rows]);own=np.array([r['estimated_state'] for r in rows]);action=np.array([r['model_action'] for r in rows])
    truth=np.array([r['truth'] for r in rows]);body=np.stack([rotation(r[22:26]).T@r[26:29] for r in truth])
    speed=np.linalg.norm(truth[:,4:6],axis=1)
    fig,axes=plt.subplots(3,1,figsize=(11,8),sharex=True,layout='constrained')
    for dim,label in [(0,'Forward'),(1,'Left')]:
        ax=axes[dim];ax.plot(t,body[:,dim],label='Physical velocity',color='#156f86')
        ax.plot(t,own[:,dim],label='Estimated velocity',color='#d88c31')
        ax.plot(t,action[:,dim],label='Executed velocity request',color='#7853aa',alpha=.7)
        ax.axhline(0,color='gray',lw=.6);ax.set_ylabel(label+' [m/s]');ax.grid(alpha=.2);ax.legend(loc='upper right',fontsize=8)
    ax=axes[2];ax.plot(t,speed,label='Physical horizontal speed',color='#156f86')
    ax.plot(t,np.linalg.norm(own[:,:2],axis=1),label='Estimated horizontal speed',color='#d88c31')
    ax.axhline(.08,color='#b33737',ls='--',label='Frozen limit: 0.08 m/s');ax.fill_between(t,0,.08,where=speed<=.08,color='#156f86',alpha=.12)
    ax.set_ylabel('Speed [m/s]');ax.set_xlabel('Simulation time [s]');ax.grid(alpha=.2);ax.legend(loc='upper right',fontsize=8)
    fig.suptitle(f'{id}: initial hover, physical valid hold {case["explicit_hover_hold_s"]:.3f}s (required 3s)')
    dest=out/(id+'.png');fig.savefig(dest,dpi=150);plt.close(fig)
    stats.append(dict(id=id,physical_hold_s=case['explicit_hover_hold_s'],
        median_body_velocity_m_s=np.median(body[:,:2],axis=0).tolist(),median_estimated_velocity_m_s=np.median(own[:,:2],axis=0).tolist(),
        median_estimate_minus_physical_m_s=np.median(own[:,:2]-body[:,:2],axis=0).tolist(),
        median_requested_velocity_m_s=np.median(action[:,:2],axis=0).tolist(),
        trace_sha256=sha(rec/'trace.jsonl'),figure_sha256=sha(dest)))
report=dict(cases=stats,selection='All initial-hover failures in the completed16-case suite',
    scope='Postflight physical telemetry compared with estimated state and executed requests. Body velocity uses saved quaternion and world velocity. This does not identify a unique cause or alter any scoring.')
(out/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
