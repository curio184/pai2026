"""Match the approved training narration to the surrounding sentence pace."""
import json,math,sys
import consistent_narration as base
from narration_pace_audit import mora
OUT=base.OUT;source=OUT/'new_training_slow_past';dest=OUT/'training_matched';dest.mkdir(exist_ok=True)
assert json.loads((source/'asr.json').read_text(encoding='utf8'))['wording_matches']
manifest=json.loads((source/'manifest.json').read_text(encoding='utf8'))
texts=['VLAを飛行制御に対応させるため、追加学習を行いました。','移動や旋回などの動作を定義し、','画像や指示、機体の状態と対応付けました。']
readings=['ぶいえるえーをひこうせいぎょにたいおうさせるため、ついかがくしゅうをおこないました。','いどうやせんかいなどのどうさをていぎし、','がぞうやしじ、きたいのじょうたいとたいおうづけました。']
assert [v['text'] for v in manifest]==texts
plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'));before=json.loads(json.dumps(plan))
clips=[];at=.7
for i,(v,reading) in enumerate(zip(manifest,readings)):
 p=source/v['file'];assert base.sha(p)==v['sha256']
 target=round(mora(reading)/6.8+reading.count('、')*.12+.18,3)
 ratio=base.wav_duration(p)/target
 assert .8<ratio<1.6,(i,ratio)
 output=dest/v['file']
 base.run(['ffmpeg','-v','error','-y','-i',str(p),'-af',f'atempo={ratio:.8f}','-ar','24000','-ac','1',str(output)])
 duration=base.wav_duration(output);assert abs(duration-target)<.08
 clips.append(dict(index=i,start=at,max_s=duration+.2,text=v['text'],caption=v['text'],file=v['file'],duration_s=duration,source=str(p),source_sha256=v['sha256'],tempo_factor=ratio,reading=reading,mora=mora(reading),target_duration_s=target))
 at+=duration+([.5,.25,1.2][i])
duration=math.ceil(at)
(dest/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
sys.path.insert(0,str(base.ROOT));import make_rescue_presentation_audio as mixer
mixer.TMP=dest;mixer.PLAN=dict(duration_s=duration,flights=[],timeline=[dict(start=0)]);mixer.mix()
voices=json.loads((dest/'voice_manifest.json').read_text(encoding='utf8'))
assert all(abs(v['duration_s']-c['duration_s'])<.001 for v,c in zip(voices,clips))
plan[2].update(voices=voices,work_dir=str(dest),render_file=str(dest/'section.mp4'),duration_s=duration,caption_lines=[['VLAを飛行制御に対応させるため、','追加学習を行いました。'],[texts[1]],[texts[2]]],narration_pace='Same 6.8 mora/s plus punctuation allowance as surrounding narration; pitch-preserving tempo adjustment; 0.5 s sentence pause and 0.25 s clause pause')
assert all(plan[i]==before[i] for i in range(len(plan)) if i!=2)
assert plan[5]['chapter_card_s']==4
(dest/'previous_plan.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
(dest/'review.json').write_text(json.dumps(dict(narration=voices,duration_s=duration,other_sections_unchanged=True,verified_source_asr=True,visual_review_complete=False,audio_listening_review=False),ensure_ascii=False,indent=2),encoding='utf8')
print('MATCHED_TRAINING_READY',duration,'full',sum(s['duration_s'] for s in plan),'tempo',[round(c['tempo_factor'],3) for c in clips],flush=True)
