"""Compose verified rich-world renders with untouched recorded policy JPEGs."""
import argparse,json,math,time
from pathlib import Path
import imageio.v2 as imageio
import numpy as np
from PIL import Image,ImageDraw
import make_premium_video as base
from rescue_presentation_cards import PresentationCards, localize_base
localize_base(base)
ROOT=base.ROOT;TMP=ROOT/'tmp/rescue_presentation';RENDER=ROOT/'tmp/realism_movie';OUT=ROOT/'output/video'
PLAN=json.loads((TMP/'plan.json').read_text(encoding='utf8'))
base.RECORDS=ROOT/PLAN['records'];base.CHECKPOINT=PLAN['checkpoint_sha256'];base.DURATION=PLAN['duration_s'];base.TIMELINE=[(v['name'],v['start'],v['end']) for v in PLAN['timeline']]

class NoView:
    def close(self):pass
class Production(PresentationCards,base.Production):
    def __init__(self,preview=False):
        original=base.CinematicView
        try:base.CinematicView=NoView;super().__init__()
        finally:base.CinematicView=original
        self.preview=preview
        self.voices=json.loads((TMP/'voice_manifest.json').read_text(encoding='utf8')) if (TMP/'voice_manifest.json').exists() else []
        self.projection=json.loads((RENDER/'projection.json').read_text()) if (RENDER/'projection.json').exists() else {}
    def image(self,profile,i):
        path=RENDER/profile/f'{i:04d}.jpg'
        if not path.exists() and self.preview:
            files=list((RENDER/'preview'/profile).glob('*.jpg')) or list((RENDER/profile).glob('*.jpg'));path=min(files,key=lambda p:abs(int(p.stem)-i))
        return Image.open(path).convert('RGB')
    def flight(self,t,p,start,end):
        f=next(f for f in PLAN['flights'] if f['profile']==p);local=t-start
        moment=min(f['sim_end'],f['sim_start']+max(0,local-f['lead_s'])*f['speed'])
        index,row,packet,onboard=self.records[p].at(moment)
        image_index=min(round((end-start)*30)-1,max(0,round(local*30)))
        im=self.image(p,image_index)
        if p in self.projection:
            info=self.projection[p][image_index];assert info['row_index']==index
        else:info=None
        overlay=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(overlay)
        d.rectangle((0,0,1920,176),fill=(5,13,20,225));d.rectangle((0,850,1920,1080),fill=(5,13,20,239))
        d.rounded_rectangle((1340,202,1852,824),radius=18,fill=(5,13,20,238),outline=(75,100,112,255),width=1)
        im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')
        color=base.BLUE if p=='blue' else base.RED if p=='red' else base.CYAN
        number={'blue':'01','red':'02','turns':'03','left':'04'}[p]
        mission={'blue':'青い服の人を探して','red':'赤い服の人を探して'}
        if p in mission:base.txt(im,(62,25),f'実演 {number}：'+mission[p],22,color,'bold')
        else:base.txt(im,(62,25),f'実演 {number}：回転の指示',22,color,'en')
        base.txt(im,(58,72),base.LABELS[row['phase']],48,base.WHITE,'bold')
        base.txt(im,(64,139),'いま実行している指示',20,base.MUTED)
        base.pill(im,(1360,30),f'シミュレーション映像・{f["speed"]:g}倍速',base.CYAN,20,450)
        base.txt(im,(1360,89),f'経過時間  {row["t"]:06.2f} 秒',29,base.WHITE,'en')
        base.txt(im,(1360,137),'離陸から着陸までを続けて再生',20,base.MUTED)
        base.txt(im,(1362,219),'VLAが見ている画像',22,base.CYAN,'en')
        if onboard is not None:
            im.paste(onboard.resize((448,336),Image.Resampling.NEAREST),(1372,262))
            self.inputs_verified.add((p,packet['image_file'],packet['image_sha256']))
        else:base.txt(im,(1420,420),'入力の受信待ち',25,base.MUTED)
        base.txt(im,(1373,612),'実際に入力したカメラ画像',19,base.MUTED)
        age=row['t']-packet['sim_time_capture'] if packet else 0
        base.txt(im,(1373,647),f'撮影からの経過  {age:.2f} 秒',18,base.GOLD,'en')
        base.line(im,[(1372,686),(1820,686)],base.LINE)
        base.txt(im,(1373,704),'VLAが出した速度指令（m/s）',17,base.MUTED,'en')
        for j,(label,value) in enumerate(zip(['前へ','左へ','上へ'],row['model_action'][:3])):
            x=1373+j*151;base.txt(im,(x,735),label,16,base.MUTED,'en');base.txt(im,(x,762),f'{value:+.2f}',32,base.WHITE,'en')
        if info and row['phase'] in ['blue','red']:
            d=ImageDraw.Draw(im)
            visible=[tuple(v) for v in info['trail'] if 10<v[0]<1305 and 185<v[1]<835]
            if len(visible)>1:d.line(visible,fill=base.CYAN,width=2)
            x,y=info['projected']
            if 30<x<1270 and 202<y<820:
                d.ellipse((x-17,y-17,x+17,y+17),outline=base.CYAN,width=2)
                base.pill(im,(max(40,min(1110,x+25)),y-18),'STAMPFLY',base.CYAN,16,142)
        alt=-row['truth'][3];speed=np.linalg.norm(row['truth'][4:6])
        base.txt(im,(64,872),f'高度  {alt:.2f} m',27,base.WHITE,'en')
        base.txt(im,(340,872),f'水平速度  {speed:.2f} m/s',27,base.WHITE,'en')
        if p in ['blue','red']:
            goal=self.records[p].score['goal_holds'][p]['goal_scene_xy_m'];distance=np.linalg.norm(np.array([row['truth'][2],row['truth'][1]])-goal)
            held=self.streaks[p][index]
            if row['phase']=='land':held=self.records[p].score['goal_holds'][p]['physical_hold']['duration_s']
            base.txt(im,(740,872),f'目標まで  {distance:.2f} m',27,base.WHITE,'en')
            base.txt(im,(1110,872),f'停止時間  {held:.2f} 秒',27,base.CYAN if held>=3 else base.WHITE,'en')
        elif row['phase'] in ['right','left']:
            startidx=np.searchsorted(self.records[p].times,self.phase_begin[p][row['phase']]);delta=math.degrees(self.yaws[p][index]-self.yaws[p][startidx])
            base.txt(im,(760,872),f'回転角  {delta:+.1f}°',27,base.CYAN,'en')
            base.txt(im,(1280,872),f'回転の指令  {math.degrees(row["model_action"][3]):+.1f}°/秒',24,base.WHITE,'en')
        base.txt(im,(65,925),'左：飛行記録をもとに描いた映像　／　右：実際の入力画像　／　数値：シミュレーションの記録',18,base.MUTED)
        done=moment>=f['sim_end']
        if done:
            base.rounded(im,(120,335,950,478),'#092b2c',base.CYAN,18,2)
            base.txt(im,(150,352),'飛行終了',28,base.CYAN,'en')
            base.txt(im,(150,403),'着陸し、モーターが停止しました',32,base.WHITE,'bold')
        base.footer(im,t,'Flight '+number,'RECORDED VLA + PHYSICS / SAME OPTICAL WORLD');return im
    def results(self,t):
        im=base.base().copy();base.txt(im,(72,77),'実験結果',23,base.CYAN,'en')
        base.txt(im,(68,130),'4つの実験すべてで成功しました',56,base.WHITE,'bold')
        a=self.records['blue'].score;b=self.records['red'].score;c=self.records['turns'].score;e=self.records['left'].score
        info=[('実験 01','青い服の人',f'{a["goal_holds"]["blue"]["physical_hold"]["duration_s"]:.2f} 秒','人の前で停止',base.BLUE),('実験 02','赤い服の人',f'{b["goal_holds"]["red"]["physical_hold"]["duration_s"]:.2f} 秒','人の前で停止',base.RED),('実験 03','右回転 → 左回転',f'{c["rotations"]["right"]["clockwise_rotation_deg"]:+.1f}° / {c["rotations"]["left"]["clockwise_rotation_deg"]:+.1f}°','左右に回転し、それぞれ停止',base.CYAN),('実験 04','左回転のみ',f'{e["rotations"]["left"]["clockwise_rotation_deg"]:+.1f}°','回転後に停止',base.CYAN)]
        for i,(eng,title,value,sub,color) in enumerate(info):
            x=72+i%2*912;y=260+i//2*275;base.rounded(im,(x,y,x+864,y+249),base.PANEL,base.LINE,20)
            base.txt(im,(x+28,y+20),eng,23,color,'en');base.pill(im,(x+685,y+18),'成功',color,19,150)
            base.txt(im,(x+28,y+69),title,27,base.WHITE,'bold');base.txt(im,(x+28,y+118),value,55 if i!=2 else 46,color,'en');base.txt(im,(x+28,y+196),sub,22,base.MUTED)
        base.txt(im,(77,846),'すべての実演で、離陸から着陸・モーター停止まで完了',29,base.WHITE,'bold')
        base.txt(im,(77,904),'停止の判定：目標から25 cm以内で、水平速度0.08 m/s以下を3秒以上維持',24,base.MUTED)
        base.footer(im,t,'Results','INDEPENDENT PHYSICAL LOG SCORING');return im

def main(mode):
    prod=Production(preview=mode=='preview')
    if mode=='preview':
        times=[2,10,20]+[f['start']+(f['end']-f['start'])*.5 for f in PLAN['flights']]+[next(s['start'] for s in PLAN['timeline'] if s['name']=='results')+3,PLAN['duration_s']-25,PLAN['duration_s']-5]
        for i,t in enumerate(times):prod.frame(t).save(TMP/f'composite_{i:02}.jpg',quality=95)
        return
    output=OUT/'rescue_drone_presentation_silent.mp4'
    if output.exists():raise FileExistsError(output)
    at=time.monotonic()
    with imageio.get_writer(output,fps=30,codec='libx264',macro_block_size=1,ffmpeg_params=['-crf','17','-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart'],ffmpeg_log_level='error') as writer:
        for i in range(PLAN['frames']):
            writer.append_data(np.asarray(prod.frame(i/30)))
            if i%150==0:print('CIVIC_COMPOSITE',i,PLAN['frames'],round(time.monotonic()-at,1),flush=True)
    meta=dict(**PLAN,output='rescue_drone_presentation.mp4',recorded_inputs=[dict(profile=p,file=f,sha256=h) for p,f,h in sorted(prod.inputs_verified)],presentation_only=['External viewpoint and motion graphics','Studio opening/closing','Synthesized narration, music and rotor texture'],runtime_images='Original recorded JPEGs, hash-verified, pixel-preserving nearest-neighbor enlargement',source_sha256={name:base.sha(ROOT/name) for name in ['compose_rescue_presentation.py','rescue_presentation_cards.py','render_realism_movie.py','plan_realism_movie.py']})
    (OUT/'rescue_drone_presentation.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf8');prod.close();print('CIVIC_COMPOSITE_COMPLETE',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preview','render']);main(p.parse_args().mode)
