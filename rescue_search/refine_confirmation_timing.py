"""Do not duplicate temporal verification with an extra hover timer."""
from pathlib import Path
here=Path(__file__).resolve().parent;file=here/'search_mission.py'
text=file.read_text(encoding='utf8')
old='''if phase=="confirm":
                    stable=stable and confirmed'''
new='''if phase=="confirm":
                    stable=stable and confirmed
                    # VisualConfirmation already requires three distinct, tracked images.
                    # Waiting another 3.25 s here adds no new acceptance evidence.
                    navigation_complete=stable'''
assert text.count(old)==1;text=text.replace(old,new)
old='''if phase in ("report","reacquire"):
                    stable=stable and confirmed'''
new='''if phase in ("report","reacquire"):
                    stable=stable and confirmed
                    # Approach completion already required the stop-command window.
                    navigation_complete=stable'''
assert text.count(old)==1;text=text.replace(old,new)
file.write_text(text,encoding='utf8');print('TEMPORAL_CONFIRMATION_DUPLICATION_REMOVED')
