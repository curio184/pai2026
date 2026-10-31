"""Build a scoped WSL launch command without changing the simulation program."""
import hashlib
from pathlib import Path
def linux(p):
    p=Path(p).resolve();return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def bounded_command(command,out):
    assert command[:5]==['wsl','-d','Ubuntu-22.04','--exec','env']
    assignments=[];rest=command[5:]
    while rest and '=' in rest[0] and not rest[0].startswith('/'):
        assignments.append(rest.pop(0))
    assert rest and rest[0].endswith('/python')
    w=Path(__file__).resolve().parents[1]
    unit='pai2026-flight-'+hashlib.sha256(str(out.resolve()).encode()).hexdigest()[:12]
    return ['wsl','-d','Ubuntu-22.04','--user','root','--exec','systemd-run','--scope','--quiet','--collect',
        '--uid=curio','--gid=curio','--unit='+unit,'-p','CPUQuota=400%','-p','CPUWeight=10',
        '-p','AllowedCPUs=0-3','-p','MemoryMax=8G','-p','MemoryHigh=6G','-p','TasksMax=128',
        'nice','-n','10','env','HOME=<WSL_HOME>','USER=curio','LOGNAME=curio',*assignments,
        '/usr/bin/python3',linux(w/'scripts/bounded_wsl_entry.py'),linux(out),*rest]
