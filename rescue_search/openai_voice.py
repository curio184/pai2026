"""Create local narration assets using the user-authorized OpenAI API."""
import argparse,base64,hashlib,json,os,re,sys,time,unicodedata,urllib.request,urllib.error,wave
from pathlib import Path
import websocket

HERE=Path(__file__).resolve().parent
OUT=HERE/'intro_openai';OUT.mkdir(exist_ok=True)
ENV=Path(os.environ.get('RESCUE_PROJECT_ROOT', Path(__file__).resolve().parents[1]))/'.env'
STYLE=('Read the supplied Japanese text verbatim as a professional Japanese documentary narrator. '
       'Use natural standard Japanese pronunciation, a calm, warm, assured voice, restrained emotion, '
       'and an unhurried but concise pace. Brief natural pauses at punctuation. '
       'Do not elongate sentence endings. Do not sound like an advertisement. '
       'Do not add introductions, commentary, explanations or any words not in the supplied text.')
TEXTS=['人が立ち入りにくい建物を、小型ドローンで捜索します。',
       '青い服の人を探して。',
       '言葉による指示で捜索を任せ、操縦の負担を減らすことを目指します。']

def key():
    value=os.environ.get('OPENAI_API_KEY')
    if not value:
        for line in ENV.read_text(encoding='utf-8-sig').splitlines():
            m=re.match(r'^\s*(?:export\s+)?OPENAI_API_KEY\s*=\s*(.*?)\s*$',line)
            if m:
                value=m[1]
                if value[:1] in ('"',"'"):value=value[1:value.rfind(value[0])]
                else:value=value.split(' #',1)[0].strip()
                break
    if not value:raise RuntimeError('OPENAI_API_KEY is not configured')
    return value

def models():
    req=urllib.request.Request('https://api.openai.com/v1/models',headers={'Authorization':'Bearer '+key()})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:obj=json.load(r)
    except urllib.error.HTTPError as e:
        obj=json.loads(e.read());raise RuntimeError('OpenAI API status '+str(e.code)+': '+str(obj.get('error',{}).get('code')))
    names=sorted(x['id'] for x in obj['data'] if any(s in x['id'] for s in ['tts','realtime']))
    print(json.dumps(names))
    return names

def norm(text):return ''.join(c for c in unicodedata.normalize('NFKC',text) if c.isalnum())

def generate(model,voice):
    reports=[]
    for i,text in enumerate(TEXTS):
        path=OUT/f'voice_{i:02}.wav';meta=OUT/f'voice_{i:02}.json'
        if path.exists() and meta.exists():
            info=json.loads(meta.read_text(encoding='utf8'))
            assert info['text']==text and info['model']==model and info['voice']==voice
            reports.append(info);continue
        ws=websocket.create_connection('wss://api.openai.com/v1/realtime?model='+model,
            header=['Authorization: Bearer '+key()],timeout=60)
        chunks=[];transcript='';usage=None;status=None;session=None
        def send(obj):ws.send(json.dumps(obj,ensure_ascii=False))
        def receive():
            event=json.loads(ws.recv())
            if event['type']=='error':
                err=event['error'];raise RuntimeError('OpenAI realtime error: '+str(err.get('code'))+' '+str(err.get('message')))
            return event
        try:
            while True:
                event=receive()
                if event['type']=='session.created':session=event['session']['id'];break
            send(dict(type='session.update',session=dict(type='realtime',model=model,
                output_modalities=['audio'],instructions=STYLE,
                audio=dict(input=dict(turn_detection=None),output=dict(format=dict(type='audio/pcm',rate=24000),voice=voice)))))
            while receive()['type']!='session.updated':pass
            send(dict(type='conversation.item.create',item=dict(type='message',role='user',content=[dict(type='input_text',text=text)])))
            send(dict(type='response.create',response=dict(output_modalities=['audio'])))
            deadline=time.monotonic()+120
            while time.monotonic()<deadline:
                event=receive();kind=event['type']
                if kind=='response.output_audio.delta':chunks.append(base64.b64decode(event['delta']))
                elif kind=='response.output_audio_transcript.done':transcript=event['transcript']
                elif kind=='response.done':
                    status=event['response']['status'];usage=event['response'].get('usage');break
            if status!='completed' or not chunks:raise RuntimeError('Audio generation did not complete: '+str(status))
        finally:ws.close()
        raw=b''.join(chunks)
        with wave.open(str(path),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(raw)
        info=dict(index=i,text=text,model=model,voice=voice,style=STYLE,session=session,
                  duration_s=len(raw)/48000,transcript=transcript,transcript_matches=norm(text)==norm(transcript),
                  usage=usage,file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        meta.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
        print(json.dumps(dict(index=i,duration_s=info['duration_s'],transcript=transcript,matches=info['transcript_matches']),ensure_ascii=False),flush=True)
        if not info['transcript_matches']:raise RuntimeError('Generated transcript differs; review before use')
        reports.append(info)
    (OUT/'generation_manifest.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['models','generate']);p.add_argument('--model',default='gpt-realtime-2.1-mini');p.add_argument('--voice',default='marin');a=p.parse_args()
    if a.mode=='models':models()
    else:generate(a.model,a.voice)
