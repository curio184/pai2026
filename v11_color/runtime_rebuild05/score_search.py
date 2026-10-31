"""Offline audit; simulator target positions are used only here, after flight."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import math
import xml.etree.ElementTree as ET
import numpy as np
sys.path.insert(0,os.environ['RESCUE_PROJECT_ROOT'])
from score_mission import score

def audit(record,scene):
    base=json.loads((record/'physical_score.json').read_text()) if (record/'physical_score.json').exists() else score(record,scene)
    result=json.loads((record/'result.json').read_text())
    links=json.loads((record/'vla_link_events.json').read_text())
    packets={e['id']:e for e in links if e.get('event')=='inference'}
    traces=[json.loads(s) for s in (record/'trace.jsonl').read_text().splitlines()]
    discovery=result.get('discovery');notification=result.get('notification');first=result.get('first_observation')
    image_checks=[]
    for p in packets.values():
        file=record/'observations'/p['image_file']
        image_checks.append(hashlib.sha256(file.read_bytes()).hexdigest()==p['image_sha256'])
    initial_absent=bool(first is not None and not any(p['clothing_color']==result['profile'] for p in first['perception']['persons']))
    # The first flying view also must look away, not only a ground-level view.
    hover_packets=[p for p in packets.values() if 'Stop and hover' in p['instruction'] and .85<p['estimated_state'][3]<1.2 and (not discovery or p['sim_time_capture']<discovery['t'])]
    first_hover=min(hover_packets,key=lambda p:p['sim_time_capture']) if hover_packets else None
    hover_absent=bool(first_hover and not any(p['clothing_color']==result['profile'] for p in first_hover['perception']['persons']))
    search_start=result.get('search_start_observation')
    projection=None
    if search_start:
        r=min(traces,key=lambda r:abs(r['t']-search_start['t']))
        q=np.array(r['truth'][19:26]);w,x,y,z=q[3:]
        rotation=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                           [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                           [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
        world=ET.parse(scene).getroot().find('worldbody')
        target=np.fromstring(world.find(f"body[@name='{result['profile']}_person']").get('pos'),sep=' ')
        cam=q[:3]+rotation@np.array([.014,0,.025])
        hfov=math.atan(math.tan(math.radians(64/2))*320/240)
        rays=[rotation.T@(target+np.array([dx,dy,dz])-cam) for dx in [-.35,.35] for dy in [-.35,.35] for dz in [0,1.9]]
        # Conservative person box lies entirely beyond one horizontal frustum plane.
        outside=all(v[0]<=0 for v in rays) or all(v[1]>v[0]*math.tan(hfov) for v in rays) or all(-v[1]>v[0]*math.tan(hfov) for v in rays)
        projection=dict(target_box_outside_horizontal_fov=bool(outside),capture_time=search_start['t'],
                        matched_trace_time=r['t'],camera_hfov_degrees=2*math.degrees(hfov),
                        target_box_half_width_m=.35,target_box_height_m=1.9,postflight_truth_only=True,
                        input_image=search_start['image_file'])
    evidence=discovery.get('evidence',[]) if discovery else []
    confirmed=len({p['id'] for p in evidence})>=3 and all(p['person']['clothing_color']==result['profile'] for p in evidence)
    report_verified=False
    if notification:
        e=notification['evidence'];p=packets.get(e['id'])
        report_verified=bool(p and p['image_sha256']==e['image_sha256'] and hashlib.sha256((record/'notification.jpg').read_bytes()).hexdigest()==e['image_sha256'] and 0<=notification['t']-e['t']<=2.5 and e['person']['clothing_color']==result['profile'])
    ordered=bool(discovery and notification and discovery['t']<notification['t']<traces[-1]['t'])
    checkpoints=base['checkpoints']
    checks=dict(physical_flight=base['success'],initial_target_absent=initial_absent,
                airborne_initial_target_absent=hover_absent,search_rotation_completed=bool(base['rotations']['right'].get('stopped') and 35<abs(base['rotations']['right'].get('clockwise_rotation_deg',0))<145),
                three_image_discovery=confirmed,original_image_notification=report_verified,
                discovery_notification_landing_order=ordered,all_camera_hashes_match=bool(image_checks) and all(image_checks),
                no_mission_failure=result.get('mission_failure') is None,
                search_start_geometry_out_of_view=bool(projection and projection['target_box_outside_horizontal_fov']),
                normal_end=result['stop_reason']=='landed_and_disarmed')
    report=dict(success=all(checks.values()),checks=checks,checkpoint_sha256=checkpoints,
                discovery_time_s=discovery['t'] if discovery else None,
                notification_time_s=notification['t'] if notification else None,
                completion_time_s=traces[-1]['t'],camera_frame_count=len(packets),
                initial_view_geometry=projection,
                physical=base,source='offline audit after flight; no simulator truth sent to perception or VLA',
                limits='One room with stationary people; no identity or medical-state recognition; simulated optical conditions uncalibrated')
    (record/'search_score.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(dict(success=report['success'],checks=checks,discovery=report['discovery_time_s'],notification=report['notification_time_s']),indent=2))
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('record',type=Path);p.add_argument('--scene',required=True,type=Path)
    a=p.parse_args();audit(a.record,a.scene)
