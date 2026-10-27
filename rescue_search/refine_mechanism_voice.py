import json,shutil
import openai_voice as voice
OUT=voice.HERE/'mechanism_movie';revision=OUT/'voice_revision';revision.mkdir(exist_ok=True)
voice.OUT=revision
voice.TEXTS=['VLAは、カメラ映像と言葉による指示から、次の動作を生成するAIです。']
voice.STYLE += (' Pronounce VLA clearly as ブイ・エル・エー, and AI as エー・アイ. '
 'Articulate カメラ映像と, then a brief natural pause, then ことばによる指示から. '
 'Say every syllable of ことばによる clearly. Use a steady, conversational Japanese pace.')
original_norm=voice.norm
voice.norm=lambda s:original_norm(s).lower().replace('vla','ブイエルエー').replace('ai','エーアイ').replace('ことば','言葉')
if (revision/'voice_00.json').exists():
    info=json.loads((revision/'voice_00.json').read_text(encoding='utf8'))
    info['transcript_matches']=voice.norm(info['transcript'])==voice.norm(info['text'])
    info['normalization']='Punctuation, Japanese readings of VLA/AI, and ことば/言葉'
    assert info['transcript_matches']
    (revision/'voice_00.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
voice.generate('gpt-realtime-2.1-mini','marin')
manifest=json.loads((OUT/'generation_manifest.json').read_text(encoding='utf8'))
g=json.loads((revision/'generation_manifest.json').read_text(encoding='utf8'))[0]
shutil.copy2(OUT/'voice_01.wav',OUT/'voice_01_initial.wav')
shutil.copy2(revision/'voice_00.wav',OUT/'voice_01.wav')
g.update(index=1,file='voice_01.wav');manifest[1]=g
(OUT/'generation_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
