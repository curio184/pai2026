"""Create new train07 tooling without changing any past experiment source."""
from pathlib import Path
W=Path(__file__).resolve().parents[1]
for name in ['train06_en.py','pipeline_train06_en.py','preflight_train06_loss.py','monitor_train06.py','freeze_train06_implementation.py']:
    src=W/'scripts'/name;dest=W/'scripts'/name.replace('06','07');assert not dest.exists()
    text=src.read_text(encoding='utf-8-sig')
    text=text.replace('train06','train07').replace('dataset06','dataset07').replace('teacher_flight06','teacher_flight07').replace('pipeline06','pipeline07')
    text=text.replace('Train06 English: fixed 10,000','Train07 English: fixed 6,000')
    text=text.replace('Horizontal teacher relabeled; zero and half-velocity state anchors added.', 'Horizontal teacher relabeled to zero hold targets and sharper matched-standoff navigation; no new state anchors.')
    # Shared evaluator implementation is checked against the original train05 lock,
    # which avoids accidentally including historical training scripts in the lock.
    dest.write_text(text,encoding='utf8')
print('Created five new train07 scripts; previous sources unchanged.')
