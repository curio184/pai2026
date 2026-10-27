import json,shutil
from pathlib import Path
import openai_voice as voice
OUT=Path(__file__).resolve().parent/'training_movie'
voice.OUT=OUT/'pronunciation_revision02';voice.OUT.mkdir(exist_ok=True)
voice.TEXTS=['ブイ、エル、エーにドローンの飛行動作を覚えさせるため、追加学習を行っています。']
norm=voice.norm
voice.norm=lambda s:norm(s).lower().replace('vla','ブイエルエー')
voice.STYLE += ' Articulate each acronym letter distinctly, with short pauses between letters. Speak slightly slower than your default pace.'
voice.generate('gpt-realtime-2.1-mini','marin')
manifest=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'))
info=json.loads((voice.OUT/'voice_00.json').read_text(encoding='utf8'))
info.update(api_input_text=info['text'],text=manifest[0]['text'],pronunciation='VLA = ブイ・エル・エー')
shutil.copy2(OUT/'voice_00.wav',OUT/'voice_00_before_pronunciation_fix.wav')
shutil.copy2(voice.OUT/'voice_00.wav',OUT/'voice_00.wav')
(OUT/'voice_00.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
manifest[0]=info
(OUT/'generation_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
