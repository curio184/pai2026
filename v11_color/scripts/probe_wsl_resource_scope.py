"""Tiny resource-limit probe. No simulator, inference, workload, or model load."""
import json,os,resource
from pathlib import Path
relative=next(x.split(':',2)[2] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
root=Path('/sys/fs/cgroup')/relative.lstrip('/')
values={name:(root/name).read_text().strip() for name in ['cpu.max','cpu.weight','memory.max','memory.high','memory.current','memory.events','pids.max']}
quota,period=values['cpu.max'].split()
assert quota!='max' and int(quota)/int(period)<=1
assert int(values['memory.max'])==1024**3
assert int(values['memory.high'])==768*1024**2
print(json.dumps(dict(passed=True,pid=os.getpid(),nice=os.getpriority(os.PRIO_PROCESS,0),scope=str(root),limits=values,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))
