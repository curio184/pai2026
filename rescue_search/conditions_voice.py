"""Narration for the verified visual-condition montage, using the existing voice workflow."""
from pathlib import Path
import openai_voice as voice
OUT=Path(__file__).resolve().parent/'conditions_movie';OUT.mkdir(exist_ok=True)
voice.OUT=OUT
voice.TEXTS=[
 '災害現場では、霧や粉じんで視界が悪くなることもあります。',
 'そこで、見え方を変えた条件でも、同じモデルで捜索できるか確かめました。',
 '通常を含む四つの条件で、発見から着陸まで完了しました。',
]
voice.generate('gpt-realtime-2.1-mini','marin')
