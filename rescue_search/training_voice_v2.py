"""Connected acronym pronunciation and the user's shortened script."""
import json
from pathlib import Path
import openai_voice as voice
voice.OUT=Path(__file__).resolve().parent/'training_movie_v2';voice.OUT.mkdir(exist_ok=True)
DISPLAY=['VLAは追加学習を行っています。','移動や旋回などの動作を定義し、画像や指示、機体の状態と対応づけています。']
voice.TEXTS=['ブイエルエーは追加学習を行っています。',DISPLAY[1]]
voice.STYLE+=' Read ブイエルエー as one fluid Japanese acronym, smoothly connected to は. Do not spell it out, insert pauses between its letters, or emphasize each letter separately. Use a conversational documentary cadence.'
base_norm=voice.norm
voice.norm=lambda s:base_norm(s).lower().replace('vla','ブイエルエー')
voice.generate('gpt-realtime-2.1-mini','marin')
manifest=json.loads((voice.OUT/'generation_manifest.json').read_text(encoding='utf8'))
for i,v in enumerate(manifest):
 v.update(api_input_text=v['text'],text=DISPLAY[i])
(voice.OUT/'generation_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
