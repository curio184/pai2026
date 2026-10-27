"""Hardware proposal and closing, following the approved visual and narration style."""
import os,sys,json,hashlib,subprocess,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import imageio.v2 as imageio
from demo_movie import ROOT,HERE,BG,WHITE,MUTED,CYAN,GOLD,LINE,font,text,sha,smooth
OUT=HERE/'ending_movie';OUT.mkdir(exist_ok=True)
FPS=24;DURATION=30;STARTS=[.6,9.3,15.6,22.2]
DEST=ROOT/'output/video/rescue_drone_ending.mp4'
PARTS=[ROOT/'output/video/rescue_drone_intro_mechanism_demo.mp4',ROOT/'output/video/rescue_drone_red_search.mp4',ROOT/'output/video/rescue_drone_visual_conditions.mp4']
PREFIX=ROOT/'output/video/rescue_drone_with_red_search.mp4'
COMBINED=ROOT/'output/video/rescue_drone_final.mp4'
CAPTIONS=[['実機への展開を見据え、実在する小型ドローンとカメラ、',
           '制御用パソコンを組み合わせる構成を検討しています。'],
 ['搭載や通信、実機での飛行は、今後の検証課題です。'],
 ['今回は、指定した人物を探し、','確認画像を保存するまでを実現しました。'],
 ['今後は、環境を変えた検証と、実機での確認を進めます。']]

def hardware():
 im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
 text(im,96,100,'実機への展開',56,WHITE,550)
 text(im,1824,118,'構成案',27,GOLD,500,anchor='rt')
 centers=[360,960,1560]
 for x,s in zip(centers,['機体','カメラ・無線','制御用PC']):text(im,x,278,s,30,MUTED,500,anchor='mt')
 studio=Image.open(ROOT/'tmp/premium/opening/0060.jpg').convert('RGB')
 drone=studio.crop((620,155,1700,1000)).resize((510,399),Image.Resampling.LANCZOS)
 # Retain the established studio drone image, fading the rectangular edges.
 yy,xx=np.mgrid[0:399,0:510]
 alpha=np.minimum.reduce([np.clip(yy/40,0,1),np.clip((398-yy)/45,0,1),np.clip(xx/30,0,1),np.clip((509-xx)/30,0,1)])
 blend=np.asarray(drone)*alpha[:,:,None]+np.array([9,19,25])*(1-alpha[:,:,None])
 im.paste(Image.fromarray(blend.astype('uint8')),(105,338))
 # Generic symbols denote component roles, not exact product dimensions.
 d.rounded_rectangle((831,425,1089,597),radius=17,outline=CYAN,width=4)
 d.line((858,424,883,397,948,397,970,424),fill=CYAN,width=4)
 for radius,width in [(56,4),(39,2)]:d.ellipse((960-radius,511-radius,960+radius,511+radius),outline=CYAN,width=width)
 d.ellipse((1052,446,1064,458),fill=CYAN)
 for dy in [0,19]:d.arc((1038,366-dy,1108+dy,436),200,330,fill=MUTED,width=2)
 d.rounded_rectangle((1410,403,1710,595),radius=8,outline=CYAN,width=4)
 d.line((1560,596,1560,633),fill=CYAN,width=4);d.line((1485,637,1635,637),fill=CYAN,width=4)
 text(im,1560,485,'SmolVLA',34,WHITE,500,anchor='mt')
 text(im,660,493,'＋',38,MUTED,400,anchor='mt')
 d.line((1177,511,1302,511),fill=CYAN,width=3)
 d.polygon([(1302,511),(1288,504),(1288,518)],fill=CYAN)
 d.polygon([(1177,511),(1191,504),(1191,518)],fill=CYAN)
 text(im,1240,546,'無線通信',23,MUTED,400,anchor='mt')
 text(im,360,731,'StampFly',34,WHITE,500,anchor='mt')
 text(im,960,731,'XIAO ESP32S3 Sense',29,WHITE,500,anchor='mt')
 text(im,1560,731,'GPU搭載PC',34,WHITE,500,anchor='mt')
 text(im,360,785,'実在する小型ドローン',24,MUTED,anchor='mt')
 text(im,960,785,'追加カメラの候補',24,MUTED,anchor='mt')
 text(im,1560,785,'VLAと制御プログラムを実行',24,MUTED,anchor='mt')
 text(im,960,856,'位置推定用センサー・電源回路も追加する想定',24,MUTED,anchor='mt')
 text(im,960,907,'搭載・電源・通信・実機飛行は未検証',24,GOLD,anchor='mt')
 return im

class Movie:
 def __init__(self):
  self.hardware=hardware();self.voices=json.loads((OUT/'voice_manifest.json').read_text(encoding='utf8'));self.metadata=[]
  self.poses=json.loads((HERE/'movie/renders/demo/poses.json').read_text())
  # Full-height recorded view, with a side gradient rather than cropping heads or feet.
  yy,xx=np.mgrid[0:1080,0:1920]
  opacity=.64*(1-np.clip(xx/1500,0,1))+.12
  opacity=np.maximum(opacity,np.clip((yy-850)/230,0,1)*.65)
  opacity=np.maximum(opacity,np.clip((340-xx)/148,0,1))
  self.shade=np.clip(opacity,0,1)[:,:,None]
 def frame(self,t,log=False):
  if t<15:
   im=self.hardware.copy();meta=dict(video_time_s=t,kind='hardware_proposal')
   if t<.4:im=Image.blend(Image.new('RGB',im.size),im,smooth(t/.4))
   if t>14.7:im=Image.blend(im,Image.new('RGB',im.size),smooth((t-14.7)/.3))
  else:
   u=t-15
   # Six recorded flight seconds played slowly for an editorial closing, not a new trial.
   idx=540+min(90,int(max(0,u)/12*90));source=HERE/'movie/renders/demo'/f'{idx:04d}.jpg'
   bg=Image.new('RGB',(1920,1080),BG)
   bg.paste(Image.open(source).convert('RGB').resize((1728,1080),Image.Resampling.LANCZOS),(192,0))
   values=np.asarray(bg)*(1-self.shade)+np.array([9,19,25])*self.shade
   im=Image.fromarray(values.astype('uint8'))
   text(im,96,194,'災害救助ドローン',29,CYAN,500)
   text(im,91,298,'言葉による指示で、',64,WHITE,550)
   text(im,91,389,'被災者の捜索を支援',64,WHITE,550)
   meta=dict(video_time_s=t,kind='closing',external_frame=idx,simulation_time=self.poses[idx]['simulation_time'],editorial_slow_playback=True)
   if u<.4:im=Image.blend(Image.new('RGB',im.size),im,smooth(u/.4))
  for i,v in enumerate(self.voices):
   if v['start']<=t<v['start']+v['duration_s']+.12:
    lines=CAPTIONS[i]
    for j,line in enumerate(lines):
     assert font(31).getlength(line)<1740
     y=1007 if len(lines)==1 else 981+j*43
     text(im,960,y,line,31,WHITE,450,anchor='mt')
  if t>DURATION-1.1:im=Image.blend(im,Image.new('RGB',im.size),smooth((t-DURATION+1.1)/1.1))
  if log:self.metadata.append(meta)
  return im

def audio():
 import make_rescue_presentation_audio as original
 generated=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'));clips=[]
 for i,(g,at) in enumerate(zip(generated,STARTS)):
  assert g['transcript_matches'] and ''.join(CAPTIONS[i])==g['text'] and sha(OUT/g['file'])==g['sha256']
  clips.append(dict(index=i,start=at,max_s=g['duration_s']+.1,text=g['text'],caption=g['text'],file=g['file']))
 assert all(a['start']+a['max_s']<b['start'] for a,b in zip(clips,clips[1:]))
 assert clips[-1]['start']+clips[-1]['max_s']<DURATION-1.1
 (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
 original.TMP=OUT;original.PLAN=dict(duration_s=DURATION,flights=[],timeline=[dict(start=0)]);original.mix()
 review=json.loads((OUT/'audio_review.json').read_text());review.update(voice='OpenAI gpt-realtime-2.1-mini / marin',rotor='None',time_stretch_used=False)
 (OUT/'audio_review.json').write_text(json.dumps(review,indent=2))
 with wave.open(str(OUT/'dry_narration.wav'),'wb') as dst:
  dst.setnchannels(1);dst.setsampwidth(2);dst.setframerate(24000)
  for i in range(4):
   with wave.open(str(OUT/f'voice_{i:02}.wav'),'rb') as src:dst.writeframes(src.readframes(src.getnframes()))
   dst.writeframes(bytes(24000))

def preview():
 m=Movie();sheet=Image.new('RGB',(1280,780),BG)
 for i,t in enumerate([4,11,18,26]):
  im=m.frame(t);im.save(OUT/f'preview_{i:02}.png');x=i%2*640;y=i//2*390
  text(sheet,x+10,y+4,f'{t:.1f} s',19);sheet.paste(im.resize((640,360)),(x,y+30))
 sheet.save(OUT/'preview_sheet.jpg',quality=95)

def join(paths,durations,dest,name):
 listing=OUT/(name+'.ffconcat')
 listing.write_text('ffconcat version 1.0\n'+''.join("file '"+str(p.resolve()).replace('\\','/')+"'\n" for p in paths),encoding='utf8')
 args=['ffmpeg','-v','warning','-y','-f','concat','-safe','0','-i',str(listing)]
 for p in paths:args+=['-i',str(p)]
 filters=';'.join(f'[{i+1}:a]atrim=duration={d},asetpts=PTS-STARTPTS[a{i}]' for i,d in enumerate(durations))+';'+''.join(f'[a{i}]' for i in range(len(paths)))+f'concat=n={len(paths)}:v=0:a=1[a]'
 args+=['-filter_complex',filters,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-ar','96000','-movflags','+faststart','-t',str(sum(durations)),str(dest)]
 subprocess.run(args,check=True)

def render():
 m=Movie();os.environ['IMAGEIO_FFMPEG_EXE']='ffmpeg'
 with imageio.get_writer(OUT/'silent.mp4',fps=FPS,codec='h264_nvenc',macro_block_size=1,ffmpeg_params=['-cq','18','-preset','p5','-pix_fmt','yuv420p'],ffmpeg_log_level='error') as w:
  for i in range(DURATION*FPS):
   w.append_data(np.asarray(m.frame(i/FPS,log=True)))
   if i%120==0:print('ENDING_FRAME',i,flush=True)
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','96000','-af','loudnorm=I=-16:TP=-2:LRA=7','-movflags','+faststart','-t',str(DURATION),str(DEST)],check=True)
 before={str(p):sha(p) for p in PARTS}
 join(PARTS,[92,26,27],PREFIX,'corrected_prefix')
 join(PARTS+[DEST],[92,26,27,DURATION],COMBINED,'final')
 assert all(sha(Path(p))==v for p,v in before.items())
 (OUT/'frames.json').write_text(json.dumps(m.metadata,separators=(',',':')))
 evidence=dict(duration_s=DURATION,fps=FPS,combined_duration_s=175,section_boundaries_s=[0,15,30],source_segments_sha256=before,hardware_design_sha256=sha(ROOT/'hardware_design.json'),hardware_is_proposal_only=True,closing_source='Recorded clear-blue flight frames 540–630; slowed editorial reprise',closing_narration_end_s=27.3,music_only_tail_s=2.7,powder_reading='ふんじん',powder_voice_source=str(HERE/'conditions_movie/funjin_revision02/voice_00.json'),no_new_hardware_claim=True)
 (OUT/'source_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
 print('FINAL_MOVIE_COMPLETE',COMBINED,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
