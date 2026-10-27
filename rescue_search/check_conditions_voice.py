import json,uuid,urllib.request,hashlib
from pathlib import Path
from openai_voice import key,norm
HERE=Path(__file__).resolve().parent;OUT=HERE/'conditions_movie';file=OUT/'dry_narration.wav'
boundary='----AudioCheck'+uuid.uuid4().hex
body=(f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\ngpt-transcribe\r\n'.encode()+
      f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="narration.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()+file.read_bytes()+
      f'\r\n--{boundary}--\r\n'.encode())
req=urllib.request.Request('https://api.openai.com/v1/audio/transcriptions',data=body,headers={'Authorization':'Bearer '+key(),'Content-Type':'multipart/form-data; boundary='+boundary})
with urllib.request.urlopen(req,timeout=90) as r:result=json.load(r)
expected=''.join(g['text'] for g in json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8')))
def canonical(s):return norm(s).lower().replace('vla','ブイエルエー').replace('ai','エーアイ').replace('粉塵','ふんじん').replace('粉じん','ふんじん').replace('四つ','4つ').replace('見え方','みえかた').replace('災害現場','さいがいげんば')
result.update(audio_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),model='gpt-transcribe',expected_text_supplied_to_asr=False,
    wording_matches=canonical(result['text'])==canonical(expected))
(OUT/'independent_transcription.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False),flush=True)
assert result['wording_matches']
