"""Use the approved slower delivery without squeezing it into the old slide."""
import json,math,shutil,sys
import consistent_narration as base
OUT=base.OUT;source=OUT/'new_training_slow_past';dest=OUT/'training_slow_past';dest.mkdir(exist_ok=True)
assert json.loads((source/'asr.json').read_text(encoding='utf8'))['wording_matches']
manifest=json.loads((source/'manifest.json').read_text(encoding='utf8'))
texts=['VLAを飛行制御に対応させるため、追加学習を行いました。','移動や旋回などの動作を定義し、','画像や指示、機体の状態と対応付けました。']
assert [v['text'] for v in manifest]==texts
plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'));before=json.loads(json.dumps(plan))
clips=[];at=.8
for i,v in enumerate(manifest):
 p=source/v['file'];assert base.sha(p)==v['sha256']
 shutil.copy2(p,dest/v['file'])
 duration=base.wav_duration(p)
 clips.append(dict(index=i,start=at,max_s=duration+.2,text=v['text'],caption=v['text'],file=v['file'],duration_s=duration,source=str(p),source_sha256=v['sha256'],tempo_factor=1.0))
 at+=duration+([.65,.35,1.3][i])
duration=math.ceil(at)
(dest/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
sys.path.insert(0,str(base.ROOT));import make_rescue_presentation_audio as mixer
mixer.TMP=dest;mixer.PLAN=dict(duration_s=duration,flights=[],timeline=[dict(start=0)]);mixer.mix()
voices=json.loads((dest/'voice_manifest.json').read_text(encoding='utf8'))
assert all(abs(v['duration_s']-c['duration_s'])<.001 for v,c in zip(voices,clips))
plan[2].update(voices=voices,work_dir=str(dest),render_file=str(dest/'section.mp4'),duration_s=duration,caption_lines=[['VLAを飛行制御に対応させるため、','追加学習を行いました。'],[texts[1]],[texts[2]]],narration_pace='Fresh unhurried OpenAI narration, API speed 0.9, no editorial time stretch; 0.65 s sentence pause and 0.35 s clause pause')
assert all(plan[i]==before[i] for i in range(len(plan)) if i!=2)
(dest/'previous_plan.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
(dest/'review.json').write_text(json.dumps(dict(narration=voices,duration_s=duration,other_sections_unchanged=True,no_editorial_time_stretch=True,verified_asr=True,visual_review_complete=False),ensure_ascii=False,indent=2),encoding='utf8')
print('SLOW_TRAINING_READY',duration,'full',sum(s['duration_s'] for s in plan),flush=True)
