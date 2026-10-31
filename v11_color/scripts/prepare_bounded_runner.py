"""Create audited launch-only variants; leave frozen runtime/evaluators untouched."""
import ast,difflib,json,hashlib
from pathlib import Path
W=Path(__file__).resolve().parents[1]
changes=[]
for srcname,dstname in [('run_suite_english.py','run_suite_bounded.py'),('run_round02_english.py','run_round02_bounded.py')]:
    src=W/'scripts'/srcname;dst=W/'scripts'/dstname;assert not dst.exists();old=src.read_text()
    if srcname=='run_suite_english.py':
        new=old.replace('from pathlib import Path','from pathlib import Path\nfrom bounded_wsl import bounded_command')
        needle="        write(out/'command.json',command);result['flight_started']=True"
        assert old.count(needle)==1
        new=new.replace(needle,"        command=bounded_command(command,out)\n"+needle)
    else:new=old.replace('from run_suite_english import W,P,sha,write,run_case','from run_suite_bounded import W,P,sha,write,run_case')
    assert old!=new;ast.parse(new);dst.write_text(new,encoding='utf8')
    changes.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=srcname,tofile=dstname))
(W/'protocol/bounded_execution.diff').write_text(''.join(changes),encoding='utf8')
print('Created launch-only variants; no flight, inference or model update.')
