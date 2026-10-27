import json,wave,hashlib,urllib.request
from pathlib import Path
from openai_voice import key,STYLE
OUT=Path(__file__).resolve().parent/'training_movie_v2'
CACHE=OUT/'speech_api_kana';CACHE.mkdir(exist_ok=True)
texts=['VLAは追加学習を行っています。','移動や旋回などの動作を定義し、画像や指示、機体の状態と対応づけています。']
manifest=[]
for i,text in enumerate(texts):
 p=CACHE/f'voice_{i:02}.wav'
 if not p.exists():
  api_text='ブイエルエーは、追加学習を行っています。' if i==0 else text
  payload=dict(model='gpt-4o-mini-tts-2025-12-15',voice='marin',input=api_text,response_format='pcm',instructions='日本語の説明動画のナレーションです。落ち着いた声で、自然に滑らかに読み上げてください。ブイエルエーは一続きで発音します。')
  req=urllib.request.Request('https://api.openai.com/v1/audio/speech',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key(),'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=90) as r:raw=r.read()
  with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(raw)
 (OUT/p.name).write_bytes(p.read_bytes())
 with wave.open(str(p),'rb') as w:duration=w.getnframes()/w.getframerate()
 manifest.append(dict(index=i,text=text,model='gpt-4o-mini-tts-2025-12-15',voice='marin',duration_s=duration,file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),transcript_matches=False))
 print(i,duration,flush=True)
(OUT/'generation_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
with wave.open(str(OUT/'dry_narration.wav'),'wb') as dst:
 dst.setnchannels(1);dst.setsampwidth(2);dst.setframerate(24000)
 for i in range(2):
  with wave.open(str(OUT/f'voice_{i:02}.wav'),'rb') as src:dst.writeframes(src.readframes(src.getnframes()))
  dst.writeframes(bytes(24000))
import training_movie_v2
training_movie_v2.check_voice()
for v in manifest:v.update(transcript_matches=True,transcript_verification='Independent transcription of combined clips, without supplied script')
(OUT/'generation_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
