"""Local Japanese narration and original music, synchronized to the new flights."""
import argparse,json,math,subprocess
from pathlib import Path
import numpy as np
from make_premium_video import wave_read,wave_write
from make_demo_video import FlightRecord
ROOT=Path(__file__).resolve().parent;TMP=ROOT/'tmp/rescue_presentation'
PLAN=json.loads((TMP/'plan.json').read_text(encoding='utf8'))
def narration():
    clips=[]
    def add(start,maximum,text,caption):clips.append(dict(index=len(clips),start=start,max_s=maximum,text=text,caption=caption,file=f'voice_{len(clips):02}.wav'))
    add(1,6,'言葉で指示する救助ドローンを、シミュレーションで作りました。','言葉で指示する救助ドローンを、シミュレーションで。')
    add(8.2,6.5,'カメラ映像から服の色を見分けて、その人の前まで飛びます。','服の色を見分けて、その人の前まで飛びます。')
    add(15.3,7.5,'画像と言葉から、ブイエルエーが次の動きを決めます。','VLAが、カメラ映像と言葉から次の動きを決めます。')
    add(23,4.7,'姿勢を安定させ、動いた結果を次の画像で確認します。','動いた結果をカメラで確認し、判断を繰り返します。')
    for f in PLAN['flights']:
        p=f['profile'];start=f['start'];end=f['end']
        if p=='blue':
            add(start+.8,6,'まずは離陸。青い服の人に近づき、その前で止まります。','青い服の人に近づき、その前で止まります。')
            if end-start>22:add(start+8,6.5,'右側は、実際にブイエルエーが見た画像です。左側は、同じ飛行を外から見た映像です。','右：VLAが見た画像　／　左：同じ飛行を外から見た映像')
            add(end-6.7,5.9,'人の前で三秒以上止まってから、着陸します。','人の前で3秒以上止まってから、着陸します。')
        elif p=='red':
            add(start+.8,7,'指示を赤い服の人に変えると、同じモデルが別の人に向かいます。','指示を変えると、向かう相手が変わります。')
            add(end-6.5,5.7,'赤い服の人の前でも止まりました。このあと着陸します。','赤い服の人の前で停止。このあと着陸します。')
        elif p=='turns':
            add(start+.8,6,'回転の指示にも対応します。右に九十度、次に左に九十度。','右に90度回って停止。続いて、左に90度回って停止。')
        else:add(start+.8,6,'左に九十度回る指示も、別の飛行で確認しました。','左回転のみの実験でも、離陸から着陸まで確認しました。')
    result=next(s['start'] for s in PLAN['timeline'] if s['name']=='results')
    add(result+.6,10,'四つの実験すべてで、離陸から着陸まで成功しました。停止時間と回転角は、シミュレーションの記録から確認しています。','4つの実験すべてで成功。停止時間と回転角も記録で確認。')
    hardware=next(s['start'] for s in PLAN['timeline'] if s['name']=='hardware')
    add(hardware+.4,6.2,'実機では、カメラ映像を無線で地上のパソコンへ送る想定です。','カメラ映像を、無線で地上PCへ送る想定です。')
    add(hardware+6.8,7,'ブイエルエーが動きを決め、コントローラーを通じて機体へ指令を返します。','VLAが動きを決め、コントローラーから機体へ指令を返します。')
    add(hardware+14,5.5,'この構成は設計段階です。実機での飛行はまだ行っていません。','実機化のための設計案です。実機飛行は今後の課題です。')
    add(hardware+20.5,8.9,'操縦から、言葉での指示へ。災害救助に向けた、最初の一歩です。','操縦から、言葉での指示へ。災害救助に向けた、最初の一歩。')
    clips.sort(key=lambda v:v['start'])
    assert all(a['start']+a['max_s']<=b['start'] for a,b in zip(clips,clips[1:])), 'Narration overlap'
    (TMP/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
def mix():
    sr=48000;duration=PLAN['duration_s'];n=round(sr*duration);music=np.zeros((n,2),np.float32);voice=np.zeros(n,np.float32);duck=np.ones(n,np.float32);rng=np.random.default_rng(20261026)
    def add(at,sound,gain,pan=0):
        a=round(at*sr);b=min(n,a+len(sound));sound=np.asarray(sound[:b-a],np.float32)
        if b>a:music[a:b,0]+=sound*gain*(1-.35*pan);music[a:b,1]+=sound*gain*(1+.35*pan)
    beat=60/92;bar=beat*4;chords=[(50,57,60,65),(46,53,58,62),(53,60,65,69),(48,55,60,64)]
    for k,start in enumerate(np.arange(0,duration,bar)):
        notes=chords[k%4];length=bar*1.75;t=np.arange(round(length*sr))/sr;env=np.minimum(1,t/.65)*np.minimum(1,(length-t)/1.6);pad=np.zeros_like(t)
        for midi in notes:
            hz=440*2**((midi-69)/12);pad+=(np.sin(2*np.pi*hz*t)+.3*np.sin(2*np.pi*hz*1.002*t)+.12*np.sin(2*np.pi*2*hz*t))/5.68
        add(start,pad*env,.1,.4*math.sin(k))
        for j in range(8):
            st=start+j*beat/2
            if st<8 or st>duration-5:continue
            hz=440*2**((notes[(j+k)%4]+12-69)/12);tt=np.arange(round(.65*sr))/sr
            add(st,(np.sin(2*np.pi*hz*tt)+.16*np.sin(2*np.pi*3*hz*tt))*np.exp(-tt*7)*np.minimum(tt/.008,1),.033,(-1)**j*.7)
    for k,st in enumerate(np.arange(15,duration-4,beat)):
        if k%2==0:
            tt=np.arange(round(.32*sr))/sr;add(st,np.sin(2*np.pi*(47*tt+1-np.exp(-tt*18)))*np.exp(-tt*16)*np.minimum(1,tt/.003),.05)
        tt=np.arange(round(.07*sr))/sr;noise=np.r_[0,np.diff(rng.normal(0,1,len(tt)))];add(st+beat/2,noise*np.exp(-tt*85)*np.minimum(1,tt/.002),.006,(-1)**k*.5)
    for section in PLAN['timeline'][1:]:
        at=section['start'];tt=np.arange(sr)/sr;noise=np.convolve(rng.normal(0,1,sr),np.ones(19)/19,'same');add(at-.6,noise*np.sin(np.pi*tt)**2,.06,-.3)
        tt=np.arange(round(.34*sr))/sr;add(at+.14,(np.sin(2*np.pi*880*tt)+.5*np.sin(2*np.pi*1320*tt))*np.exp(-tt*15)*np.minimum(tt/.006,1),.035,.3)
    for f in PLAN['flights']:
        r=FlightRecord(ROOT/PLAN['records']/f['profile']);wall=np.arange(round((f['end']-f['start'])*sr))/sr
        sim=np.minimum(f['sim_end'],f['sim_start']+np.maximum(0,wall-f['lead_s'])*f['speed']);duties=np.mean([row['motor_duty'] for row in r.rows],axis=1);duty=np.interp(sim,r.times,duties)
        phase=2*np.pi*np.cumsum(90+65*duty)/sr;add(f['start'],(np.sin(phase)+.2*np.sin(4.03*phase)+.1*np.sin(6.02*phase))*duty,.018,-.4)
    clips=json.loads((TMP/'narration_plan.json').read_text(encoding='utf8'))
    for clip in clips:
        sound=wave_read(TMP/clip['file']);original=len(sound)/sr
        if original>clip['max_s']:
            ratio=original/clip['max_s'];assert ratio<=1.32,(clip['index'],ratio)
            fitted=TMP/f'voice_{clip["index"]:02}_fit.wav';subprocess.run(['ffmpeg','-v','error','-y','-i',str(TMP/clip['file']),'-af',f'atempo={ratio:.8f}',str(fitted)],check=True);sound=wave_read(fitted)
        sound*=.66/max(.01,float(np.abs(sound).max()));a=round(clip['start']*sr);assert a+len(sound)<=n;voice[a:a+len(sound)]+=sound
        left=max(0,a-round(.25*sr));right=min(n,a+len(sound)+round(.4*sr));env=np.full(right-left,.42,np.float32);ramp=min(round(.25*sr),len(env));env[:ramp]=np.linspace(1,.42,ramp);ramp=min(round(.4*sr),len(env));env[-ramp:]=np.linspace(.42,1,ramp);duck[left:right]=np.minimum(duck[left:right],env)
        clip.update(duration_s=len(sound)/sr,original_duration_s=original)
    # Let the closing sentence finish at full narration level; fade the score separately.
    music[:sr]*=np.linspace(0,1,sr)[:,None];music[-2*sr:]*=np.linspace(1,0,2*sr)[:,None]
    master=music*duck[:,None]+voice[:,None]
    tail=round(.25*sr);assert all(c['start']+c['duration_s']<duration-.25 for c in clips)
    master[-tail:]*=np.linspace(1,0,tail)[:,None]
    peak=float(np.abs(master).max())
    if peak>.89:master*=.89/peak
    wave_write(TMP/'soundtrack.wav',master)
    (TMP/'voice_manifest.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
    (TMP/'audio_review.json').write_text(json.dumps(dict(duration_s=duration,sample_rate=sr,channels=2,voice='Microsoft Haruka Desktop, local SAPI',music='Original deterministic synthesis, seed 20261026',rotor='Designed texture follows actual recorded motor duty; not microphone sound',all_voices_fit=True,clipped_samples=int((np.abs(master)>=1).sum())),indent=2))
    print('CIVIC_AUDIO_COMPLETE',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['narration','mix']);args=p.parse_args();globals()[args.mode]()
