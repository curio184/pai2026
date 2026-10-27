"""Compose new recorded search flights; original camera pixels stay unchanged."""
import argparse
import bisect
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);sys.path.insert(0,str(ROOT))
import imageio.v2 as imageio
import numpy as np
from PIL import Image,ImageDraw
import make_premium_video as b
from rescue_presentation_cards import arrow,box
HERE=Path(__file__).resolve().parent;OUT=HERE/'movie'
BG='#091218';WHITE='#f4f4ee';MUTED='#b0bcc0';GOLD='#e9c78e';CYAN='#77d9ce'
PHASE={'takeoff':'離陸','hover':'捜索の準備','right':'室内を見渡す','confirm':'人物を確認','blue':'接近して停止','red':'接近して停止','report':'通知前の確認','reacquire':'停止して再確認','land':'着陸'}
CONDITION={'clear':'通常の見え方','fog_light':'薄い霧','fog_dense':'濃い霧','dust':'粉じん'}
def text(im,xy,s,size=28,color=WHITE,kind='jp'):b.txt(im,xy,s,size,color,kind)
def rect(im,xy,fill=BG,outline=None,r=0):b.rounded(im,xy,fill,outline,r)
def title(im,kicker,headline):
    text(im,(64,54),kicker,24,CYAN,'bold');text(im,(60,103),headline,54,WHITE,'bold')
def darken(im,alpha=.65):
    return Image.alpha_composite(im.convert('RGBA'),Image.new('RGBA',im.size,(4,11,17,round(alpha*255)))).convert('RGB')
def wrap(s,width,font):
    lines=[];line=''
    for c in s:
        if font.getlength(line+c)>width:lines.append(line);line=c
        else:line+=c
    if line:lines.append(line)
    return lines
class Record:
    def __init__(self,path):
        self.path=path
        self.rows=[json.loads(l) for l in (path/'trace.jsonl').read_text().splitlines()]
        self.times=[r['t'] for r in self.rows]
        self.packets=[e for e in json.loads((path/'vla_link_events.json').read_text()) if e.get('event')=='inference']
        self.score=json.loads((path/'search_score.json').read_text())
        self.result=json.loads((path/'result.json').read_text())
        self.inputs={}
        for p in self.packets:
            raw=(path/'observations'/p['image_file']).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==p['image_sha256']
            self.inputs[p['id']]=Image.open(path/'observations'/p['image_file']).convert('RGB')
    def at(self,t):
        index=max(0,bisect.bisect_right(self.times,t)-1);row=self.rows[index]
        # Use the packet actually applied/available in the recorded controller trace.
        candidates=[p for p in self.packets if row.get('model_capture_time') is not None and abs(p['sim_time_capture']-row['model_capture_time'])<1e-6]
        p=candidates[-1] if candidates else None
        return index,row,p,self.inputs[p['id']] if p else None
class Movie:
    def __init__(self,preview=False):
        self.plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'));self.preview=preview
        self.records={c:Record(Path(self.plan['records'])/(c+'_blue')) for c in CONDITION}
        self.voices=json.loads((OUT/'voice_manifest.json').read_text(encoding='utf8')) if (OUT/'voice_manifest.json').exists() else []
        self.used=set();self.metadata=[]
    def world(self,t=0):
        path=ROOT/'tmp/realism_movie/world_final'/f'{min(209,max(0,int(t*20))):04d}.jpg'
        return Image.open(path).convert('RGB')
    def external(self,name,index):
        folder=OUT/('preview' if self.preview else 'renders')/name
        file=folder/f'{index:04d}.jpg'
        if not file.exists() and self.preview:
            files=list(folder.glob('*.jpg'));file=min(files,key=lambda f:abs(int(f.stem)-index))
        if not self.preview:
            deadline=time.monotonic()+3600
            while not file.exists() or time.time()-file.stat().st_mtime<.3:
                if time.monotonic()>deadline:raise TimeoutError('Missing rendered frame: '+str(file))
                time.sleep(.25)
        return Image.open(file).convert('RGB')
    def title(self,t):
        im=darken(self.world(t),.56)
        rect(im,(65,208,73,716),GOLD)
        text(im,(102,220),'PHYSICAL AI  /  SIMULATION',25,GOLD,'en')
        text(im,(97,319),'災害救助ドローンの開発',82,WHITE,'bold')
        text(im,(104,466),'― VLAを用いた飛行制御のシミュレーション ―',35,WHITE)
        text(im,(104,650),'捜索を支援する、小型ドローンの自律飛行',30,MUTED)
        text(im,(104,900),'SmolVLA  ×  ArduPilot  ×  MuJoCo',25,GOLD,'en')
        return im
    def purpose(self,u):
        im=darken(self.world(u/2),.68)
        text(im,(78,90),'目的',25,CYAN,'bold')
        text(im,(72,205),'人が近づきにくい場所に、',64,WHITE,'bold')
        text(im,(72,300),'捜索の目を増やす。',74,WHITE,'bold')
        text(im,(80,477),'1機ずつ操縦する負担を減らし、',33,MUTED)
        text(im,(80,535),'任務を伝えて捜索を任せることを目指します。',33,MUTED)
        rect(im,(76,687,1815,891),'#14232b',r=16)
        text(im,(108,715),'今回の検証',27,CYAN,'bold')
        text(im,(108,770),'1機・1つの室内で、指定した人物の発見と画像の報告まで。',37,WHITE,'bold')
        text(im,(110,837),'複数機での捜索は将来の構想です。',25,MUTED)
        return im
    def mechanism(self,u):
        im=Image.new('RGB',(1920,1080),BG);title(im,'仕組み','任務を受け取り、画像を見ながら飛ぶ')
        rect(im,(65,220,1855,365),'#14232b',r=12)
        text(im,(88,242),'利用者の指示',23,CYAN,'bold');text(im,(88,285),'「青い服の人を探して」',36,WHITE,'bold')
        arrow(im,[(580,293),(740,293)],CYAN,min(1,u/2))
        text(im,(780,239),'任務の進行を管理するプログラム',29,WHITE,'bold')
        text(im,(780,296),'捜索 → 人物の確認 → 接近 → 画像付き通知',30,MUTED)
        records=self.records['clear'];p=next(p for p in records.packets if p['sim_time_capture']>=records.score['discovery_time_s'])
        im.paste(records.inputs[p['id']].resize((384,288),Image.Resampling.NEAREST),(65,435))
        text(im,(65,752),'人物検出 ＋ 服の色の確認',27,CYAN,'bold')
        text(im,(65,798),'複数の画像で対象を確認',25,MUTED)
        rect(im,(650,435,1225,839),'#14232b',CYAN,14)
        text(im,(685,467),'SmolVLA',45,WHITE,'en')
        text(im,(685,540),'カメラ画像・工程の指示・機体の状態',25,WHITE)
        text(im,(685,600),'数秒分の飛行動作をまとめて生成',29,WHITE,'bold')
        for i in range(32):
            x=689+i*15;rect(im,(x,669,x+9,710),CYAN if i<int(u*5)%33 else '#325057',r=2)
        text(im,(685,764),'32ステップ・3.2秒分（概念図）',25,MUTED)
        rect(im,(1410,435,1855,839),'#14232b',GOLD,14)
        text(im,(1440,473),'飛行制御',38,GOLD,'bold')
        text(im,(1440,554),'ArduPilot',30,WHITE,'en')
        text(im,(1440,600),'姿勢を安定させる',26,WHITE)
        text(im,(1440,686),'MuJoCo',30,WHITE,'en')
        text(im,(1440,733),'機体の運動を物理計算',26,WHITE)
        arrow(im,[(470,550),(650,550)],CYAN,min(1,u/3))
        arrow(im,[(1225,550),(1410,550)],GOLD,min(1,u/4))
        arrow(im,[(1620,840),(1620,887),(240,887),(240,840)],GOLD,min(1,u/6))
        text(im,(65,919),'VLAへの工程指示は英語・日本語を併記。捜索の手順と発見判定はプログラムが管理します。',23,MUTED)
        return im
    def flight(self,name,u,condition=False):
        seg=next(s for s in self.plan['segments'] if s['name']==name)
        c=seg['condition'];r=self.records[c]
        index=min(round(seg['duration_s']*30)-1,max(0,round(u*30)))
        moment=min(seg['sim_end'],seg['sim_start']+u*2)
        _,row,packet,onboard=r.at(moment)
        im=Image.new('RGB',(1920,1080),BG)
        text(im,(48,25),'視覚条件を変えた検証' if condition else '捜索の指示',24,CYAN,'bold')
        text(im,(48,68),CONDITION[c] if condition else '「青い服の人を探して」',49,WHITE,'bold')
        text(im,(50,134),PHASE[row['phase']],28,GOLD,'bold')
        playback='飛行終了・静止画' if moment>=seg['sim_end'] else ('抜粋・' if condition else '')+'2倍速'
        text(im,(1308,31),'シミュレーション・'+playback,23,CYAN)
        text(im,(1308,77),f'飛行記録  {row["t"]:.1f} 秒',26,MUTED)
        im.paste(self.external(name,index).resize((1216,760),Image.Resampling.LANCZOS),(48,192))
        rect(im,(48,192,1264,232),'#102027')
        text(im,(64,196),'飛行記録から再描画した外部視点',22,MUTED)
        rect(im,(1308,192,1872,952),'#14232b',r=14)
        text(im,(1332,211),'VLAに入力された画像',28,WHITE,'bold')
        if onboard is not None:
            im.paste(onboard.resize((512,384),Image.Resampling.NEAREST),(1332,266))
            self.used.add((c,packet['image_file'],packet['image_sha256']))
        text(im,(1332,670),f'撮影から {row["t"]-packet["sim_time_capture"]:.2f} 秒' if packet else '画像の受信待ち',22,MUTED)
        found=row['t']>=r.score['discovery_time_s'];reported=row['t']>=r.score['notification_time_s']
        b.line(im,[(1332,716),(1844,716)],'#42545c',1)
        if condition:
            text(im,(1332,738),'この条件での飛行全体',25,MUTED)
            text(im,(1332,784),'発見・画像通知・着陸を確認',27,CYAN,'bold')
            text(im,(1332,838),f'停止 {r.score["physical"]["goal_holds"]["blue"]["physical_hold"]["duration_s"]:.2f} 秒',31,WHITE,'bold')
            text(im,(1332,902),'各条件1回・同じモデルで検証',23,MUTED)
        else:
            text(im,(1332,738),'画像を地上PCに記録' if reported else '指定した人物を確認' if found else '視野を確認中',29,CYAN if found else WHITE,'bold')
            text(im,(1332,796),'青い服の人物',27,WHITE)
            text(im,(1332,845),'画像付き通知を記録済み' if reported else '接近・停止を確認中' if found else '複数の画像で確認します',25,MUTED)
            text(im,(1332,902),'モーター停止' if row['t']>=seg['sim_end']-.04 else f'高度 {-row["truth"][3]:.2f} m',25,WHITE)
        if reported and not condition:
            # Actual local notification record; never substitute a better-looking face image.
            rect(im,(72,252,736,502),'#102027',CYAN,10)
            im.paste(Image.open(r.path/'notification.jpg').resize((288,216),Image.Resampling.NEAREST),(88,269))
            text(im,(399,282),'画像付き通知',31,CYAN,'bold')
            text(im,(399,340),'青い服の人物を確認',24,WHITE)
            text(im,(399,392),'服の色を確認した画像',21,MUTED)
            text(im,(399,434),'地上PC内に保存',22,MUTED)
        if not condition and not found and row['phase'] in ('hover','right','confirm') and onboard is not None:
            # During search, the actual visual observation is the principal view.
            rect(im,(0,184,1920,970),BG)
            im.paste(onboard.resize((896,672),Image.Resampling.NEAREST),(48,260))
            text(im,(48,205),'VLAに入力された画像',29,CYAN,'bold')
            im.paste(self.external(name,index).resize((884,553),Image.Resampling.LANCZOS),(988,260))
            text(im,(988,205),'同じ飛行の外部視点',28,WHITE,'bold')
            text(im,(988,839),'カメラの向きを変えて、室内を確認',27,WHITE)
            text(im,(988,893),'画像から人物と服の色を確認しています',25,MUTED)
        return im
    def hardware(self,u):
        im=Image.new('RGB',(1920,1080),BG);title(im,'実機に向けた構成案','カメラ映像と飛行指令を、無線で送受信')
        rect(im,(65,262,625,828),'#14232b',r=18)
        text(im,(94,294),'機体：StampFly',35,WHITE,'bold')
        # Existing model image is explicitly an illustration of a proposed assembly.
        try:
            studio=b.studio('hero')
            im.paste(studio.crop((650,180,2380,1300)).resize((490,318),Image.Resampling.LANCZOS),(100,367))
            text(im,(110,689),'構成イメージ（CG）',18,MUTED)
        except Exception:
            text(im,(110,480),'小型機 ＋ カメラ・無線',30,WHITE)
        text(im,(94,716),'機体側で姿勢を安定化',27,MUTED)
        text(im,(94,771),'実在する機体を基に設計',25,WHITE)
        rect(im,(980,262,1855,828),'#14232b',r=18)
        text(im,(1010,296),'地上のGPU搭載PC',35,WHITE,'bold')
        box(im,(1020,439,1360,694),'コントローラー',['画像と状態を受信','飛行指令を送信'],title_size=27)
        box(im,(1490,439,1815,694),'VLA',['画像・指示・状態から','動作を生成'],title_size=34)
        text(im,(1010,367),'利用者が任務を伝える → プログラムが進行を管理',25,MUTED)
        arrow(im,[(625,455),(815,455),(815,505),(1020,505)],CYAN,min(1,u/4))
        text(im,(663,354),'無線で送信',27,CYAN,'bold');text(im,(663,401),'画像・機体の状態',24,CYAN)
        arrow(im,[(1020,638),(810,638),(810,720),(625,720)],GOLD,min(1,u/5))
        text(im,(665,760),'飛行指令を返信',26,GOLD,'bold')
        arrow(im,[(1360,505),(1490,505)],CYAN,min(1,u/6))
        arrow(im,[(1490,638),(1360,638)],GOLD,min(1,u/7))
        text(im,(1010,757),'コントローラーとVLAは、同じPC上のソフトです。',24,MUTED)
        text(im,(65,867),'カメラ・無線の候補：XIAO ESP32S3 Sense　／　位置推定用センサーも構成案に含めます。',24,WHITE)
        text(im,(65,919),'実在する部品を基にした設計案です。搭載・電源・通信・実機での飛行は未検証です。',25,MUTED)
        return im
    def closing(self,u):
        im=darken(self.world(7),.7)
        text(im,(78,118),'今回の到達点',27,GOLD,'bold')
        text(im,(72,224),'見えていない人を探し、',68,WHITE,'bold')
        text(im,(72,322),'確認した画像を届ける。',68,WHITE,'bold')
        text(im,(80,497),'1つの室内・4つの視覚条件で、捜索から着陸まで確認。',33,WHITE)
        text(im,(80,584),'霧・粉じんは描画上の条件です。実環境での耐性は未検証です。',27,MUTED)
        text(im,(80,710),'次の課題：場所や人物を変えた検証、実機での確認',30,MUTED)
        text(im,(80,886),'人物・背景素材：MakeHuman / Poly Haven（CC0）',22,MUTED)
        return im
    def frame(self,t):
        section=next(s for s in self.plan['timeline'] if s['start']<=t<s['end']);name=section['name'];u=t-section['start']
        if name=='demo':im=self.flight('demo',u)
        elif name=='conditions':im=self.flight(['fog_light','fog_dense','dust'][min(2,int(u/8))],u%8,True)
        else:im=getattr(self,name)(u)
        rect(im,(0,970,1920,1080),BG)
        clip=next((v for v in self.voices if v['start']<=t<v['start']+v['duration_s']+.1),None)
        if clip:
            lines=wrap(clip['caption'],1790,b.font(28,'bold'));assert len(lines)<=2
            for i,line in enumerate(lines):text(im,((1920-b.font(28,'bold').getlength(line))/2,976+i*34),line,28,WHITE,'bold')
        b.line(im,[(48,1055),(1872,1055)],'#334750',1)
        b.line(im,[(48,1055),(48+1824*t/self.plan['duration_s'],1055)],GOLD,2)
        return im
def main(args):
    movie=Movie(args.mode=='preview')
    if args.mode=='preview':
        times=[s['start']+(s['end']-s['start'])/2 for s in movie.plan['timeline']]
        demo=next(s for s in movie.plan['timeline'] if s['name']=='demo')
        times += [demo['start']+1,demo['end']-3]
        for i,t in enumerate(times):movie.frame(t).save(OUT/f'composite_{i:02}.jpg',quality=95)
        (OUT/'composite_times.json').write_text(json.dumps(times));return
    target=OUT/'search_presentation_silent.mp4';assert not target.exists()
    os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg';started=time.monotonic()
    with imageio.get_writer(target,fps=30,codec='h264_nvenc',macro_block_size=1,ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p','-movflags','+faststart'],ffmpeg_log_level='error') as writer:
        for i in range(movie.plan['frames']):
            writer.append_data(np.asarray(movie.frame(i/30)))
            if i%180==0:print('SEARCH_COMPOSITE',i,movie.plan['frames'],round(time.monotonic()-started,1),flush=True)
    (OUT/'composite_evidence.json').write_text(json.dumps(dict(inputs=[dict(condition=c,file=f,sha256=h) for c,f,h in sorted(movie.used)],source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preview','render']);main(p.parse_args())
