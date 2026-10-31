"""Record a development hypothesis separately from frozen evaluation evidence."""
import datetime,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
source=W/'reports/heldout_train03_phase_diagnostic.json'
data=json.loads(source.read_text(encoding='utf-8'))
cases=[c for c in data['cases'] if c['case']['model']=='v1.1']
out=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    provisional=True,completed_trials=data['completed'],planned_trials=data['planned'],
    diagnostic_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    model='train03',checkpoint_sha256='22f07e7b5b72af541cca8bdb2e2b55075d3e0d9e680730b012341c6f7552c4b8',
    completed_v11=len(cases),successful_v11=sum(c['success'] for c in cases),
    per_case=[dict(id=c['case']['id'],success=c['success'],failed_checks=c['failed_checks'],
        failed_physical_components=c['failed_physical_components'],hold_s=c['approach_hold_s'],
        score_sha256=c['score_sha256'],trace_sha256=c['trace_sha256']) for c in cases],
    observations=[
        'Several cases reach and hold the requested goal but fail the separately preregistered initial-hover or post-turn physical stop checks.',
        'For H01/H05/H06/H07, hover altitude and vertical speed are inside scoring limits; horizontal drift is the limiting quantity.',
        'Estimated horizontal speed can be below 0.08 m/s while physical speed exceeds it. Mission progression uses estimated state; scoring correctly uses postflight truth.',
        'H10 reaches the requested scoring goal to 0.035 m but only holds 2.245 s under the unchanged criteria.',
        'The current non-navigation teacher asks for zero horizontal velocity, independent of the observed velocity. The frozen external converter then requests acceleration equal to desired minus estimated velocity.'
    ],
    unverified_hypothesis='Teach the VLA a state-dependent horizontal braking request, including hover and turn instructions, using onboard estimated velocity as input. A candidate coefficient of 0.8 and a captured-state correction held across an action chunk may reduce drift despite observation latency. This has not been trained, flight-tested, or shown to fix the failures. Do not infer a unique root cause from these correlations.',
    constraints=[
        'Finish every case in this final round and its preregistered static probe/known-failure replay before deciding on another training attempt.',
        'Do not change the runtime controller, gains, mission transitions, scorer, or acceptance thresholds.',
        'The current heldout layouts and seeds are now exposed. Any subsequent adapted model needs a fresh preregistered final set from the same task domain; keep this failed final round in the report.',
        'No runtime truth inputs. Any teacher change belongs to a new immutable dataset and preregistered training attempt.',
        'Use final-step weights only; preserve all earlier attempts.'
    ])
dest=W/'reports/train03_interim_diagnosis.json'
dest.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(path=str(dest),completed=data['completed'],successful_v11=out['successful_v11'],provisional=True)))
