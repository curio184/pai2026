"""Preserve the registered diagnostic and correct its grounded-takeoff reference."""
import ast,datetime,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=W/'scripts/diagnose_train06_postflight.py'
old=src.read_text(encoding='utf-8-sig')
new=old.replace("brake = -1.2 * state[:2]", "brake = np.zeros(2) if task==2 and state[3]<.25 else -1.2 * state[:2]")
new=new.replace("brake = -1.2*own[:2];norm=np.linalg.norm(brake)", "brake = np.zeros(2) if tasks[e['instruction']]==2 and own[3]<.25 else -1.2*own[:2];norm=np.linalg.norm(brake)")
new=new.replace('train06_en_postflight_development_diagnostic.json','train06_en_postflight_v2_development_diagnostic.json')
assert new!=old and new.count('np.zeros(2)')==2
ast.parse(new)
dst=W/'scripts/diagnose_train06_postflight_v2.py';assert not dst.exists();dst.write_text(new,encoding='utf8')
note=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    original_report='reports/train06_en_postflight_development_diagnostic.json',
    original_sha256=sha(W/'reports/train06_en_postflight_development_diagnostic.json'),
    corrected_report='reports/train06_en_postflight_v2_development_diagnostic.json',
    reason='The train06 grounded-takeoff horizontal teacher is zero below estimated altitude 0.25m. The first diagnostic used -1.2 times velocity for this subset. Hover and navigation conclusions are unchanged.',
    scope='Postflight descriptive reference only; no changes to flights, scoring, labels, train07 plan, model, or final evaluation.',
    correction_script_sha256=sha(dst))
path=W/'reports/train06_diagnostic_reference_correction.json';assert not path.exists()
path.write_text(json.dumps(note,indent=2),encoding='utf8')
print(json.dumps(note))
