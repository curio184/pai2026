"""Review-only narrated training slide and its surrounding transition."""
import os,sys,json,wave,subprocess,hashlib,uuid,urllib.request,math
from pathlib import Path
import numpy as np
from PIL import Image
import imageio.v2 as imageio
from demo_movie import font,text,smooth,BG,WHITE
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);HERE=Path(__file__).resolve().parent
OUT=HERE/'training_movie';FPS=24
generation=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'))
STARTS=[.7,.7+generation[0]['duration_s']+.5]
DURATION=math.ceil(STARTS[1]+generation[1]['duration_s']+1.2)
DEST=ROOT/'output/video/rescue_drone_training_preview.mp4'
CAPTIONS=[['VLAにドローンの飛行動作を覚えさせるため、','追加学習を行っています。'],
 ['移動や旋回などの動作を定義し、画像や指示、','機体の状態と対応づけて学習しています。']]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audio():
 import make_rescue_presentation_audio as mixer
 generated=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'))
 clips=[]
 for i,(g,start) in enumerate(zip(generated,STARTS)):
  assert g['transcript_matches'] and ''.join(CAPTIONS[i])==g['text']
  assert sha(OUT/g['file'])==g['sha256']
  clips.append(dict(index=i,start=start,max_s=g['duration_s']+.1,text=g['text'],caption=g['text'],file=g['file']))
 assert clips[0]['start']+clips[0]['max_s']<clips[1]['start']
 assert clips[-1]['start']+clips[-1]['max_s']<DURATION-.5
 (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
 mixer.TMP=OUT;mixer.PLAN=dict(duration_s=DURATION,flights=[],timeline=[dict(start=0)]);mixer.mix()
 review=json.loads((OUT/'audio_review.json').read_text());review.update(voice='OpenAI gpt-realtime-2.1-mini / marin',rotor='None',time_stretch_used=False)
 (OUT/'audio_review.json').write_text(json.dumps(review,indent=2))
 with wave.open(str(OUT/'dry_narration.wav'),'wb') as dst:
  dst.setnchannels(1);dst.setsampwidth(2);dst.setframerate(24000)
  for i in range(2):
   with wave.open(str(OUT/f'voice_{i:02}.wav'),'rb') as src:dst.writeframes(src.readframes(src.getnframes()))
   dst.writeframes(bytes(24000))
def check_voice():
 from openai_voice import key,norm
 file=OUT/'dry_narration.wav';boundary='----AudioCheck'+uuid.uuid4().hex
 body=(f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\ngpt-transcribe\r\n'.encode()+f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="narration.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()+file.read_bytes()+f'\r\n--{boundary}--\r\n'.encode())
 req=urllib.request.Request('https://api.openai.com/v1/audio/transcriptions',data=body,headers={'Authorization':'Bearer '+key(),'Content-Type':'multipart/form-data; boundary='+boundary})
 with urllib.request.urlopen(req,timeout=90) as r:result=json.load(r)
 def canonical(s):return norm(s).lower().replace('vla','ブイエルエー').replace('ぶいえるえー','ブイエルエー').replace('対応付け','対応づけ')
 expected=''.join(''.join(c) for c in CAPTIONS)
 result.update(wording_matches=canonical(result['text'])==canonical(expected),audio_sha256=sha(file),expected_text_supplied_to_asr=False)
 (OUT/'independent_transcription.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(result,ensure_ascii=False),flush=True);assert result['wording_matches']
def render():
 slide=ROOT/'output/video/mechanism_review/smolvla_training_overview.png'
 canvas=Image.new('RGB',(1920,1080),BG)
 canvas.paste(Image.open(slide).convert('RGB').resize((1728,972),Image.Resampling.LANCZOS),(96,0))
 voices=json.loads((OUT/'voice_manifest.json').read_text(encoding='utf8'))
 def frame(t):
  im=canvas.copy()
  for i,v in enumerate(voices):
   if v['start']<=t<v['start']+v['duration_s']+.1:
    for j,line in enumerate(CAPTIONS[i]):
     assert font(31).getlength(line)<1728
     text(im,960,984+j*43,line,31,WHITE,450,anchor='mt')
  if t<.35:im=Image.blend(Image.new('RGB',im.size),im,smooth(t/.35))
  if t>DURATION-.4:im=Image.blend(im,Image.new('RGB',im.size),smooth((t-DURATION+.4)/.4))
  return im
 os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg'
 with imageio.get_writer(OUT/'silent.mp4',fps=FPS,codec='h264_nvenc',macro_block_size=1,ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p'],ffmpeg_log_level='error') as w:
  for i in range(DURATION*FPS):w.append_data(np.asarray(frame(i/FPS)))
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','96000','-af','loudnorm=I=-16:TP=-2:LRA=7','-movflags','+faststart','-t',str(DURATION),str(DEST)],check=True)
 frame(3).save(OUT/'preview.png')
 # Context preview: eight seconds of the mechanism, new slide, then six seconds of the demonstration.
 parts=[(ROOT/'output/video/rescue_drone_mechanism.mp4',20,8),(ROOT/'output/video/rescue_drone_demonstration.mp4',0,6)]
 for i,(p,start,duration) in enumerate(parts):
  subprocess.run(['ffmpeg','-v','error','-y','-ss',str(start),'-i',str(p),'-t',str(duration),'-c:v','h264_nvenc','-cq','18','-c:a','aac','-ar','96000','-b:a','192k',str(OUT/f'context_{i}.mp4')],check=True)
 from ending_movie import join
 context=ROOT/'output/video/rescue_drone_training_context_preview.mp4'
 join([OUT/'context_0.mp4',DEST,OUT/'context_1.mp4'],[8,DURATION,6],context,'training_context')
 checks=[]
 for p,seconds in [(DEST,DURATION),(context,14+DURATION)]:
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
  v=next(s for s in probe['streams'] if s['codec_type']=='video')
  assert int(v['nb_frames'])==seconds*FPS and abs(float(probe['format']['duration'])-seconds)<.1
  assert not any(s['codec_type']=='subtitle' for s in probe['streams']) and not p.with_suffix('.srt').exists()
  subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(p),'-f','null','-'],check=True)
  checks.append(dict(video=str(p),duration_s=seconds,sha256=sha(p),full_decode=True))
 (OUT/'review.json').write_text(json.dumps(dict(status='Review only; final film unchanged',videos=checks,slide_sha256=sha(slide),narration_text=[''.join(c) for c in CAPTIONS],narration_starts_s=STARTS,no_audio_time_stretch=True,subtitle_delivery='Burned-in only',visual_review_complete=False),ensure_ascii=False,indent=2),encoding='utf8')
 print('TRAINING_PREVIEW_COMPLETE',context,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
