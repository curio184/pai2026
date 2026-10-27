"""Hold the conditions chapter card for the same four seconds as the demo card."""
import json,shutil,sys
from pathlib import Path
import consistent_narration as base
OUT=base.OUT;dest=OUT/'conditions_card4';dest.mkdir(exist_ok=True)
plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'));before=json.loads(json.dumps(plan));sec=plan[5]
source=Path(sec.get('work_dir',str(OUT/'conditions_movie')))
shift=4-sec.get('chapter_card_s',2)
voices=[]
for v in sec['voices']:
 clip=dict(v);clip['start']+=shift
 if source.resolve()!=dest.resolve():shutil.copy2(source/v['file'],dest/v['file'])
 assert base.sha(source/v['file'])==base.sha(dest/v['file'])
 voices.append(clip)
assert voices[0]['start']>=4
duration=sec['duration_s']+shift
(dest/'narration_plan.json').write_text(json.dumps(voices,ensure_ascii=False,indent=2),encoding='utf8')
sys.path.insert(0,str(base.ROOT));import make_rescue_presentation_audio as mixer
mixer.TMP=dest;mixer.PLAN=dict(duration_s=duration,flights=[],timeline=[dict(start=0)]);mixer.mix()
mixed=json.loads((dest/'voice_manifest.json').read_text(encoding='utf8'))
assert all(abs(a['duration_s']-b['duration_s'])<.001 for a,b in zip(voices,mixed))
sec.update(work_dir=str(dest),render_file=str(dest/'section.mp4'),duration_s=duration,chapter_card_s=4,voices=mixed)
assert all(plan[i]==before[i] for i in range(len(plan)) if i!=5)
(dest/'previous_plan.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
(dest/'review.json').write_text(json.dumps(dict(chapter_card_s=4,music_only_card=True,voice_starts=[v['start'] for v in mixed],duration_s=duration,flight_excerpt_duration_unchanged=True,source_wavs_unchanged=True),indent=2),encoding='utf8')
print('CONDITIONS_CARD_READY',duration,'full',sum(s['duration_s'] for s in plan),flush=True)
