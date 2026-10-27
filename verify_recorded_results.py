"""Recompute the four scores from shipped logs without GPU, training or a simulator."""
from pathlib import Path
import contextlib,hashlib,io,json,shutil,tempfile
from score_mission import score
ROOT=Path(__file__).resolve().parent
records=ROOT/'outputs/ardupilot/realism_precision_03'
scene=ROOT/'assets/civic_realism/physics03/rescue_scene.xml'
summary=[]
with tempfile.TemporaryDirectory(prefix='rescue-record-check-') as temporary:
    for profile in ['blue','red','turns','left']:
        source=records/profile;case=Path(temporary)/profile;case.mkdir()
        for name in ['trace.jsonl','result.json','events.json','vla_link_events.json','last_messages.json']:shutil.copy2(source/name,case/name)
        expected=json.loads((source/'physical_score.json').read_text(encoding='utf8'))
        with contextlib.redirect_stdout(io.StringIO()):actual=score(case,scene)
        assert actual==expected,(profile,'Stored and recomputed scores differ')
        count=0
        for event in json.loads((source/'vla_link_events.json').read_text(encoding='utf8')):
            if event.get('event')=='inference':
                image=source/'observations'/event['image_file']
                assert hashlib.sha256(image.read_bytes()).hexdigest()==event['image_sha256']
                count+=1
        summary.append(dict(profile=profile,success=actual['success'],score_matches=True,verified_inputs=count))
assert all(r['success'] for r in summary)
print(json.dumps(dict(all_pass=True,checks=summary),indent=2))
