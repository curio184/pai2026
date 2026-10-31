"""Describe saved detector outputs separately from VLA motion; no new inference."""
import argparse,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--suite',required=True);args=ap.parse_args()
    suite=W/'runs'/args.suite;summary=read(suite/'summary.json');rows=[]
    assert summary['completed']==summary['planned']
    for outcome in summary['cases']:
        case=outcome['case']
        if case['kind']!='search':continue
        root=suite/(case['id']+'_'+case['model'])/'record';file=root/'vla_link_events.json'
        events=[e for e in read(file) if e.get('event')=='inference'];counts=[];sequence=0;longest=0
        for e in events:
            n=sum(p['clothing_color']==case['color'] for p in e.get('perception',{}).get('persons',[]))
            counts.append(n);sequence=sequence+1 if n==1 else 0;longest=max(longest,sequence)
        prompt='Approach the person wearing '+case['color']+' and stop.'
        result=read(root/'result.json')
        row=dict(id=case['id'],color=case['color'],success=outcome['success'],mission_failure=result.get('mission_failure'),
            images=len(events),frames_with_exactly_one_requested_color=sum(n==1 for n in counts),
            longest_consecutive_requested_color_count=longest,
            requested_approach_prompt_count=sum(e['instruction']==prompt for e in events),
            discovery_saved=result.get('discovery') is not None,events_sha256=sha(file))
        if args.suite=='stress_train05_en' and case['id']=='H15':
            e=next(e for e in events if e['id']==45);image=root/'observations'/e['image_file']
            assert sha(image)==e['image_sha256']
            row['illustrative_example']=dict(image=image.relative_to(W).as_posix(),image_sha256=e['image_sha256'],
                accepted_person_colors=[p['clothing_color'] for p in e['perception']['persons']],
                instruction=e['instruction'],selection='Manually inspected illustrative failure frame; not a preregistered statistical sample or new detector inference.')
        rows.append(row)
    report=dict(suite=args.suite,cases=rows,scope='Saved detector outputs and VLA prompt records only.',
        caveat='Consecutive candidate count is not the runtime confirmation gate: that gate also checks overlap, age and timing. This diagnostic does not change scoring or assign every failure to one cause.')
    out=W/'reports'/(args.suite+'_perception_diagnostic.json')
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(cases=len(rows),failures=[r for r in rows if not r['success']],output=str(out))))
if __name__=='__main__':main()
