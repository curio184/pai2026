"""Copy the frozen runtime, changing only seven instruction constants."""
import ast,difflib,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=W/'runtime';new=W/'runtime_english';assert not new.exists()
    lock=read(W/'protocol/runtime_lock.json');variants=read(W/'data/dataset/manifest.json')['prompt_variants']
    mapping={v[0]:v[2] for v in variants};assert len(mapping)==7
    changed=['search_mission.py','ardupilot_bridge/rescue_mission.py'];diffs=[];newhashes={}
    for name,expected in lock['runtime'].items():
        src=old/name;dest=new/name;assert sha(src)==expected
        dest.parent.mkdir(parents=True,exist_ok=True);before=src.read_bytes();after=before
        if name in changed:
            for bilingual,english in mapping.items():
                assert after.count(bilingual.encode('utf-8'))==1,(name,bilingual)
                after=after.replace(bilingual.encode('utf-8'),english.encode('utf-8'))
            restored=after
            for bilingual,english in mapping.items():
                assert restored.count(english.encode('utf-8'))==1
                restored=restored.replace(english.encode('utf-8'),bilingual.encode('utf-8'))
            assert restored==before
            ast.parse(after.decode('utf-8'))
            diffs.extend(difflib.unified_diff(before.decode('utf-8').splitlines(True),after.decode('utf-8').splitlines(True),fromfile='runtime/'+name,tofile='runtime_english/'+name))
        dest.write_bytes(after);newhashes[name]=sha(dest)
        if name not in changed:assert newhashes[name]==expected
    report=dict(base_runtime_lock_sha256=sha(W/'protocol/runtime_lock.json'),runtime=newhashes,
        project_imports=lock['project_imports'],changed_files=changed,change='Seven stage instruction strings: remove Japanese suffix only',
        exact_original_bytes_reconstructed_by_restoring_strings=True,all_other_runtime_files_byte_identical=True,
        language_amendment_sha256=sha(W/'protocol/english_language_amendment.json'))
    (W/'protocol/runtime_english_lock.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (W/'protocol/runtime_english.diff').write_text(''.join(diffs),encoding='utf-8')
    print(json.dumps(dict(copied=len(newhashes),changed_files=changed,logic_and_gains_unchanged=True,lock_sha256=sha(W/'protocol/runtime_english_lock.json'))))
if __name__=='__main__':main()
