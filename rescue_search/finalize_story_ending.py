"""Apply the approved purpose-led closing to the uniformly paced full edit."""
import json,math,shutil,sys
from pathlib import Path
import consistent_narration as base
from narration_pace_audit import mora
OUT=base.OUT;DEST=OUT/'story_ending';DEST.mkdir(exist_ok=True)
plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'))
old=plan[6]
manifest=json.loads((OUT/'new_closing/manifest.json').read_text(encoding='utf8'))
assert json.loads((OUT/'new_closing/asr.json').read_text(encoding='utf8'))['wording_matches']
# Retain the approved hardware narration and its already-normalized pace.
hardware=dict(old['voices'][0]);hardware.update(index=0,file='voice_00.wav')
hardware_source=Path(old.get('work_dir',str(OUT/'ending_movie')))/old['voices'][0]['file']
if hardware_source.resolve()!=(DEST/'voice_00.wav').resolve():shutil.copy2(hardware_source,DEST/'voice_00.wav')
clips=[hardware]
readings=['ことばによるしじでひさいしゃをさがす。','ひとがたちいりにくいばしょで、そうさくをささえるどろーんをめざしています。']
hardware_end=11;at=hardware_end+.6
for j,(v,reading) in enumerate(zip(manifest,readings)):
 source=OUT/'new_closing'/v['file'];assert base.sha(source)==v['sha256']
 target=round(mora(reading)/6.8+reading.count('、')*.12+.18,3)
 # Keep the short closing phrase unhurried rather than force its syllable target.
 ratio=min(base.wav_duration(source)/target,1.25)
 target=base.wav_duration(source)/ratio
 assert .75<ratio<1.3,(j,ratio)
 file=f'voice_{j+1:02}.wav'
 base.run(['ffmpeg','-v','error','-y','-i',str(source),'-af',f'atempo={ratio:.8f}','-ar','24000','-ac','1',str(DEST/file)])
 actual=base.wav_duration(DEST/file);assert abs(actual-target)<.08
 clips.append(dict(index=j+1,start=at,max_s=actual+.1,text=v['text'],caption=v['text'],file=file,duration_s=actual,original_source_duration_s=v['duration_s'],tempo_factor=ratio,reading=reading,source=str(source),source_sha256=v['sha256']))
 at+=actual+.5
duration=math.ceil(at-.5+2.8)
assert clips[0]['start']+clips[0]['duration_s']<hardware_end-.5
assert all(a['start']+a['duration_s']<b['start'] for a,b in zip(clips,clips[1:]))
(DEST/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
sys.path.insert(0,str(base.ROOT));import make_rescue_presentation_audio as mixer
mixer.TMP=DEST;mixer.PLAN=dict(duration_s=duration,flights=[],timeline=[dict(start=0)]);mixer.mix()
voices=json.loads((DEST/'voice_manifest.json').read_text(encoding='utf8'))
plan[6].update(voices=voices,work_dir=str(DEST),render_file=str(DEST/'section.mp4'),duration_s=duration,hardware_end_s=hardware_end,caption_lines=[['実機への展開を見据え、実在する小型ドローンとカメラ、','制御用パソコンを組み合わせた構成にしています。'],['言葉による指示で被災者を探す。'],['人が立ち入りにくい場所で、','捜索を支えるドローンを目指しています。']],closing_intent='Purpose-led closing; experiment-report lines removed; hardware caveat remains on the slide',music_only_tail_s=duration-voices[-1]['start']-voices[-1]['duration_s'])
(OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
(DEST/'review.json').write_text(json.dumps(dict(duration_s=duration,narration=voices,music_only_tail_s=plan[6]['music_only_tail_s'],hardware_label='無線通信',unverified_hardware_note_retained=True),ensure_ascii=False,indent=2),encoding='utf8')
print('STORY_ENDING_READY',duration,'total',sum(s['duration_s'] for s in plan),'tail',plan[6]['music_only_tail_s'],flush=True)
