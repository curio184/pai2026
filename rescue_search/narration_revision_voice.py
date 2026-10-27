import json,wave,hashlib,urllib.request,uuid,sys,shutil,os
from pathlib import Path
from openai_voice import key,norm
OUT=Path(__file__).resolve().parent/'narration_consistent/new_training';OUT.mkdir(parents=True,exist_ok=True)
TEXTS=['SmolVLAを飛行制御に対応させるため、追加学習を行っています。','移動や旋回などの動作を定義し、画像や指示、機体の状態と対応付けています。']
INPUTS=['スモールブイエルエーを飛行制御に対応させるため、追加学習を行っています。',TEXTS[1]]
INSTRUCTIONS='日本語の説明動画のナレーションです。落ち着いた声で、自然に滑らかに読み上げてください。スモールブイエルエーは一続きで発音します。文の途中で急に早口にならず、一定の読みやすいテンポを保ってください。'
SPEED=1.0
if len(sys.argv)>1 and sys.argv[1]=='training_natural':
 OUT=OUT.parent/'new_training_natural02';OUT.mkdir(parents=True,exist_ok=True)
 shutil.copy2(OUT.parent/'new_training_natural/voice_01.wav',OUT/'voice_01.wav')
 TEXTS=['VLAを飛行制御に対応させるため、追加学習を行いました。','移動や旋回などの動作を定義し、画像や指示、機体の状態と対応付けました。']
 INPUTS=['ブイエルエーを、ひこうせいぎょに対応させるため、追加学習を行いました。',TEXTS[1]]
 INSTRUCTIONS='日本語の説明動画のナレーションです。落ち着いた自然な声で、標準的な説明のテンポで滑らかに読んでください。特別ゆっくりにも早口にもせず、読点で短く間を取り、文末を引き伸ばさないでください。ブイエルエーはひと続きの名称として発音し、文字ごとに区切らないでください。指定された文章のみを正確に読み上げてください。'
elif len(sys.argv)>1 and sys.argv[1]=='conditions_quad':
 OUT=OUT.parent/'new_conditions_quad02';OUT.mkdir(parents=True,exist_ok=True)
 TEXTS=['災害現場を想定し、霧や粉じんで視界が悪くなる条件でも、捜索できることを確かめました。']
 INPUTS=['災害現場を想定し、きりやふんじんで視界が悪くなる条件でも、そうさくできることを確かめました。']
 INSTRUCTIONS='日本語の説明動画のナレーションです。落ち着いた自然な声で、標準的な説明のテンポで滑らかに読んでください。特別ゆっくりにも早口にもせず、読点で短く間を取り、文末を引き伸ばさないでください。ふんじんは粉塵の読みです。指定された文章のみを正確に読み上げてください。'
elif len(sys.argv)>1 and sys.argv[1]=='ending':
 OUT=OUT.parent/'new_ending';OUT.mkdir(parents=True,exist_ok=True)
 TEXTS=['実機への展開を見据え、実在する小型ドローンとカメラ、制御用パソコンを組み合わせた構成にしています。']
 INPUTS=TEXTS
elif len(sys.argv)>1 and sys.argv[1]=='closing':
 OUT=OUT.parent/'new_closing';OUT.mkdir(parents=True,exist_ok=True)
 TEXTS=['言葉による指示で被災者を探す。','人が立ち入りにくい場所で、捜索を支えるドローンを目指しています。']
 INPUTS=TEXTS
elif len(sys.argv)>1 and sys.argv[1] in ['training_slow','training_slow_past']:
 OUT=OUT.parent/'new_training_slow';OUT.mkdir(parents=True,exist_ok=True)
 TEXTS=['VLAを飛行制御に対応させるため、追加学習を行いました。','移動や旋回などの動作を定義し、','画像や指示、機体の状態と対応付けています。']
 INPUTS=['ブイエルエーを飛行制御に対応させるため、追加学習を行いました。',TEXTS[1],TEXTS[2]]
 INSTRUCTIONS='日本語の説明動画のナレーションです。落ち着いた自然な声で、普段よりゆっくり、聞き手が図を理解できる余裕を持って読んでください。ブイエルエーは一つの名称として滑らかにつなげ、一文字ずつ区切らないでください。読点では短く自然に間を取り、文末を引き伸ばさず、最後まで一定のゆったりしたテンポを保ってください。指定された文章のみを正確に読み上げてください。'
 SPEED=.9
 if sys.argv[1]=='training_slow_past':
  prior=OUT;OUT=OUT.parent/'new_training_slow_past';OUT.mkdir(parents=True,exist_ok=True)
  for i in [0,1]:shutil.copy2(prior/f'voice_{i:02}.wav',OUT/f'voice_{i:02}.wav')
  TEXTS[2]='画像や指示、機体の状態と対応付けました。'
  INPUTS[2]=TEXTS[2]
manifest=[]
for i,(text,api_text) in enumerate(zip(TEXTS,INPUTS)):
 p=OUT/f'voice_{i:02}.wav'
 if not p.exists():
  payload=dict(model='gpt-4o-mini-tts-2025-12-15',voice='marin',input=api_text,response_format='pcm',instructions=INSTRUCTIONS,speed=SPEED)
  req=urllib.request.Request('https://api.openai.com/v1/audio/speech',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key(),'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=90) as r:raw=r.read()
  with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(raw)
 with wave.open(str(p),'rb') as w:duration=w.getnframes()/w.getframerate()
 manifest.append(dict(index=i,text=text,api_input_text=api_text,duration_s=duration,file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),model='gpt-4o-mini-tts-2025-12-15',voice='marin',speed=SPEED,instructions=INSTRUCTIONS))
 print(i,duration,flush=True)
with wave.open(str(OUT/'dry.wav'),'wb') as dst:
 dst.setnchannels(1);dst.setsampwidth(2);dst.setframerate(24000)
 for i in range(len(TEXTS)):
  with wave.open(str(OUT/f'voice_{i:02}.wav'),'rb') as src:dst.writeframes(src.readframes(src.getnframes()))
  dst.writeframes(bytes(24000))
boundary='----Check'+uuid.uuid4().hex
asr_model=os.environ.get('NARRATION_ASR_MODEL','gpt-transcribe')
body=(f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\n{asr_model}\r\n'.encode()+f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="voice.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()+(OUT/'dry.wav').read_bytes()+f'\r\n--{boundary}--\r\n'.encode())
req=urllib.request.Request('https://api.openai.com/v1/audio/transcriptions',data=body,headers={'Authorization':'Bearer '+key(),'Content-Type':'multipart/form-data; boundary='+boundary})
with urllib.request.urlopen(req,timeout=90) as r:asr=json.load(r)
def canon(s):return norm(s).lower().replace('smolvla','スモールブイエルエー').replace('スモルブイエルエー','スモールブイエルエー').replace('vla','ブイエルエー').replace('対応付け','対応づけ').replace('粉じん','ふんじん').replace('粉塵','ふんじん')
asr.update(wording_matches=canon(asr['text'])==canon(''.join(TEXTS)),expected_text_supplied=False,audio_sha256=hashlib.sha256((OUT/'dry.wav').read_bytes()).hexdigest())
(OUT/'asr.json').write_text(json.dumps(asr,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(asr,ensure_ascii=False),flush=True)
assert asr['wording_matches']
