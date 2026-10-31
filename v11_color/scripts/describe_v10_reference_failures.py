"""Apply the same postflight explanation to all 16 teacher-compatible cases."""
from pathlib import Path

W = Path(__file__).resolve().parents[1]
source = (W / 'scripts/describe_rebuild03_failures.py').read_text(encoding='utf-8')
source = source.replace('rebuild03_final.json', 'rebuild03_v10_reference.json')
source = source.replace('runs/rebuild03_final', 'runs/rebuild03_v10_reference')
source = source.replace('planned=42', 'planned=16')
source = source.replace('reports/rebuild03_failure_details.json',
                        'reports/rebuild03_v10_reference_failure_details.json')
exec(compile(source, str(W / 'scripts/describe_rebuild03_failures.py'), 'exec'),
     {'__name__': '__main__', '__file__': __file__})
