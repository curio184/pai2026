import openai_voice as voice
voice.OUT=voice.HERE/'intro_pan';voice.OUT.mkdir(exist_ok=True)
voice.TEXTS=['災害救助ドローンとは、人が立ち入りにくい場所で、被災者の捜索を支援するドローンです。']
voice.STYLE += (' Pay special attention to the opening: pronounce exactly "さいがいきゅうじょドローンとは、" '
                '(saigai kyujo doron to wa), then a short pause. The two particles after ドローン are と and は only. '
                'Never insert して or としては. Read the entire supplied sentence naturally and verbatim.')
voice.generate('gpt-realtime-2.1-mini','marin')
