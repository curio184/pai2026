import json, shutil
import openai_voice as voice
OUT=voice.HERE/'intro_slow';OUT.mkdir(exist_ok=True)
voice.OUT=OUT
voice.TEXTS=[
 '災害救助ドローンとは、人が立ち入りにくい場所で、被災者の捜索を支援するドローンです。',
 '今回は、言葉による指示で捜索を任せ、操縦の負担を減らすことを目指しました。']
voice.generate('gpt-realtime-2.1-mini','marin')
shutil.copy2(voice.HERE/'intro_openai/voice_01.wav',OUT/'command.wav')
shutil.copy2(voice.HERE/'intro_openai/voice_01.json',OUT/'command.json')
