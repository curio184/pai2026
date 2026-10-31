"""Read-only monitoring of the known pipeline, saved progress, and completed results."""
import argparse,json,shutil
from pathlib import Path
import psutil
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pid',type=int,required=True);a=parser.parse_args()
    r=dict(free_gib=shutil.disk_usage(W).free/1024**3)
    try:
        p=psutil.Process(a.pid);cmd=p.cmdline()
        assert any(x.replace('\\','/').endswith('v11_color/scripts/pipeline_train16_en.py') for x in cmd), 'PID belongs to a different process'
        r['pipeline_live']=p.is_running();r['pipeline_process_created']=p.create_time()
        r['children']=[dict(pid=x.pid,name=x.name()) for x in p.children(recursive=True) if x.is_running()]
    except psutil.NoSuchProcess:r['pipeline_live']=False
    state=W/'pipeline_train16_en_status.json'
    if state.exists():r['pipeline']=read(state)
    model=W/'models/train16_en'
    for name in ['progress','result','failure']:
        f=model/(name+'.json')
        if f.exists():r['training_'+name]=read(f)
    r['suites']={}
    for prefix in ['dev','stress','regression','known_failure','heldout_round02_english']:
        folder=W/'runs'/(prefix+'_train16_en')
        if not folder.exists():continue
        summary=folder/'summary.json'
        v={k:read(summary)[k] for k in ['completed','planned','successes']} if summary.exists() else dict(completed=0)
        plan=folder/'suite_plan.json'
        if plan.exists():
            for case in read(plan)['cases']:
                f=folder/(case['id']+'_'+case['model'])
                if f.exists() and not (f/'outcome.json').exists():
                    v['in_progress']=case['id']+'_'+case['model']
                    trace=f/'record/trace.jsonl'
                    if trace.exists():
                        with trace.open('rb') as stream:
                            stream.seek(max(0,trace.stat().st_size-16384));lines=stream.read().splitlines()
                        for line in reversed(lines[1:]):
                            try:last=json.loads(line)
                            except (ValueError,UnicodeDecodeError):continue
                            v['last_recorded_phase']=last.get('phase');v['last_recorded_sim_time']=last.get('t');break
                    break
        r['suites'][prefix]=v
    print(json.dumps(r,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
