"""Monitor the bounded execution alias without starting any guest process."""
import json,sys
from pathlib import Path
import monitor_train08 as base
W=base.W
original=base.psutil.Process

def main():
    import argparse,shutil,psutil
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--recovery',action='store_true');p.add_argument('--brief',action='store_true');a=p.parse_args()
    script='resume_train08_capped_startup01.py' if a.recovery else 'pipeline_train08_capped.py'
    result={'free_gib':shutil.disk_usage(W).free/1024**3}
    try:
        process=original(a.pid)
        assert any(x.replace('\\','/').endswith('v11_color/scripts/'+script) for x in process.cmdline())
        result.update(pipeline_live=process.is_running(),children=[{'pid':x.pid,'name':x.name()} for x in process.children(recursive=True) if x.is_running()])
    except psutil.NoSuchProcess:result['pipeline_live']=False
    state=W/('pipeline_train08_capped_recovery01_status.json' if a.recovery else 'pipeline_train08_capped_status.json')
    if state.exists():result['pipeline']=base.read(state)
    result['suites']={}
    for prefix in ['dev','stress','regression','known_failure','heldout_round02_english']:
        folder=W/'runs'/(prefix+'_train08_en_capped')
        if not folder.exists():continue
        s=folder/'summary.json';v={k:base.read(s)[k] for k in ['completed','planned','successes']} if s.exists() else {'completed':0}
        for f in folder.iterdir():
            if not f.is_dir() or (f/'outcome.json').exists() or (f/'startup_failure.json').exists():continue
            v['active']=f.name
            for name in ['resource_limits','resource_usage']:
                resource=f/(name+'.json')
                if resource.exists():v[name]=base.read(resource)
            trace=f/'record/trace.jsonl'
            if trace.exists():
                with trace.open('rb') as stream:
                    stream.seek(max(0,trace.stat().st_size-16384));lines=stream.read().splitlines()
                for line in reversed(lines[1:]):
                    try:last=json.loads(line)
                    except (ValueError,UnicodeDecodeError):continue
                    v['phase']=last.get('phase');v['sim_time']=last.get('t');break
        result['suites'][prefix]=v
    if a.brief:
        result.pop('children',None)
        for v in result['suites'].values():
            initial=v.pop('resource_limits',None);usage=v.pop('resource_usage',None)
            if initial:v['limits_confirmed']={n:initial['limits'][n] for n in ['cpu.max','memory.max']}
            if usage:v['peak_bytes']=usage['measurements']['memory.peak']
    print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
