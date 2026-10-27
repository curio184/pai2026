"""Prevent a player's automatic SRT overlay on already-captioned video."""
import json,hashlib,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path.cwd()
video=ROOT/'output/video/rescue_drone_final.mp4'
sidecar=video.with_suffix('.srt')
transcript=HERE/'ending_movie/transcript_review.srt'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(video)
if sidecar.exists():
 transcript.write_bytes(sidecar.read_bytes())
 assert sha(sidecar)==sha(transcript)
 sidecar.unlink()
assert not sidecar.exists() and sha(video)==before
# A new delivery name also avoids a player retaining an already-loaded SRT.
dest=video.with_name('rescue_drone_final_caption_fixed.mp4')
shutil.copy2(video,dest)
assert sha(dest)==before and not dest.with_suffix('.srt').exists()
streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(dest)]))['streams']
assert all(s['codec_type']!='subtitle' for s in streams)
meta=json.loads(video.with_suffix('.json').read_text(encoding='utf8'))
meta.pop('subtitle_file',None)
meta.update(transcript_review_file=str(transcript),subtitle_delivery='Burned-in captions only; matching external SRT removed',duplicate_subtitle_fix=dict(video_and_audio_bytes_preserved=True,sha256=before,embedded_subtitle_streams=0,reviewed_frame_times_s=[123,150,165],player_auto_overlay_prevented=True))
video.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
meta['video']=str(dest)
dest.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
qa=HERE/'ending_movie/final_qa.json'
reports=json.loads(qa.read_text(encoding='utf8'))
for r in reports:
 if r.get('video')==str(video):
  r.pop('subtitle_file',None)
  r.update(transcript_review_file=str(transcript),subtitle_delivery=meta['subtitle_delivery'])
qa.write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
print('CAPTION_DELIVERY_FIXED',dest)
