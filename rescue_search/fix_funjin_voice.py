"""Use an unambiguous kana input for the user-corrected reading ふんじん."""
import json,shutil
from pathlib import Path
import openai_voice as voice
OUT=Path(__file__).resolve().parent/'conditions_movie'
revision=OUT/'funjin_revision02';revision.mkdir(exist_ok=True)
manifest=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'))
display='災害現場では、霧や粉じんで視界が悪くなることもあります。'
spoken='さいがいげんばでは、霧やふんじんで視界が悪くなることもあります。'
original_norm=voice.norm
voice.norm=lambda s:original_norm(s).replace('粉塵','ふんじん').replace('粉じん','ふんじん').replace('災害現場','さいがいげんば')
voice.OUT=revision;voice.TEXTS=[spoken]
voice.STYLE+=' The word ふんじん is pronounced funjin, with the mora sequence ふ・ん・じ・ん. Follow the supplied hiragana exactly.'
voice.generate('gpt-realtime-2.1-mini','marin')
new=json.loads((revision/'generation_manifest.json').read_text(encoding='utf8'))[0]
assert new['transcript_matches']
if not (OUT/'voice_00_before_reading_fix.wav').exists():shutil.copy2(OUT/'voice_00.wav',OUT/'voice_00_before_reading_fix.wav')
shutil.copy2(revision/'voice_00.wav',OUT/'voice_00.wav')
new.update(index=0,text=display,api_input_text=spoken,reading_correction='粉じん → ふんじん',file='voice_00.wav')
manifest[0]=new
(OUT/'generation_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
