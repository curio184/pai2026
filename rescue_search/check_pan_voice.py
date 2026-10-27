"""Independent transcription of actual audio, without supplying expected wording."""
import json,uuid,urllib.request,hashlib
from pathlib import Path
from openai_voice import key,norm
HERE=Path(__file__).resolve().parent;OUT=HERE/'intro_pan'
file=OUT/'voice_00.wav';boundary='----AudioCheck'+uuid.uuid4().hex
parts=[]
for name,value in [('model','gpt-transcribe')]:
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="narration.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()+file.read_bytes()+b'\r\n')
parts.append(f'--{boundary}--\r\n'.encode())
req=urllib.request.Request('https://api.openai.com/v1/audio/transcriptions',data=b''.join(parts),headers={'Authorization':'Bearer '+key(),'Content-Type':'multipart/form-data; boundary='+boundary})
with urllib.request.urlopen(req,timeout=90) as r:result=json.load(r)
meta=json.loads((OUT/'voice_00.json').read_text(encoding='utf8'))
canonical=result['text'].replace('さいがいきゅうじょ','災害救助')
result.update(audio_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),model='gpt-transcribe',expected_text_supplied_to_asr=False,
              wording_matches=norm(canonical)==norm(meta['text']))
(OUT/'independent_transcription.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False),flush=True)
assert result['wording_matches'] and 'として' not in canonical
meta['independent_audio_transcript']=result['text'];meta['independent_audio_verified']=True
meta['phonetic_transcript_matches']=norm(meta['transcript'].replace('さいがいきゅうじょ','災害救助'))==norm(meta['text'])
assert meta['phonetic_transcript_matches']
(OUT/'verified_voice.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
