"""Prepare a local, checksummed data archive; no upload or publication."""
import hashlib,json,zipfile
from pathlib import Path
W=Path(__file__).resolve().parents[1];out=W/'review_assets';out.mkdir(exist_ok=True)
dest=out/'training_data_train01.zip'
if dest.exists():raise FileExistsError(dest)
files=sorted(p for p in (W/'data/dataset').rglob('*') if p.is_file())
files += [W/'protocol'/n for n in ['plan.json','training_frames.json','SHA256.txt','data_split_audit.json','sampling_implementation.json']]
files += [W/'scripts'/n for n in ['render_training.py','build_dataset.py']]
hashes={}
with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:
        name='v11_color/'+p.relative_to(W).as_posix();data=p.read_bytes();z.writestr(name,data);hashes[name]=hashlib.sha256(data).hexdigest()
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in hashes.items())
result=dict(archive=dest.name,bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),files=len(files),all_entries_sha256_verified=True,uploaded=False,source_files_unchanged=True,entries=hashes)
(out/'training_data_train01_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='entries'}))
