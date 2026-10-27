import openai_voice as voice
voice.OUT=voice.HERE/'mechanism_movie';voice.OUT.mkdir(exist_ok=True)
voice.TEXTS=[
 'ドローンの飛行を制御するために、VLAを利用します。',
 'VLAは、カメラ映像と言葉による指示から、次の動作を生成するAIです。',
 'ドローンの映像を無線でパソコンへ送り、VLAが生成した動作を飛行指令として返します。',
 'このやり取りを繰り返すことで、ドローンを自律的に制御します。']
voice.STYLE += ' Pronounce VLA as ブイエルエー and AI as エーアイ in Japanese. Do not explain the abbreviations or add words.'
original_norm=voice.norm
voice.norm=lambda s:original_norm(s.replace('VLA','ブイエルエー').replace('AI','エーアイ').replace('ブイ・エル・エー','ブイエルエー'))
voice.generate('gpt-realtime-2.1-mini','marin')
