"""Prepare postflight teacher comparisons; no inference or runtime changes."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
source=(W/'scripts/diagnose_train08_postflight.py').read_text(encoding='utf-8')
source=source.replace('stress_train08_en_capped','stress_train10_en').replace('dataset08_en','dataset10_en').replace('teacher_flight08','teacher_flight10')
source=source.replace("manifest['braking_coefficient']==0", "manifest['braking_coefficient']==.6")
source=source.replace("executed.append((action,ref[k],np.asarray(t['estimated_state']),k))", "reference=ref[k].copy()\n                yaw_k=t.get('yaw_chunk_index');yaw_k=k if yaw_k is None else int(yaw_k)\n                assert 0<=yaw_k<len(ref)\n                reference[3]=ref[yaw_k,3]\n                executed.append((action,reference,np.asarray(t['estimated_state']),k))")
source=source.replace("summary=read(suite/'summary.json')", "summary=read(suite/'summary.json');assert summary['completed']==summary['planned']")
source=source.replace("dest.write_text(json.dumps(out,indent=2),encoding='utf8')", "assert not dest.exists();dest.write_text(json.dumps(out,indent=2),encoding='utf8')")
out=W/'scripts/diagnose_train10_postflight.py';assert not out.exists();ast.parse(source);out.write_text(source,encoding='utf-8')
print('Prepared train10 postflight comparison with correct separate yaw execution indices; not executed.')
