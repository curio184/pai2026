"""Record the complete failed-candidate diagnosis and bounded next hypotheses."""
import datetime,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
suite=read(W/'runs/stress_train13_en/summary.json');assert suite['completed']==suite['planned']==16
ph=read(W/'reports/stress_train13_en_phase_diagnostic.json')
geo=read(W/'reports/stress_train13_en_perception_diagnostic.json')
policy=read(W/'reports/stress_train13_en_postflight_development_diagnostic_v2.json')
fit=read(W/'reports/train13_fit_diagnostic/summary.json');assert fit['complete'] and fit['samples']==112 and fit['outputs']==224
verified=read(W/'reports/train13_en_all_records_verified.json');assert verified['evidence_consistent']
rows=[]
for r in ph['cases']:
    if r['success']:continue
    id=r['case']['id'];g=next(x for x in geo['cases'] if x['id']==id)
    p=next(x for x in policy['cases'] if x['id']==id)
    phase='hover' if 'initial_hover_3s' in r['failed_physical_components'] else r['case']['color']
    rows.append(dict(id=id,color=r['case']['color'],scene=r['case']['scene'],
        failure=r['mission_failure'],failed_checks=r['failed_checks'],failed_physical=r['failed_physical_components'],
        goal_hold_s=r['approach_hold_s'],initial_hover_s=r['explicit_hover_hold_s'],
        clearance_m=r['minimum_person_clearance_m'],closest_person=g['closest_person'],
        diagnostic_phase=phase,executed_vs_teacher=p['phases'][phase].get('actual_execution')))
sources=['protocol/train13_english.json','protocol/train13_fit_diagnostic.json',
 'runs/stress_train13_en/summary.json','reports/stress_train13_en_phase_diagnostic.json',
 'reports/stress_train13_en_perception_diagnostic.json','reports/stress_train13_en_power_diagnostic.json',
 'reports/stress_train13_en_postflight_development_diagnostic_v2.json',
 'reports/train13_fit_diagnostic/summary.json','reports/train13_fit_diagnostic/raw_outputs.jsonl',
 'figures/train13_hover_diagnosis/summary.json','reports/train13_en_all_records_verified.json',
 'reports/train13_diagnostic_reference_correction.json','reports/train13_teacher_source_completion_audit.json']
report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train13_en',
    final_checkpoint_sha256=read(W/'models/train13_en/result.json')['checkpoint_sha256'],
    development=dict(successes=8,planned=8),stress=dict(successes=9,planned=16),
    components=ph['component_counts']['v1.1'],failures=rows,
    observations=[
      'All16 trials ran;13/16 requested-person physical goal holds passed3s. Full mission passed9/16. Candidate rejected under the existing gates.',
      'H01 reached the requested goal and held6.9765s but repeatedly reacquired the target; late battery voltage decline and duty near0.95 coincided with thrust-loss/altitude loss before reporting. This is a simulation power model observation, not measured real-world endurance.',
      'H02 met the goal hold but violated minimum clearance during landing:0.395607m at89.2845s. Completion of approach does not establish safe completion of the full mission.',
      'H06 and H09 initial hover failed despite small horizontal teacher imitation errors (median executed component errors roughly0.004–0.006m/s). Physical and estimated velocities differ; teacher reproduction alone is insufficient.',
      'H11,H15,H16 failed requested-goal hold3s:2.947,2.927,0.90225s. Scores remain failures. Navigation has nonzero yaw errors and late lateral velocity errors; no unique causal attribution is established.',
      'Training-input fit check used112 preregistered inputs,224 saved outputs. One-step and10-step errors show no consistent large advantage; takeoff/landing request errors can be larger with one step. Runtime remains10 steps.',
      'Teacher13 uses current target bearing for navigation yaw, with no capture-delay/rate forecast. Scan teacher12 already uses1s yaw-rate anticipation. This discrepancy is a plausible training-label improvement, not proof of a cure.'
    ],
    next_hypotheses_not_registered_training=[
      'Keep the existing controller, detector, manager, inference steps, runtime caps, scoring, images and model inputs fixed.',
      'Consider a training-only navigation yaw target anticipating1s of current estimated angular/linear motion, retaining the same world stop goal and horizontal law.',
      'Consider a modest stationary teacher braking increase from1.2 to1.6, not an unconstrained gain increase. The delayed closed loop can oscillate; improvement must be tested, not assumed.',
      'Use a fixed-step continuation from the latest final13 weights only, with all choices preregistered before training. No intermediate checkpoint selection or final-round input use.',
      'Do not infer that image geometry generalizes from these exposed development placements. Fresh final round02 remains unexposed.'
    ],
    global_records_verified=verified['records'],scope='Completed development evidence and preregistered training-input diagnosis only. No successful final candidate or final submission artifact is claimed.',
    fresh_final_started=False,no_runtime_or_scoring_changes=True,
    source_sha256={s:sha(W/s) for s in sources})
dest=W/'reports/train13_failure_analysis.json';assert not dest.exists();dest.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(dict(report=str(dest),sha256=sha(dest),stress=report['stress'],components=report['components'],next_training_registered=False)))
