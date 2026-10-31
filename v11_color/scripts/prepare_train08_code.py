"""Prepare a separate safety-margin training implementation; no data or training."""
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for name in ['train07_en.py','pipeline_train07_en.py','preflight_train07_loss.py','monitor_train07.py','freeze_train07_implementation.py']:
    src=W/'scripts'/name;dst=W/'scripts'/name.replace('07','08');assert not dst.exists()
    text=src.read_text(encoding='utf8').replace('train07','train08').replace('dataset07','dataset08').replace('teacher_flight07','teacher_flight08').replace('pipeline07','pipeline08')
    text=text.replace('Train07 English: fixed 6,000','Train08 English: fixed 4,000')
    text=text.replace('sharper matched-standoff navigation','sharper navigation with a 10cm teacher safety margin')
    dst.write_text(text,encoding='utf8')
src=W/'scripts/teacher_flight07.py';dst=W/'scripts/teacher_flight08.py';assert not dst.exists()
text=src.read_text(encoding='utf8');assert text.count('[-.9,0]')==1
dst.write_text(text.replace('[-.9,0]','[-1.,0]'),encoding='utf8')
src=W/'scripts/build_dataset07_en.py';dst=W/'scripts/build_dataset08_en.py';assert not dst.exists()
text=src.read_text(encoding='utf8').replace('train07 recipe','train08 recipe')
text=text.replace('from teacher_flight07 import teacher_chunk as teacher','from teacher_flight08 import teacher_chunk as teacher')
text=text.replace('from teacher_flight06 import teacher_chunk as oldteacher','from teacher_flight07 import teacher_chunk as oldteacher')
text=text.replace("protocol/train07_english.json","protocol/train08_english.json")
text=text.replace("source=W/'data/dataset06_en';out=W/'data/dataset07_en'","source=W/'data/dataset07_en';out=W/'data/dataset08_en'")
text=text.replace('scripts/teacher_flight07.py','scripts/teacher_flight08.py').replace('teacher_standoff_m=.9','teacher_standoff_m=1.0')
dst.write_text(text,encoding='utf8')
print('Seven train08 tools prepared; no plan, data generation, optimizer updates or inference executed.')
