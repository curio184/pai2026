"""Lossless NTFS compression of completed records and two inactive candidates.

No deletion, movement, content rewrite, video/PDF/audio compression or WSL use.
Register metadata while tests run; execute only after train11 pipeline has ended.
"""
import argparse,ctypes,datetime,hashlib,json,os,shutil,subprocess
from ctypes import wintypes
from pathlib import Path
import psutil
W=Path(__file__).resolve().parents[1];P=W.parent
PLAN=W/'protocol/ntfs_inactive_record_compression.json'
SUFFIXES={'.json','.jsonl','.log','.txt'}
FINALS={'v11_color/models/train10_en/final/model.safetensors','v11_color/models/train11_en/final/model.safetensors'}
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,o):p.write_text(json.dumps(o,indent=2),encoding='utf8')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def contained(p):
    p=p.resolve();assert p.is_relative_to(P.resolve()) and p.drive.upper()=='E:',p
    rel=p.relative_to(P.resolve()).as_posix()
    assert rel in FINALS or (p.suffix.lower() in SUFFIXES and p.stat().st_size>1024**2),rel
    assert not any(x in rel for x in ['stress_train11_en/','dev_train11_en/','models/train11_en/source_snapshot/']),rel
    return p
def allocated(p):
    k=ctypes.WinDLL('kernel32',use_last_error=True);f=k.GetCompressedFileSizeW
    f.argtypes=[wintypes.LPCWSTR,ctypes.POINTER(wintypes.DWORD)];f.restype=wintypes.DWORD
    hi=wintypes.DWORD();ctypes.set_last_error(0);lo=f(str(p),ctypes.byref(hi))
    if lo==0xffffffff and ctypes.get_last_error():raise ctypes.WinError(ctypes.get_last_error())
    return (hi.value<<32)|lo
def register():
    assert not PLAN.exists()
    assert any(x.mountpoint.upper()=='E:\\' and x.fstype.upper()=='NTFS' for x in psutil.disk_partitions(all=True))
    candidates=[]
    for root,dirs,names in os.walk(P,followlinks=False):
        dirs[:]=[d for d in dirs if not (Path(root)/d).is_junction() and d not in ['.git','__pycache__']]
        for n in names:
            q=Path(root)/n;rel=q.relative_to(P).as_posix()
            if any(x in rel for x in ['stress_train11_en/','dev_train11_en/','models/train11_en/','logs/pipeline11_']):continue
            if q.suffix.lower() in SUFFIXES and q.stat().st_size>1024**2:candidates.append(contained(q))
    candidates.extend(contained(P/x) for x in sorted(FINALS))
    files=[]
    for q in sorted(set(candidates),key=lambda x:x.stat().st_size,reverse=True):
        rel=q.relative_to(P).as_posix();expected=None
        if rel in FINALS:expected=read(q.parent.parent/'result.json')['checkpoint_sha256']
        files.append(dict(path=rel,bytes=q.stat().st_size,allocated_bytes=allocated(q),expected_sha256=expected))
    obj=dict(created_utc=now(),operation='Native NTFS transparent compression with compact.exe /C /Q, exact files only.',
        script_sha256=sha(Path(__file__)),files=files,target_free_gib=8,
        limits=dict(cpu_affinity=[0,1],priority='BELOW_NORMAL',concurrent_files=1),
        excludes=['submitted v1.0 weights','all videos, images, PDF and audio','train11 flight records','active files'],
        precondition='All train11 trials and pipeline processing finished; no project training/flight workers.',
        integrity='SHA-256 before and after every file; preserve byte contents and all paths; no deletion or movement.',
        free_bytes_before_registration=shutil.disk_usage(P).free)
    write(PLAN,obj);print(json.dumps(dict(registered=True,files=len(files),logical_gib=sum(x['bytes'] for x in files)/2**30,plan_sha256=sha(PLAN))))
def execute():
    plan=read(PLAN);assert plan['script_sha256']==sha(Path(__file__))
    assert read(W/'pipeline_train11_en_status.json')['stage']=='development_review'
    for proc in psutil.process_iter(['pid','name']):
        if proc.pid==os.getpid() or proc.info['name'].lower() not in ['python.exe','blender.exe','wsl.exe']:continue
        try:args=proc.cmdline()
        except (psutil.NoSuchProcess,psutil.AccessDenied):continue
        command=' '.join(args).replace('\\','/').lower()
        if 'pai2026/drone_rescue_stampfly' in command and any(x in command for x in ['pipeline_train','run_round02','search_worker.py','vla_worker.py','civic_render_client.py','search_mission.py','rescue_mission.py']):
            raise RuntimeError('Project training/flight process still active')
    out=W/'reports/inactive_record_compression';out.mkdir(exist_ok=False)
    proc=psutil.Process();proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS);proc.cpu_affinity([0,1])
    compact=Path(os.environ['SystemRoot'])/'System32/compact.exe';assert compact.is_file()
    start=shutil.disk_usage(P).free;receipts=[]
    write(out/'started.json',dict(started_utc=now(),plan_sha256=sha(PLAN),free_bytes=start,windows_native=True,wsl_used=False))
    for i,item in enumerate(plan['files']):
        if shutil.disk_usage(P).free>=plan['target_free_gib']*1024**3:break
        q=contained(P/item['path']);assert q.stat().st_size==item['bytes']
        before=sha(q)
        if item['expected_sha256']:assert before==item['expected_sha256']
        receipt=dict(path=item['path'],sha256_before=before,logical_bytes=q.stat().st_size,allocated_before=allocated(q),started_utc=now())
        write(out/f'{i:03d}_before.json',receipt)
        result=subprocess.run([str(compact),'/C','/Q',str(q)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        (out/f'{i:03d}_compact.log').write_bytes(result.stdout+result.stderr)
        after=sha(q);receipt.update(sha256_after=after,hash_match=before==after,returncode=result.returncode,allocated_after=allocated(q),finished_utc=now())
        write(out/f'{i:03d}_receipt.json',receipt);receipts.append(receipt)
        assert result.returncode==0 and before==after,'Stop on any integrity failure'
        write(out/'status.json',dict(state='running',completed=len(receipts),files=receipts,free_bytes=shutil.disk_usage(P).free))
        if i%20==0:print(json.dumps(dict(completed=len(receipts),planned=len(plan['files']),all_hashes_match=True,free_gib=shutil.disk_usage(P).free/2**30)),flush=True)
    write(out/'status.json',dict(state='complete',completed=len(receipts),planned=len(plan['files']),files=receipts,
        all_hashes_match=all(r['hash_match'] for r in receipts),plan_sha256=sha(PLAN),free_bytes_before=start,free_bytes_after=shutil.disk_usage(P).free,
        logical_contents_or_paths_changed=False,files_deleted=0,files_moved=0))
    print(json.dumps(dict(complete=True,files=len(receipts),all_hashes_match=True,free_gib=shutil.disk_usage(P).free/2**30)),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['register','execute']);a=ap.parse_args()
    register() if a.mode=='register' else execute()
