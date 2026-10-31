"""Repair missing stdlib by relocating the identical base interpreter to E:."""
import datetime,hashlib,json
from pathlib import Path
OLD=Path('<USER_HOME>/AppData/Local/Temp/physical_ai_fly_lite/python/cpython-3.12.15-windows-x86_64-none')
NEW=Path('<WORK_ROOT>/runtimes/python_restore/cpython-3.12.15-windows-x86_64-none')
OUT=Path('<WORK_ROOT>/runtimes/receipt_environment_recovery');OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
binary={n:dict(old=sha(OLD/n),restored=sha(NEW/n)) for n in ['python.exe','python312.dll','python3.dll','vcruntime140.dll','vcruntime140_1.dll']}
assert all(r['old']==r['restored'] for r in binary.values())
assert (NEW/'Lib/encodings/__init__.py').exists() and (NEW/'Lib/os.py').exists()
rows=[]
for name,root in [('check_env','C:/Temp/pai2026_submission/check_env'),
                  ('smolvla_env','<USER_HOME>/AppData/Local/Temp/physical_ai_drone_smolvla/venv'),
                  ('pdf_env','<USER_HOME>/AppData/Local/Temp/physical_ai_drone_rescue/venv')]:
    cfg=Path(root)/'pyvenv.cfg';old=cfg.read_bytes();backup=OUT/(name+'_pyvenv.cfg.original')
    with backup.open('xb') as f:f.write(old)
    lines=old.decode('utf-8').splitlines()
    assert any(l.startswith('home = ') and str(OLD).lower() in l.lower() for l in lines)
    new='\n'.join('home = '+str(NEW) if l.startswith('home = ') else l for l in lines)+'\n'
    cfg.write_text(new,encoding='utf-8')
    rows.append(dict(path=str(cfg),backup=str(backup),before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=sha(cfg)))
report=dict(updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    reason='Original base interpreter Lib/encodings directory was present but empty; interpreter could not start.',
    old_base=str(OLD),new_base=str(NEW),binary_hashes=binary,venvs=rows,
    model_changed=False,packages_upgraded=False,flight_repeated=False,scoring_changed=False)
(OUT/'recovery.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
