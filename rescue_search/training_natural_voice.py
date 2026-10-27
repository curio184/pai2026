import json,shutil
from pathlib import Path
import openai_voice as v
OUT=Path(__file__).resolve().parent/'training_movie_v2'
v.OUT=OUT/'natural_revision02';v.OUT.mkdir(exist_ok=True)
v.TEXTS=['VLAは追加学習を行っています。']
v.STYLE+=' Pronounce VLA in standard Japanese as ブイエルエー, with clear vowels and the normal continuous rhythm used for an acronym in a sentence. Do not insert pauses between letters; do not rush or slur the acronym.'
old=v.norm;v.norm=lambda s:old(s).lower().replace('vla','ブイエルエー')
v.generate('gpt-realtime-2.1-mini','marin')
info=json.loads((v.OUT/'voice_00.json').read_text(encoding='utf8'))
manifest=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'))
manifest[0]=info
shutil.copy2(v.OUT/'voice_00.wav',OUT/'voice_00.wav')
(OUT/'generation_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
