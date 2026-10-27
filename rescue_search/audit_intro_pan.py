"""Reuse full encode checks, then verify pan geometry and audio correction."""
from pathlib import Path
import intro_pan as current
import sys,json,math
HERE=Path(__file__).resolve().parent
source=(HERE/'audit_intro_atmosphere.py').read_text(encoding='utf8')
source=source.replace('from intro_atmosphere import','from intro_pan import')
source=source.replace('times=[2,4.5,6,9.5,10,11,14,16,18,21,22.5,23.5]',
                      'times=[2,6,10,12.5,16,17,18,19,20,21,22.5,23.5]')
exec(compile(source,str(HERE/'audit_intro_atmosphere.py'),'exec'))
pan=json.loads((current.OUT/'pan_scene_source.json').read_text())
frames=pan['frames'];assert len(frames)==192
positions=[f['camera_position'] for f in frames]
assert all(max(abs(x-y) for x,y in zip(positions[0],p))<1e-6 for p in positions)
assert frames[-1]['focus_distance']>frames[0]['focus_distance']*4
asr=json.loads((current.OUT/'independent_transcription.json').read_text(encoding='utf8'))
assert asr['wording_matches'] and not asr['expected_text_supplied_to_asr']
assert asr['audio_sha256']==hashlib.sha256((current.OUT/'voice_00.wav').read_bytes()).hexdigest()
for p in [current.OUT/'final_qa.json',current.DEST.with_suffix('.json')]:
    r=json.loads(p.read_text(encoding='utf8'));r.update(fixed_position_camera_pan=True,focus_pull_to_survivor=True,
       opening_independent_transcription=asr['text'],opening_audio_verified_by_asr=True)
    p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
