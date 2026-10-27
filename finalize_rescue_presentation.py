"""Master the new-world video and prepare full-decode visual/audio verification."""
import hashlib,json,math,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from finalize_premium_video import run,loudness,stamp
ROOT=Path(__file__).resolve().parent;TMP=ROOT/'tmp/rescue_presentation';OUT=ROOT/'output/video'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    plan=json.loads((TMP/'plan.json').read_text(encoding='utf8'));meta=json.loads((OUT/'rescue_drone_presentation.json').read_text(encoding='utf8'))
    output=OUT/'rescue_drone_presentation.mp4'
    if output.exists():raise FileExistsError(output)
    assert sha(ROOT/plan['scene_file'])==plan['blend_sha256']
    assert sha(OUT/'rescue_drone_realism.mp4')==plan['prior_video_sha256']
    assert sha(OUT/'rescue_drone_premium.mp4')=='fb72c90f92d670a870554e9fd5f3dc889f3c93c7b9eab0604fd4bebd3fa991f6'
    for profile,files in plan['evidence_sha256'].items():
        for name,digest in files.items():assert sha(ROOT/plan['records']/profile/name)==digest
    before=loudness(TMP/'soundtrack.wav')
    af=('loudnorm=I=-16:TP=-2:LRA=10:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=false:print_format=json').format(**before)
    proc=run(['ffmpeg','-hide_banner','-i',str(OUT/'rescue_drone_presentation_silent.mp4'),'-i',str(TMP/'soundtrack.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af',af,'-c:a','aac','-b:a','256k','-ar','48000','-t',str(plan['duration_s']),'-movflags','+faststart','-metadata','title=RESCUE / VLA - The Rescue Room','-metadata','comment=Actual rich-world VLA and MuJoCo flights. Same frozen optical scene. External cameras reconstruct recorded poses. No real flight.',str(output)])
    (TMP/'mastering_log.txt').write_bytes(proc.stderr)
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)]).stdout)
    video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
    assert (video['width'],video['height'])==(1920,1080) and video['avg_frame_rate']=='30/1'
    assert int(video['nb_frames'])==plan['frames'] and video['codec_name']=='h264' and video['pix_fmt']=='yuv420p'
    assert audio['codec_name']=='aac' and audio['channels']==2 and audio['sample_rate']=='48000'
    assert abs(float(probe['format']['duration'])-plan['duration_s'])<.1 and 60<=plan['duration_s']<=180
    times=set(float(v) for v in range(0,math.ceil(plan['duration_s']),3) if v<plan['duration_s'])
    for section in plan['timeline'][1:]:times.update([section['start']-.1,section['start']+.25])
    for f in plan['flights']:
        previous=None
        for text in (ROOT/plan['records']/f['profile']/'trace.jsonl').read_text().splitlines():
            row=json.loads(text)
            if row['phase']!=previous and row['t']>=f['sim_start']:
                t=f['start']+f['lead_s']+(row['t']-f['sim_start'])/f['speed'];times.update([t-.1,t+.25])
            previous=row['phase']
    times.add(plan['duration_s']-.5);frames=sorted(set(round(t*30) for t in times if 0<=t<plan['duration_s']-.04));times=[f/30 for f in frames]
    dest=TMP/'final_qa';dest.mkdir(exist_ok=False)
    selection='+'.join(f'eq(n\\,{f})' for f in frames)
    decoded=run(['ffmpeg','-v','error','-xerror','-i',str(output),'-vf',f'select={selection}','-fps_mode','vfr','-q:v','2',str(dest/'frame_%03d.jpg')]);assert not decoded.stderr.strip()
    extracted=sorted(dest.glob('frame_*.jpg'));assert len(extracted)==len(frames)
    font=ImageFont.truetype('C:/Windows/Fonts/bahnschrift.ttf',19);sheets=[]
    for offset in range(0,len(extracted),6):
        sheet=Image.new('RGB',(1440,1302),'#07121d');draw=ImageDraw.Draw(sheet)
        for j,file in enumerate(extracted[offset:offset+6]):
            x=j%2*720;y=j//2*434;sheet.paste(Image.open(file).resize((720,405)),(x,y));draw.text((x+14,y+408),f'{offset+j+1:02} / {times[offset+j]:06.2f} s',font=font,fill='#b6ccd9')
        file=dest/f'sheet_{offset//6:02}.jpg';sheet.save(file,quality=94);sheets.append(str(file.relative_to(ROOT)))
    after=loudness(output);assert abs(float(after['input_i'])+16)<.8 and float(after['input_tp'])<=-1.4
    voices=json.loads((TMP/'voice_manifest.json').read_text(encoding='utf8'));subtitles=[]
    for i,v in enumerate(voices):subtitles.extend([str(i+1),stamp(v['start'])+' --> '+stamp(v['start']+v['duration_s']+.2),v['caption'],''])
    (OUT/'rescue_drone_presentation.srt').write_text('\n'.join(subtitles),encoding='utf8')
    meta.update(sha256=sha(output),bytes=output.stat().st_size,audio_mastering=dict(target_lufs=-16,true_peak_ceiling_db=-2,input=before,encoded_measurement=after),actual_new_environment_execution=True,real_hardware_flight=False,hardware_diagram_status='Proposed real-hardware architecture; payload, power and wireless links not validated. Controller and VLA are software on the ground PC.',hardware_design_sha256=sha(ROOT/'hardware_design.json'))
    for name in ['finalize_rescue_presentation.py','make_rescue_presentation_audio.py','synthesize_rescue_presentation_voice.ps1','build_civic_realism.py','civic_humans_v2.py','prepare_realism_build.py','civic_camera.py','civic_render_client.py']:meta['source_sha256'][name]=sha(ROOT/name)
    (OUT/'rescue_drone_presentation.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf8')
    qa=dict(sha256=meta['sha256'],decoded_without_errors=True,width=1920,height=1080,fps=30,frames=plan['frames'],duration_s=plan['duration_s'],stereo_audio_verified=True,loudness_lufs=float(after['input_i']),true_peak_db=float(after['input_tp']),extracted_times_s=times,contact_sheets=sheets,visually_reviewed=False,old_premium_preserved=True,scene_hash_matches_live_policy_camera=True)
    (OUT/'presentation_qa.json').write_text(json.dumps(qa,indent=2),encoding='utf8')
    print(json.dumps(qa,indent=2),flush=True)
if __name__=='__main__':main()
