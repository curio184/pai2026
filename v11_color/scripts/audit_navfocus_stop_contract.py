"""Postflight contract audit only; never run policy, flight, or change scores."""
import hashlib
import json
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parents[1]
def read(p):
    return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    findings = []
    inputs = {}
    for failure in read(W/'reports/navfocus_failure_details.json')['failures']:
        if failure['case']['model'] != 'v1.1':
            continue
        record = W/failure['record']/'record'
        for name in ['trace.jsonl', 'events.json', 'physical_score.json']:
            path = record/name
            inputs[str(path.relative_to(W))] = sha(path)
        events = read(record/'events.json')
        event = next(e for e in events if e['event']=='vla_approach_completed')
        end = event['t']
        rows = [json.loads(line) for line in (record/'trace.jsonl').open(encoding='utf-8')]
        endpoint = min(rows, key=lambda r: abs(r['t']-end))
        score = read(record/'physical_score.json')
        goal = np.asarray(score['goal_holds'][score['profile']]['goal_scene_xy_m'])
        distance = float(np.linalg.norm(np.asarray(endpoint['truth'])[[2,1]]-goal))
        teacher_distance = float(np.linalg.norm(np.asarray(endpoint['truth'])[[2,1]]-(goal+[-.1,0.])))
        own_speed = float(np.linalg.norm(endpoint['estimated_state'][:2]))
        # Teacher14 (inherited by 15/16 for task0/1): 1.4*delta - .5*v,
        # norm limited to .2. Rotation preserves norms. Triangle inequality
        # gives a rigorous bound for a hypothetical teacher at this state.
        # This is NOT a counterfactual policy output at an earlier image time.
        teacher_lower = min(.2, max(0., 1.4*teacher_distance-.5*own_speed)) if teacher_distance>.02 else 0.
        integral = np.zeros(2); magnitude = 0.; covered = 0.
        for left, right in zip(rows, rows[1:]):
            dt = max(0., min(end, right['t'])-max(end-4., left['t']))
            if not dt:
                continue
            evidence = left.get('stop_intent_evidence')
            if not evidence or not evidence.get('valid_state'):
                continue
            command = np.asarray(evidence['intent_command'])
            integral += dt*command
            magnitude += dt*float(np.linalg.norm(command))
            covered += dt
        assert covered > 3.9, (failure['case']['id'], covered)
        findings.append(dict(case=failure['case']['id'], completion_t=end,
            goal_distance_m=distance, estimated_speed_m_s=own_speed,
            teacher_goal_distance_m=teacher_distance,
            hypothetical_teacher_first_command_norm_lower_bound_m_s=teacher_lower,
            actual_current_policy_command_norm_m_s=float(np.linalg.norm(endpoint['model_action'][:2])),
            trace_reconstruction_window_s=covered,
            norm_of_mean_intent_m_s=float(np.linalg.norm(integral)/covered),
            mean_intent_magnitude_m_s=magnitude/covered))
    for name in ['teacher_flight14.py','teacher_flight15.py','teacher_flight16.py']:
        p = W/'scripts'/name; inputs[str(p.relative_to(W))]=sha(p)
    for name in ['flight_progress.py','stop_intent.py','search_mission.py']:
        p=W/'runtime_navfocus'/name;inputs[str(p.relative_to(W))]=sha(p)
    output = dict(scope='Saved-record and source-code analysis only; no flight, inference, training or acceptance change.',
        teacher_law='For navigation, outside2cm: clip_norm(1.4*body_goal_delta - .5*estimated_body_velocity, .2). Teacher15/16 preserve this law.',
        teacher_bound='The teacher goal is person-1.0m, score goal person-.9m. At score-distance>=.25 and estimated speed<=.08, teacher-distance>=.15, raw norm>=.17; clipped norm is at least.17, above the .065 completion threshold.',
        correction='Revision2 corrects a10cm teacher/scorer goal offset omitted from revision1. Superseded report and script are preserved with _v1_superseded_coordinate_offset suffix. Original flight scores are untouched.',
        caveat='Teacher bound uses recorded completion state, not the image-capture state. It does not measure supervised error at the actual VLA input. Trace integration approximates20Hz intent updates from logged samples.',
        confirmed_contract_issue='Norm of signed mean velocity is not mean velocity magnitude. Opposing correction requests can cancel; this is not proof that the VLA issued a persistent zero request.',
        rejected_simple_fix='All six reconstructed four-second mean command magnitudes are also below .065m/s. Replacing norm(mean(command)) with mean(norm(command)) alone would not reject these completion windows. This observation is not a counterfactual flight result.',
        unresolved='These records do not prove that a new stopping rule would bring all flights into the goal tolerance. A counterfactual flight cannot be inferred from terminated traces.',
        cases=findings, source_sha256=inputs)
    for rel, digest in inputs.items():
        assert sha(W/rel)==digest
    p=W/'reports/navfocus_stop_contract_audit.json'
    p.write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps(findings,indent=2))

if __name__=='__main__':
    main()
