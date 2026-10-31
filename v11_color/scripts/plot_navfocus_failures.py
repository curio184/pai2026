"""Plot every failed v1.1 approach from saved records, never new trials."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

W=Path(__file__).resolve().parents[1]
FONT=FontProperties(fname='C:/Windows/Fonts/BIZ-UDGothicR.ttc')
def read(p):return json.loads(p.read_text(encoding='utf-8'))

def main():
    failures=read(W/'reports/navfocus_failure_details.json')['failures']
    output=W/'reports/navfocus_failure_figures';output.mkdir(exist_ok=True)
    rows_out=[]
    for case in failures:
        if case['case']['model']!='v1.1' or not case['target']:continue
        record=W/case['record']/'record';score=read(record/'physical_score.json');color=case['case'].get('color',case['case'].get('profile'))
        rows=[json.loads(line) for line in (record/'trace.jsonl').open(encoding='utf-8')]
        nav=[r for r in rows if (r.get('execution_owner') or {}).get('owner')=='VLA']
        if not nav:continue
        span=[r for r in rows if nav[0]['t']<=r['t']<=nav[-1]['t']]
        t=np.asarray([r['t'] for r in span]);truth=np.asarray([r['truth'] for r in span]);acts=np.asarray([r['model_action'] for r in span])
        owned=np.asarray([(r.get('execution_owner') or {}).get('owner')=='VLA' for r in span]);acts[~owned]=np.nan
        goal=np.asarray(score['goal_holds'][color]['goal_scene_xy_m']);distance=np.linalg.norm(truth[:,[2,1]]-goal,axis=1)
        speed=np.linalg.norm(truth[:,4:6],axis=1);height=-truth[:,3]
        fig,axes=plt.subplots(3,1,figsize=(9,6.5),sharex=True);fig.patch.set_facecolor('white')
        axes[0].plot(t,distance,color='#087F7F');axes[0].axhline(.25,color='#D44946',ls='--',label='許容距離 0.25 m')
        axes[0].set_ylabel('目標点までの距離 (m)',fontproperties=FONT);axes[0].legend(prop=FONT)
        axes[1].plot(t,speed,color='#087F7F',label='機体の実速度');axes[1].plot(t,np.linalg.norm(acts[:,:2],axis=1),color='#CBA96C',alpha=.8,label='VLAの速度要求')
        axes[1].axhline(.08,color='#D44946',ls='--',label='停止判定 0.08 m/s');axes[1].set_ylabel('水平速度 (m/s)',fontproperties=FONT);axes[1].legend(prop=FONT,ncol=3,fontsize=8)
        valid=(distance<=.25)&(speed<=.08)&(height>=.8)&(height<=1.25)&np.asarray([r['phase']==color for r in span])
        axes[2].fill_between(t,0,valid.astype(float),step='post',color='#087F7F',alpha=.6)
        axes[2].set_ylabel('距離・速度・高度が成立',fontproperties=FONT);axes[2].set_ylim(-.05,1.1);axes[2].set_yticks([0,1]);axes[2].set_xlabel('シミュレーション時刻 (秒)',fontproperties=FONT)
        for ax in axes:
            ax.grid(alpha=.15);ax.axvline(t[-1],color='#102C38',ls=':')
        held=score['goal_holds'][color]['physical_hold']['duration_s']
        fig.suptitle(f"{case['case']['id']} / {color}：条件内での最長停止 {held:.2f} 秒（必要時間 3 秒）",fontproperties=FONT,fontsize=13)
        fig.text(.5,.01,'記録の事後解析。縦の点線はVLA接近工程の終了。真値は採点・解析のみに利用。',ha='center',fontproperties=FONT,fontsize=9)
        fig.tight_layout(rect=[0,.035,1,.96]);dest=output/(case['case']['id']+'.png');fig.savefig(dest,dpi=140);plt.close(fig)
        rows_out.append(dict(case=case['case'],figure=dest.relative_to(W).as_posix()))
    (output/'index.json').write_text(json.dumps(rows_out,indent=2),encoding='utf-8');print(json.dumps(dict(figures=len(rows_out))))
if __name__=='__main__':main()
