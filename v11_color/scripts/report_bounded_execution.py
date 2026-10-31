"""Summarize resource receipts and separately identify non-performance attempts.

Reads original evidence; does not change scores or the frozen acceptance gates.
"""
import hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]

def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def counters(text):return {line.split()[0]:int(line.split()[1]) for line in text.splitlines()}

def main():
    plan=read(W/'protocol/bounded_execution.json');rows=[];exceptions=[]
    for f in sorted((W/'runs').glob('*/*/resource_usage.json')):
        folder=f.parent;initial=read(folder/'resource_limits.json');usage=read(f);m=usage['measurements']
        q,period=m['cpu.max'].split();events=counters(m['memory.events']);cpu=counters(m['cpu.stat'])
        assert q!='max' and int(q)/int(period)<=plan['cpu_quota_cores']
        assert int(m['memory.max'])==plan['memory_max_bytes']
        assert initial['nice']>=plan['nice'] and initial['uid']==1000
        row={'record':folder.relative_to(W).as_posix(),'exit':usage['exit'],
             'peak_bytes':int(m['memory.peak']),'cpu_seconds':cpu['usage_usec']/1e6,
             'throttled_seconds':cpu['throttled_usec']/1e6,'oom_kill':events['oom_kill'],
             'usage_sha256':sha(f),'limits_sha256':sha(folder/'resource_limits.json')}
        if (folder/'outcome.json').exists():row['success']=read(folder/'outcome.json')['success']
        rows.append(row)
    for f in sorted((W/'runs').glob('*/*/outcome.json')):
        result=read(f)
        if result.get('user_interrupted'):
            exceptions.append(dict(kind='user_interrupted_flight',record=f.parent.relative_to(W).as_posix(),
                success=result['success'],normal_performance_trial=False,outcome_sha256=sha(f)))
    for f in sorted((W/'runs').glob('*/*/startup_failure.json')):
        exceptions.append(dict(kind='preflight_startup_failure',record=f.parent.relative_to(W).as_posix(),
            normal_performance_trial=False,flight_started=False,receipt_sha256=sha(f)))
    result=dict(resource_protocol_sha256=sha(W/'protocol/bounded_execution.json'),
        completed_bounded_flights=len(rows),maximum_peak_bytes=max((r['peak_bytes'] for r in rows),default=0),
        resource_oom_kills=sum(r['oom_kill'] for r in rows),cases=rows,non_performance_attempts=exceptions,
        scope='WSL simulation process trees only; Windows inference/rendering and unrelated WSL jobs are outside these receipts.',
        scores_modified=False,old_and_new_execution_conditions_not_pooled=True)
    output=W/'reports/bounded_execution_summary.json';output.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['cases','non_performance_attempts']},ensure_ascii=False))
    index=W/'ALL_TRIALS_ROUND02_ENGLISH.md'
    if index.exists():
        text=index.read_text(encoding='utf8');marker='## 資源制限と中断・起動エラー'
        text=text.split(marker)[0].rstrip()+'\n\n'+marker+'\n\n'
        text+='WSLの本プロジェクト処理を4 CPU・8GiB以下に制限し、優先度を下げて1件ずつ実行しています。条件導入前後を合算した性能評価は行いません。`train08_en_capped` は `train08_en` と同じ重みを使う実行用の名前です。\n\n'
        text+='| 区分 | 記録 | 扱い |\n| --- | --- | --- |\n'
        for row in exceptions:
            name='利用者の指示による中断' if row['kind']=='user_interrupted_flight' else '飛行前の起動エラー'
            file='outcome.json' if row['kind']=='user_interrupted_flight' else 'startup_failure.json'
            note='採点は不成功。通常の性能試験とは分ける' if row['kind']=='user_interrupted_flight' else '飛行・推論は未開始。成功率の分母に含めない'
            text+=f"| {name} | [元記録]({row['record']}/{file}) | {note} |\n"
        text+='\n各試験の `resource_limits.json` と `resource_usage.json` に上限と使用量を記録しています。[集計](reports/bounded_execution_summary.json)\n'
        index.write_text(text,encoding='utf8')
if __name__=='__main__':main()
