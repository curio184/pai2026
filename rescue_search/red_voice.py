"""Spoken red-person command, using the established approved narration voice."""
from pathlib import Path
import openai_voice as voice
voice.OUT=Path(__file__).resolve().parent/'red_movie';voice.OUT.mkdir(exist_ok=True)
voice.TEXTS=['赤い服の人を探して。']
voice.generate('gpt-realtime-2.1-mini','marin')
