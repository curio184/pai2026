"""Read-only inventory; never traverses directory reparse points implicitly."""
import os, json, stat, datetime
from pathlib import Path
P=Path(__file__).resolve().parents[2]
def size(root):
    total=0;count=0;links=[];errors=[];pending=[str(root)]
    while pending:
        directory=pending.pop()
        try:
            with os.scandir(directory) as entries:
                for e in entries:
                    try:
                        s=e.stat(follow_symlinks=False)
                        if getattr(s,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT:
                            links.append(dict(path=e.path,target=os.path.realpath(e.path)));continue
                        if e.is_dir(follow_symlinks=False):pending.append(e.path)
                        elif e.is_file(follow_symlinks=False):total+=s.st_size;count+=1
                    except OSError as exc:errors.append(dict(path=e.path,error=str(exc)))
        except OSError as exc:errors.append(dict(path=directory,error=str(exc)))
    return dict(bytes=total,files=count,links=links,errors=errors)
rows=[]
for child in P.iterdir():
    s=child.lstat()
    if getattr(s,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT:
        rows.append(dict(name=child.name,reparse_target=os.path.realpath(child),**size(os.path.realpath(child))))
    elif child.is_dir():rows.append(dict(name=child.name,**size(child)))
    else:rows.append(dict(name=child.name,bytes=s.st_size,files=1,links=[],errors=[]))
link_rows=[];seen=set();pending=[]
for r in rows:
    if r.get('reparse_target'):pending.append(r['reparse_target'])
    pending.extend(l['target'] for l in r['links'])
while pending:
    target=pending.pop();key=os.path.normcase(os.path.realpath(target))
    if key in seen:continue
    seen.add(key);info=size(target);link_rows.append(dict(target=target,**info))
    pending.extend(l['target'] for l in info['links'])
physical_bytes=sum(r['bytes'] for r in rows if not r.get('reparse_target'))
total=physical_bytes+sum(r['bytes'] for r in link_rows)
result=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project=str(P),entries=rows,
    linked_storage=link_rows,project_physical_bytes=physical_bytes,unique_total_bytes=total)
out=P/'v11_color/reports/storage_inventory_20261029.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(project_physical_gib=physical_bytes/1024**3,unique_total_gib=total/1024**3,
    linked_storage=[dict(target=r['target'],gib=round(r['bytes']/1024**3,3),files=r['files'],links=r['links'],errors=r['errors']) for r in link_rows],report=str(out)),ensure_ascii=False))
