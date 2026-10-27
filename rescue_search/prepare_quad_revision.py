"""Shorter evidence sequence and newly generated, unstretched training voice."""
import json,math,shutil,sys
import consistent_narration as base
OUT=base.OUT
plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'));before=json.loads(json.dumps(plan))
sys.path.insert(0,str(base.ROOT));import make_rescue_presentation_audio as mixer
for index,srcname,dstname in [(2,'new_training_natural02','training_natural'),(5,'new_conditions_quad02','conditions_quad')]:
 source=OUT/srcname;dest=OUT/dstname;dest.mkdir(exist_ok=True)
 assert json.loads((source/'asr.json').read_text(encoding='utf8'))['wording_matches']
 manifest=json.loads((source/'manifest.json').read_text(encoding='utf8'));clips=[];at=.7 if index==2 else 4.25
 for i,v in enumerate(manifest):
  p=source/v['file'];assert base.sha(p)==v['sha256'];shutil.copy2(p,dest/v['file'])
  seconds=base.wav_duration(p)
  clips.append(dict(index=i,start=at,max_s=seconds+.2,text=v['text'],caption=v['text'],file=v['file'],duration_s=seconds,source=str(p),source_sha256=v['sha256'],tempo_factor=1.0))
  at+=seconds+.5
 duration=math.ceil(at+.7) if index==2 else 18
 assert at-.5<duration-1
 if index==5:assert at-.5<14
 (dest/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
 mixer.TMP=dest;mixer.PLAN=dict(duration_s=duration,flights=[],timeline=[dict(start=0)]);mixer.mix()
 voices=json.loads((dest/'voice_manifest.json').read_text(encoding='utf8'))
 assert all(abs(a['duration_s']-b['duration_s'])<.001 for a,b in zip(voices,clips))
 plan[index].update(work_dir=str(dest),render_file=str(dest/'section.mp4'),voices=voices,duration_s=duration,narration_pace='New OpenAI narration at normal API speed 1.0; no editorial tempo adjustment; listening approval pending')
 if index==2:plan[index]['caption_lines']=[['VLAを飛行制御に対応させるため、','追加学習を行いました。'],['移動や旋回などの動作を定義し、','画像や指示、機体の状態と対応付けました。']]
 else:plan[index].update(renderer_module='conditions_quad',chapter_card_s=4)
 (dest/'review.json').write_text(json.dumps(dict(duration_s=duration,voice_source_verified=True,no_editorial_time_stretch=True,audio_listening_review=False,visual_review_complete=False),indent=2),encoding='utf8')
assert all(plan[i]==before[i] for i in range(len(plan)) if i not in [2,5])
assert sum(s['duration_s'] for s in plan)<=180
(OUT/'before_quad_plan.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
print('QUAD_PLAN_READY',[(s['folder'],s['duration_s']) for s in plan],sum(s['duration_s'] for s in plan),flush=True)
