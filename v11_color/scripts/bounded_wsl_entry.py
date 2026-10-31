"""Resource wrapper only: run the unchanged simulator inside a bounded cgroup."""
import datetime,json,os,subprocess,sys
from pathlib import Path
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def controls(root):
    names=['cpu.max','cpu.weight','cpuset.cpus.effective','memory.max','memory.high','memory.current','memory.peak','memory.events','cpu.stat','pids.max']
    return {n:(root/n).read_text().strip() for n in names if (root/n).exists()}
def cpus(text):
    result=set()
    for part in text.split(','):
        ends=part.split('-');result.update(range(int(ends[0]),int(ends[-1])+1))
    return result
def main():
    out=Path(sys.argv[1]);args=sys.argv[2:];assert out.is_dir() and args
    relative=next(x.split(':',2)[2] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
    root=Path('/sys/fs/cgroup')/relative.lstrip('/');limits=controls(root)
    quota,period=limits['cpu.max'].split();assert quota!='max' and int(quota)/int(period)<=4
    assert len(cpus(limits['cpuset.cpus.effective']))<=4
    assert int(limits['memory.max'])==8*1024**3 and int(limits['memory.high'])==6*1024**3
    assert os.getuid()==1000 and os.getpriority(os.PRIO_PROCESS,0)>=10
    assert os.environ['HOME']=='<WSL_HOME>'
    initial=dict(created_utc=now(),scope=str(root),limits=limits,command=args,uid=os.getuid(),nice=os.getpriority(os.PRIO_PROCESS,0),home=os.environ['HOME'],controller_and_model_logic_changed=False)
    dest=out/'resource_limits.json';assert not dest.exists();dest.write_text(json.dumps(initial,indent=2))
    result=subprocess.run(args)
    (out/'resource_usage.json').write_text(json.dumps(dict(finished_utc=now(),exit=result.returncode,scope=str(root),measurements=controls(root)),indent=2))
    return result.returncode
if __name__=='__main__':raise SystemExit(main())
