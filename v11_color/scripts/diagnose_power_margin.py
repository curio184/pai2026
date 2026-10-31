"""Postflight battery/actuator and clearance evidence; thresholds are descriptive.

The frozen task score is not changed. No runtime inputs or policy calls.
"""
import argparse,datetime,json,hashlib
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--suite',required=True);a=ap.parse_args()
    root=W/'runs'/a.suite;s=read(root/'summary.json');assert s['completed']==s['planned'];out=[]
    for case in s['cases']:
        r=root/(case['case']['id']+'_'+case['case']['model'])/'record'
        if not (r/'trace.jsonl').exists():continue
        rr=[json.loads(x) for x in (r/'trace.jsonl').read_text().splitlines()]
        def item(t):
            return dict(t=t['t'],phase=t['phase'],battery_v=t['truth'][17],height_m=-t['truth'][3],
                        motor_duty=t['motor_duty'],model_action=t['model_action'])
        phases={}
        for phase in sorted(set(t['phase'] for t in rr)):
            tt=[t for t in rr if t['phase']==phase]
            phases[phase]=dict(start=item(tt[0]),end=item(tt[-1]),
                battery_min_v=min(t['truth'][17] for t in tt),
                max_motor_duty=max(max(t['motor_duty']) for t in tt))
        critical=[e for e in read(r/'events.json') if e.get('event')=='STATUSTEXT' and any(x in e['message'].get('text','').lower() for x in ['thrust loss','failsafe','position lost'])]
        land=[e for e in read(r/'events.json') if e.get('event')=='land_request']
        physical=read(r/'physical_score.json')
        out.append(dict(id=case['id'],success=case['success'],color=case['case'].get('color'),
            minimum_clearance_m=physical['minimum_person_clearance_m'],
            initial_hover_s=physical['explicit_hover_instruction_hold']['duration_s'],
            phases=phases,critical_status_events=critical,land_requests=land,
            first_motor_at_least_point94=next((item(t) for t in rr if max(t['motor_duty'])>=.94),None),
            first_battery_below3point3=next((item(t) for t in rr if t['truth'][17]<3.3),None),
            trace_sha256=sha(r/'trace.jsonl'),events_sha256=sha(r/'events.json')))
    report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),suite=a.suite,
        completed=s['completed'],planned=s['planned'],cases=out,
        scope='Saved postflight telemetry only. Voltage and duty cutoffs describe traces, not new success criteria. Battery behavior is a simulation model, not measured hardware endurance.',
        caveat='Timing correlations do not uniquely isolate the cause of a failure.')
    dest=W/'reports'/(a.suite+'_power_diagnostic.json');assert not dest.exists();dest.write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(dict(report=str(dest),cases=len(out),critical_status_cases=[x['id'] for x in out if x['critical_status_events']])))
if __name__=='__main__':main()
