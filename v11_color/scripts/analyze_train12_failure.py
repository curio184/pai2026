"""Summarize the complete development suite before registering another recipe."""
import datetime,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
suite=read(W/'runs/dev_train12_en/summary.json'); assert suite['completed']==suite['planned']==8
diagfile=W/'reports/dev_train12_en_postflight_development_diagnostic.json'; diag=read(diagfile)
rotationfile=W/'reports/train12_dev01_blue_rotation_development_diagnostic.json'
geometryfile=W/'reports/navigation_training_geometry_audit.json'
failed=[r for r in diag['cases'] if not r['success']]; assert len(failed)==1 and failed[0]['id']=='dev01_blue'
case=failed[0]; rec=W/'runs/dev_train12_en/dev01_blue_v1.1/record'
events=read(rec/'vla_link_events.json')
images=[e['image_file'] for e in events if e.get('event')=='inference' and 50.89<=e['sim_time_capture']<=53.83]
result=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='train12_en',
    development=dict(completed=8,successes=suite['successes'],failures=['dev01_blue']),
    evidence=dict(full_diagnostic_sha256=sha(diagfile),rotation_comparison_sha256=sha(rotationfile),training_geometry_audit_sha256=sha(geometryfile)),
    failure=dict(id='dev01_blue',reason=case['failure'],goal_hold_s=case['goal_hold_s'],initial_hover_s=case['initial_hover_s'],
        minimum_person_clearance_m=case['minimum_person_clearance_m'],navigation_images=images,
        navigation_prediction_first10_median=case['phases']['blue']['predicted_first10_median'],
        navigation_teacher_first10_median=case['phases']['blue']['teacher_first10_median']),
    observations=[
        'All four primitive cases and three of four search cases passed the unchanged scoring.',
        'The failed blue case discovered the target at the right image edge; after approach began the target left the field of view and reacquisition timed out.',
        'The postflight comparison shows the failed case ended its scan around 84 degrees of relative yaw, with the blue person bearing about -34 degrees; at approach start the bearing was about -37 degrees.',
        'The complete existing navigation training labels contain zero yaw commands, including off-center target views. 3270 of 9432 unique airborne image/instruction pairs have absolute target bearing above25 degrees.',
        'During the short blue approach the predicted translation is more forward and less right than the reconstructed teacher. These errors and prior drift also contribute; a single cause has not been isolated.'
    ],
    hypothesis='Teach navigation yaw to center the requested person while preserving the same world stop goal and translation law. This may prevent edge loss; it is not yet a measured policy improvement.',
    scope='Full development suite and training-only metadata; no new policy inference or final-test exposure.',
    truth_usage='Postflight geometry analysis only; no runtime truth inputs.',
    preserved='All8 development cases and all earlier trials/weights remain available.')
out=W/'reports/train12_failure_analysis.json'; assert not out.exists();out.write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(dict(report=str(out),sha256=sha(out),development_successes=suite['successes'],completed=8)))
