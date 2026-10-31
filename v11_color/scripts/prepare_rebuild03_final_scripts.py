"""Prepare guarded final tools for the pipeline/5-step runtime; does not run evaluation."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def write(name,s):ast.parse(s);(W/'scripts'/name).write_text(s,encoding='utf-8')
def main():
    s=(W/'scripts/prepare_rebuild01_final.py').read_text(encoding='utf-8').replace('rebuild01','rebuild03')
    start=s.index("    initial=read(W/'runs/rebuild03_dev/summary.json')")
    end=s.index("    base=read(W/'protocol/rebuild03_dev.json')",start)
    s=s[:start]+'''    development=read(W/'runs/rebuild03_dev/summary.json')
    assert development['completed']==5 and all(r['success'] for r in development['cases'])
'''+s[end:]
    # Templates come from the established navfocus static figures. Runtime names
    # are changed to the final rebuild03 paths by the existing mapping loop.
    marker="        ast.parse(s);(W/'scripts'/after).write_text(s,encoding='utf-8')"
    assert marker in s
    s=s.replace(marker,"        if before=='run_probe_navfocus.py':\n            s=s.replace('model=DroneVLA(ck)','model=DroneVLA(ck);model.policy.model.config.num_steps=5')\n            s=s.replace('row=dict(model=version,','row=dict(num_steps=5,model=version,')\n"+marker)
    s=s.replace("configuration='rebuild03',", "configuration='rebuild03',flow_steps=5,")
    s=s.replace('only after all26 development cases pass','only after the five pipeline diagnostics pass')
    write('prepare_rebuild03_final.py',s)
    s=(W/'scripts/run_rebuild01_final.py').read_text(encoding='utf-8').replace('rebuild01','rebuild03')
    write('run_rebuild03_final.py',s)
    s=(W/'scripts/verify_probe_rebuild01.py').read_text(encoding='utf-8').replace('rebuild01','rebuild03')
    s=s.replace("            f=row['frame'];assert f==plan['frames'][f['id']]", "            assert row['num_steps']==5\n            f=row['frame'];assert f==plan['frames'][f['id']]")
    write('verify_probe_rebuild03.py',s)
    s=(W/'scripts/summarize_rebuild01.py').read_text(encoding='utf-8').replace('rebuild01','rebuild03')
    s=s.replace("for suite in ['rebuild03_dev','rebuild03_expanded']:","for suite in ['rebuild01_dev','rebuild01_expanded','rebuild02_dev','rebuild03_dev']:")
    s=s.replace("assert len(history)==405 and len({r['record'] for r in history})==405","assert len(history)==395 and len({r['record'] for r in history})==395")
    s=s.replace("configuration='rebuild03',", "configuration='rebuild03',flow_steps=5,")
    write('summarize_rebuild03.py',s)
    for before,after in [('describe_rebuild01_failures.py','describe_rebuild03_failures.py'),('trial_index_rebuild01.py','trial_index_rebuild03.py')]:
        s=(W/'scripts'/before).read_text(encoding='utf-8').replace('REBUILD01','REBUILD03').replace('rebuild01','rebuild03');write(after,s)
    print('Guarded final tools prepared; reserved holdouts remain unused.')
if __name__=='__main__':main()
