"""Lossless NTFS compression of inactive pre-submission candidates, without moving or deleting files.

Registration reads metadata only. Execution must wait until all flights have ended.
Current candidate train10 and the submitted v1.0 are excluded explicitly.
"""
import argparse,ctypes,datetime,hashlib,json,os,shutil,subprocess,sys
from ctypes import wintypes
from pathlib import Path
import psutil
W=Path(__file__).resolve().parents[1];P=W.parent
PLAN=W/'protocol/ntfs_legacy_model_compression.json'
ARCHIVES=['smolvla_training','smolvla_training_civic_01','smolvla_training_realism_01','smolvla_training_revision_02']

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,obj):p.write_text(json.dumps(obj,indent=2),encoding='utf-8')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def contained(p):
    p=p.resolve();root=(P/'outputs').resolve()
    assert p.is_relative_to(root) and p.drive.upper()=='E:',p
    assert p.relative_to(root).parts[0] in ARCHIVES,p
    return p
def allocated(p):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    fn=kernel.GetCompressedFileSizeW;fn.argtypes=[wintypes.LPCWSTR,ctypes.POINTER(wintypes.DWORD)];fn.restype=wintypes.DWORD
    high=wintypes.DWORD();ctypes.set_last_error(0);low=fn(str(p),ctypes.byref(high))
    if low==0xffffffff and ctypes.get_last_error():raise ctypes.WinError(ctypes.get_last_error())
    return (high.value<<32)|low

def register():
    assert not PLAN.exists()
    assert any(x.mountpoint.upper()=='E:\\' and x.fstype.upper()=='NTFS' for x in psutil.disk_partitions(all=True))
    files=[]
    for candidate in ARCHIVES:
        for rel in ['final/model.safetensors']:
            p=contained(P/'outputs'/candidate/rel)
            assert p.is_file()
            expected=None  # Record full SHA-256 immediately before and after compression.
            files.append(dict(path=p.relative_to(P).as_posix(),bytes=p.stat().st_size,allocated_bytes=allocated(p),expected_sha256=expected))
    obj=dict(created_utc=now(),operation='NTFS transparent compression, compact.exe /C /Q on exact files; no recursion, moves, deletion or content editing.',
        script_sha256=sha(Path(__file__)),target_free_gib=8,files=files,
        excludes=['submitted v1.0','train10_en','all flight records','video','original PDF'],
        limits=dict(cpu_affinity=[0,1],priority='BELOW_NORMAL',concurrent_files=1),
        execution_precondition='train10 full suite ended; no project training or flight processes running.',
        integrity='Record and compare SHA-256 before and after each operation. Preserve original filenames and paths.',
        free_bytes_before_registration=shutil.disk_usage(W).free)
    write(PLAN,obj);print(json.dumps(dict(registered=True,files=len(files),logical_bytes=sum(x['bytes'] for x in files),plan_sha256=sha(PLAN))))

def execute():
    plan=read(PLAN);assert plan['script_sha256']==sha(Path(__file__))
    assert read(W/'pipeline_train10_en_status.json')['stage']=='development_review'
    for p in psutil.process_iter(['pid','name']):
        if p.pid==os.getpid():continue
        if p.info['name'].lower() not in ['python.exe','blender.exe','wsl.exe']:continue
        try:args=p.cmdline()
        except (psutil.NoSuchProcess,psutil.AccessDenied):continue
        normalized=' '.join(args).replace('\\','/').lower()
        if 'pai2026/drone_rescue_stampfly' in normalized and any(x in normalized for x in ['pipeline_train','run_round02','search_worker.py','vla_worker.py','civic_render_client.py','search_mission.py','rescue_mission.py']):
            raise RuntimeError('A project flight/training worker is still running; do not compress concurrently.')
    out=W/'reports/legacy_model_compression';out.mkdir(exist_ok=False)
    proc=psutil.Process();proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS);proc.cpu_affinity(plan['limits']['cpu_affinity'])
    compact=Path(os.environ['SystemRoot'])/'System32/compact.exe';assert compact.is_file()
    start_free=shutil.disk_usage(W).free;receipts=[]
    write(out/'started.json',dict(started_utc=now(),plan_sha256=sha(PLAN),free_bytes=start_free,windows_native=True,wsl_used=False))
    for index,item in enumerate(plan['files']):
        if shutil.disk_usage(W).free>=plan['target_free_gib']*1024**3:break
        p=contained(P/item['path']);assert p.stat().st_size==item['bytes']
        before=sha(p)
        if item['expected_sha256']:assert before==item['expected_sha256'],item['path']
        receipt=dict(path=item['path'],sha256_before=before,logical_bytes=p.stat().st_size,allocated_before=allocated(p),started_utc=now())
        write(out/f'{index:02d}_before.json',receipt)
        completed=subprocess.run([str(compact),'/C','/Q',str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        (out/f'{index:02d}_compact.log').write_bytes(completed.stdout+completed.stderr)
        after=sha(p)
        receipt.update(sha256_after=after,hash_match=before==after,returncode=completed.returncode,allocated_after=allocated(p),finished_utc=now(),free_bytes=shutil.disk_usage(W).free)
        write(out/f'{index:02d}_receipt.json',receipt);receipts.append(receipt)
        write(out/'status.json',dict(state='running',completed=len(receipts),files=receipts))
        print(json.dumps(dict(path=item['path'],hash_match=before==after,saved_bytes=receipt['allocated_before']-receipt['allocated_after'],free_gib=receipt['free_bytes']/1024**3)),flush=True)
        assert completed.returncode==0 and before==after,'Stop on any integrity or filesystem error'
    end_free=shutil.disk_usage(W).free
    write(out/'status.json',dict(state='complete',completed=len(receipts),files=receipts,all_hashes_match=all(r['hash_match'] for r in receipts),
        plan_sha256=sha(PLAN),free_bytes_before=start_free,free_bytes_after=end_free,logical_contents_or_paths_changed=False,files_deleted=0,files_moved=0))
    print(json.dumps(dict(complete=True,files=len(receipts),all_hashes_match=True,free_gib=end_free/1024**3)),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','execute']);args=parser.parse_args()
    register() if args.mode=='register' else execute()
