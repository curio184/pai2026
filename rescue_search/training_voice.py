"""Approved short fine-tuning explanation, using the existing narration voice."""
from pathlib import Path
import openai_voice as voice
voice.OUT=Path(__file__).resolve().parent/'training_movie'
voice.OUT.mkdir(exist_ok=True)
voice.TEXTS=[
 'VLAにドローンの飛行動作を覚えさせるため、追加学習を行っています。',
 '移動や旋回などの動作を定義し、画像や指示、機体の状態と対応づけて学習しています。',
]
base_norm=voice.norm
voice.norm=lambda s:base_norm(s).lower().replace('vla','ブイエルエー').replace('ぶいえるえー','ブイエルエー')
voice.generate('gpt-realtime-2.1-mini','marin')
