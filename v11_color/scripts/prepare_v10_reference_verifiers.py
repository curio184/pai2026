from pathlib import Path
W=Path(__file__).resolve().parents[1]
s=(W/'scripts/audit_rebuild03_execution.py').read_text(encoding='utf-8').replace("W/'runtime_rebuild03'", "W/'runtime_rebuild03_v10ref'")
(W/'scripts/audit_v10_teacher_reference.py').write_text(s,encoding='utf-8')
s=(W/'scripts/verify_rebuild03.py').read_text(encoding='utf-8')
for a,b in [("W/'runtime_rebuild03'","W/'runtime_rebuild03_v10ref'"),('protocol/rebuild03_final.json','protocol/rebuild03_v10_reference.json'),('runs/rebuild03_final','runs/rebuild03_v10_reference'),('run_suite_rebuild03_final.py','run_suite_rebuild03_v10ref.py'),('len(rows)==42','len(rows)==16'),('records=42','records=16'),('portable_rebuild03_verified.json','portable_v10_reference_verified.json')]:s=s.replace(a,b)
(W/'scripts/verify_v10_teacher_reference.py').write_text(s,encoding='utf-8')
