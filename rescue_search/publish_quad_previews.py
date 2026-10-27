import json,shutil
from pathlib import Path
import consistent_narration as base
plan=json.loads((base.OUT/'plan.json').read_text(encoding='utf8'))
quad=base.VIDEO/'rescue_drone_conditions_quad_preview.mp4'
shutil.copy2(plan[5]['render_file'],quad)
context=base.VIDEO/'rescue_drone_training_natural_context.mp4'
inputs=[plan[i]['render_file'] for i in [1,2,3]]
clips=[(21,8),(0,plan[2]['duration_s']),(0,6)]
args=['ffmpeg','-v','error','-y']
for p in inputs:args+=['-i',p]
filters=[]
for i,(start,duration) in enumerate(clips):
 filters += [f'[{i}:v]trim=start={start}:duration={duration},setpts=PTS-STARTPTS[v{i}]',f'[{i}:a]atrim=start={start}:duration={duration},asetpts=PTS-STARTPTS[a{i}]']
filters += ['[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]']
args += ['-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-c:v','h264_nvenc','-cq','18','-preset','p5','-pix_fmt','yuv420p','-c:a','aac','-ar','96000','-b:a','192k','-movflags','+faststart',str(context)]
base.run(args)
for p,seconds in [(quad,18),(context,14+plan[2]['duration_s'])]:
 base.run(['ffmpeg','-v','error','-xerror','-i',str(p),'-f','null','-'])
 probe=json.loads(base.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]).stdout)
 assert abs(float(probe['format']['duration'])-seconds)<.05
 assert not any(s['codec_type']=='subtitle' for s in probe['streams'])
 assert not p.with_suffix('.srt').exists()
base.run(['ffmpeg','-v','error','-y','-ss','13.5','-i',str(quad),'-frames:v','1','-update','1',str(base.OUT/'conditions_quad/success_check.png')])
print('PREVIEWS_READY',quad,context,flush=True)
