import json,shutil
from pathlib import Path
import openai_voice as voice
OUT=Path(__file__).resolve().parent/'conditions_movie'
revision=OUT/'voice_revision';revision.mkdir(exist_ok=True)
manifest=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'))
voice.OUT=revision;voice.TEXTS=[manifest[1]['text']]
original_norm=voice.norm
voice.norm=lambda s:original_norm(s).replace('見え方','みえかた')
cached=revision/'voice_00.json'
if cached.exists():
 info=json.loads(cached.read_text(encoding='utf8'))
 info['transcript_matches']=voice.norm(info['text'])==voice.norm(info['transcript'])
 assert info['transcript_matches']
 cached.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
voice.STYLE+=' Pronounce 見え方 as みえかた, clearly separating each syllable. Use a brief natural pause after そこで. Read exactly the supplied sentence.'
voice.generate('gpt-realtime-2.1-mini','marin')
new=json.loads((revision/'generation_manifest.json').read_text(encoding='utf8'))[0]
assert new['transcript_matches'] and new['duration_s']<7
if not (OUT/'voice_01_initial.wav').exists():shutil.copy2(OUT/'voice_01.wav',OUT/'voice_01_initial.wav')
shutil.copy2(revision/'voice_00.wav',OUT/'voice_01.wav')
new.update(index=1,file='voice_01.wav');manifest[1]=new
(OUT/'generation_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
