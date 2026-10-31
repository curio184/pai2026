"""Read-only phase/detection geometry diagnosis of every completed suite case.

Truth is read after flight, never supplied to the running policy or detector.
No new inference, scoring changes, or trial retries.
"""
import argparse, bisect, datetime, hashlib, json, math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from verify_records_round02_english import scene_path
W=Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--suite',required=True); a=ap.parse_args()
    folder=W/'runs'/a.suite; summary=read(folder/'summary.json')
    assert summary['completed']==summary['planned']
    rows=[]
    for outcome in summary['cases']:
        case=outcome['case']
        if case['kind']!='search': continue
        rec=folder/(case['id']+'_'+case['model'])/'record'
        if not (rec/'physical_score.json').exists():
            rows.append(dict(id=case['id'],success=outcome['success'],note='No completed physical record'));continue
        trace=[json.loads(line) for line in (rec/'trace.jsonl').read_text().splitlines()]
        score=read(rec/'physical_score.json'); times=[r['t'] for r in trace]
        world=ET.parse(scene_path(case)).getroot().find('worldbody')
        persons={c:np.fromstring(world.find(f"body[@name='{c}_person']").get('pos'),sep=' ')[:2] for c in ['blue','red']}
        phases={}; closest=None
        for t in trace:
            truth=t['truth']; height=-truth[3]
            if height<=.1:continue
            xy=np.array([truth[2],truth[1]])
            color,dist=min(((c,float(np.linalg.norm(xy-p))) for c,p in persons.items()),key=lambda pair:pair[1])
            item=dict(t=t['t'],phase=t['phase'],person=color,distance_m=dist,height_m=height,
                      scene_xy_m=xy.tolist(),estimated_state=t['estimated_state'],model_action=t['model_action'])
            if closest is None or dist<closest['distance_m']:closest=item
            if t['phase'] not in phases or dist<phases[t['phase']]['distance_m']:phases[t['phase']]=item
        assert abs(closest['distance_m']-score['minimum_person_clearance_m'])<1e-8
        observations=[]
        for e in read(rec/'vla_link_events.json'):
            if e.get('event')!='inference':continue
            k=min(bisect.bisect_left(times,e['sim_time_capture']),len(trace)-1)
            if k and abs(times[k-1]-e['sim_time_capture'])<abs(times[k]-e['sim_time_capture']):k-=1
            t=trace[k]; q=t['truth'][19:26]; w,x,y,z=q[3:]
            heading=math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
            delta=persons[case['color']]-q[:2]
            bearing=math.atan2(delta[1],delta[0])-heading
            bearing=math.atan2(math.sin(bearing),math.cos(bearing))
            people=e['perception']['persons']; selected=[p for p in people if p.get('clothing_color')==case['color']]
            path=rec/'observations'/e['image_file'];assert sha(path)==e['image_sha256']
            observations.append(dict(id=e['id'],capture_s=e['sim_time_capture'],phase=t['phase'],
                image=path.relative_to(W).as_posix(),image_sha256=e['image_sha256'],
                requested_color_detections=len(selected),requested_bboxes=[p['bbox'] for p in selected],
                requested_person_bearing_deg=math.degrees(bearing),
                requested_person_distance_m=float(np.linalg.norm(delta)),
                estimated_state=e['estimated_state'],action=e['action']))
        byphase={}
        for phase in sorted(set(x['phase'] for x in observations)):
            rr=[x for x in observations if x['phase']==phase]
            byphase[phase]=dict(images=len(rr),exactly_one_requested_detection=sum(x['requested_color_detections']==1 for x in rr),
                bearing_min_median_max_deg=np.percentile([x['requested_person_bearing_deg'] for x in rr],[0,50,100]).tolist())
        rows.append(dict(id=case['id'],color=case['color'],success=outcome['success'],
            failure=read(rec/'result.json').get('mission_failure'),
            closest_person=closest,closest_by_phase=phases,perception_by_phase=byphase,
            observations=observations,trace_sha256=sha(rec/'trace.jsonl'),events_sha256=sha(rec/'vla_link_events.json')))
    report=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),suite=a.suite,
        completed=summary['completed'],planned=summary['planned'],cases=rows,
        scope='All completed search trials. Postflight geometry and saved detector outputs only; no policy inference, runtime changes, or changed success criteria.',
        caveat='Person center bearing is diagnostic geometry, not proof of detector visibility. Closest timestamps use saved trace resolution. Correlation does not establish a unique cause.')
    dest=W/'reports'/(a.suite+'_perception_diagnostic.json'); assert not dest.exists()
    dest.write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(dict(path=str(dest),completed=len(rows),failures=[dict(id=r['id'],failure=r.get('failure'),closest=r.get('closest_person')) for r in rows if not r['success']])))
if __name__=='__main__': main()
