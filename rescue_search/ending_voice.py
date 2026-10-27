"""Approved hardware-proposal and closing narration."""
from pathlib import Path
import openai_voice as voice
voice.OUT=Path(__file__).resolve().parent/'ending_movie';voice.OUT.mkdir(exist_ok=True)
voice.TEXTS=[
 '実機への展開を見据え、実在する小型ドローンとカメラ、制御用パソコンを組み合わせる構成を検討しています。',
 '搭載や通信、実機での飛行は、今後の検証課題です。',
 '今回は、指定した人物を探し、確認画像を保存するまでを実現しました。',
 '今後は、環境を変えた検証と、実機での確認を進めます。',
]
voice.generate('gpt-realtime-2.1-mini','marin')
