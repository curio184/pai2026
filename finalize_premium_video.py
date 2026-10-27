"""Master, decode, and prepare visual review of the rich video; local files only."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
TMP=ROOT/'tmp/premium';OUT=ROOT/'output/video'

def run(args):
    proc=subprocess.run(args,capture_output=True)
    if proc.returncode:
        raise RuntimeError(f'Process failed ({proc.returncode}): {args[0]}\n'+proc.stderr.decode('utf8',errors='replace')[-7000:])
    return proc

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def loudness(path):
    p=run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-16:TP=-2:LRA=10:print_format=json','-f','null','-'])
    log=p.stderr.decode('utf8',errors='replace')
    obj=re.findall(r'\{\s*"input_i"[\s\S]*?\}',log)
    if not obj:raise ValueError('Missing loudness measurements')
    return json.loads(obj[-1])

def stamp(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def main():
    output=OUT/'rescue_drone_premium.mp4'
    if output.exists():raise FileExistsError(output)
    meta=json.loads((OUT/'rescue_drone_premium.json').read_text(encoding='utf8'))
    before=loudness(TMP/'soundtrack.wav')
    af=('loudnorm=I=-16:TP=-2:LRA=10:measured_I={input_i}:measured_TP={input_tp}:'
        'measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:'
        'linear=false:print_format=json').format(**before)
    proc=run(['ffmpeg','-hide_banner','-y','-i',str(OUT/'rescue_drone_premium_silent.mp4'),
         '-i',str(TMP/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af',af,
         '-c:a','aac','-b:a','256k','-ar','48000','-t','158','-movflags','+faststart',
         '-metadata','title=RESCUE / VLA - From language to flight',
         '-metadata','comment=Recorded physical simulation. Studio CG and sound are presentation. No real flight.',str(output)])
    (TMP/'mastering_log.txt').write_bytes(proc.stderr)
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)]).stdout)
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
    assert (video['width'],video['height'])==(1920,1080)
    assert video['avg_frame_rate']=='30/1' and int(video['nb_frames'])==4740
    assert video['codec_name']=='h264' and video['pix_fmt']=='yuv420p'
    assert audio['codec_name']=='aac' and audio['channels']==2 and audio['sample_rate']=='48000'
    assert abs(float(probe['format']['duration'])-158)<.1
    print('CONTAINER_AND_STREAMS_VERIFIED',flush=True)
    # Extract every 3 s, plus samples surrounding each flight's phase changes.
    times=set(range(0,158,3))
    times.update([2,7.7,8.3,15.7,16.3,30.7,31.3,55.7,56.3,80.7,81.3,109.7,110.3,130.7,131.3,144.7,145.3,157.5])
    for flight in meta['continuous_flights']:
        directory=ROOT/meta['source_records']/flight['profile']
        last=None
        for text in (directory/'trace.jsonl').read_text(encoding='utf8').splitlines():
            row=json.loads(text)
            if row['phase']!=last and row['t']>=16:
                t=flight['video_start_s']+(row['t']-16)/2
                times.update([max(0,t-.15),t+.2])
            last=row['phase']
    times=sorted(times)
    frames=[round(t*30) for t in times]
    dest=TMP/'final_qa';dest.mkdir(exist_ok=True)
    selection='+'.join(f'eq(n\\,{f})' for f in frames)
    proc=run(['ffmpeg','-v','error','-xerror','-i',str(output),'-vf',f'select={selection}',
              '-fps_mode','vfr','-q:v','2',str(dest/'frame_%03d.jpg')])
    assert not proc.stderr.strip()
    extracts=sorted(dest.glob('frame_*.jpg'))
    assert len(extracts)==len(frames),(len(extracts),len(frames))
    from PIL import Image,ImageDraw,ImageFont
    f=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',19)
    sheets=[]
    for offset in range(0,len(extracts),6):
        sheet=Image.new('RGB',(1440,1302),'#07121d');d=ImageDraw.Draw(sheet)
        for j,path in enumerate(extracts[offset:offset+6]):
            x=j%2*720;y=j//2*434
            sheet.paste(Image.open(path).resize((720,405)),(x,y))
            d.text((x+14,y+408),f'{offset+j+1:02} / {times[offset+j]:06.2f} s',font=f,fill='#b6ccd9')
        path=dest/f'sheet_{offset//6:02}.jpg';sheet.save(path,quality=94);sheets.append(str(path.relative_to(ROOT)))
    after=loudness(output)
    assert abs(float(after['input_i'])+16)<.8
    assert float(after['input_tp'])<=-1.4
    voices=json.loads((TMP/'voice_manifest.json').read_text(encoding='utf8'))
    srt=[]
    for i,v in enumerate(voices):
        srt.extend([str(i+1),stamp(v['start'])+' --> '+stamp(v['start']+v['duration_s']+.2),v['caption'],''])
    (OUT/'rescue_drone_premium.srt').write_text('\n'.join(srt),encoding='utf8')
    meta['sha256']=sha(output);meta['bytes']=output.stat().st_size
    meta['audio_mastering']=dict(target_lufs=-16,true_peak_ceiling_db=-2,input=before,encoded_measurement=after)
    meta['source_sha256'].update({name:sha(ROOT/name) for name in ['animate_studio_blender.py','finalize_premium_video.py','synthesize_video_voice.ps1']})
    meta['studio_frames']=dict(opening=240,closing=390,renderer='Blender 3.1 Eevee',resolution=[1920,1080],fps=30)
    (OUT/'rescue_drone_premium.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
    qa=dict(sha256=meta['sha256'],decoded_without_errors=True,full_frame_count=int(video['nb_frames']),
            width=1920,height=1080,fps=30,duration_s=158,stereo_audio_verified=True,
            loudness_lufs=float(after['input_i']),true_peak_db=float(after['input_tp']),
            extracted_times_s=times,contact_sheets=sheets,
            representative_frames_visually_inspected=False,visual_review='Pending review of the actual encoded MP4 extracts, not only previews.',
            evidence_unchanged=all(sha(ROOT/meta['source_records']/profile/name)==value for profile,items in meta['evidence_sha256'].items() for name,value in items.items()),
            external_contact=False,new_training=False,new_flights=False)
    assert qa['evidence_unchanged']
    (OUT/'premium_qa.json').write_text(json.dumps(qa,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in qa.items() if k not in ['extracted_times_s','contact_sheets']},indent=2),flush=True)
    print('CONTACT_SHEETS',len(sheets),flush=True)

if __name__=='__main__':main()
