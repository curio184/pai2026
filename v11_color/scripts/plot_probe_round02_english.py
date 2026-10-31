import json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PIL import Image
W=Path(__file__).resolve().parents[1]
font=FontProperties(fname='C:/Windows/Fonts/BIZ-UDGothicR.ttc')
plan=json.loads((W/'protocol/round02_english.json').read_text(encoding='utf-8'));probe=json.loads((W/'protocol/static_probe_round02_english.json').read_text(encoding='utf-8'))
rows=[json.loads(l) for l in (W/'probe_round02_english/outputs/raw_outputs.jsonl').read_text(encoding='utf-8').splitlines()]
layouts={l['name']:l for l in plan['heldout_layouts']};(W/'figures_round02_english').mkdir(exist_ok=True)
for fid in probe['figure_ids']:
    f=probe['frames'][fid];pos=np.asarray(layouts[f['scene']]['positions'])[:,:2];q=np.asarray(f['qpos'])
    fig,axes=plt.subplots(1,3,figsize=(12,3.6),gridspec_kw={'width_ratios':[1.15,1,1]});fig.patch.set_facecolor('white')
    axes[0].imshow(Image.open(W/'probe_round02_english/images'/f'{fid:05d}.jpg'));axes[0].axis('off');axes[0].set_title('VLAへの入力画像',fontproperties=font,fontsize=15)
    for ax,version in zip(axes[1:],['v1.0','v1.1']):
        rr=[r for r in rows if r['model']==version and r['frame']['id']==fid and r['prompt_group']=='runtime_english'];assert len(rr)==2
        ax.scatter([q[0]],[q[1]],color='#102C38',marker='^',s=65,zorder=5)
        for row in rr:
            color=row['color'];paint='#167CCA' if color=='blue' else '#D44946';actor=f['blue_actor'] if color=='blue' else 1-f['blue_actor'];target=pos[actor]+[-.9,0]
            ax.scatter([target[0]],[target[1]],s=75,color=paint,marker='o',alpha=.6)
            v=np.asarray(row['world_horizontal']);norm=np.linalg.norm(v)
            if norm>=.02:
                v=v/norm*1.3;ax.annotate('',xy=q[:2]+v,xytext=q[:2],arrowprops=dict(arrowstyle='->',lw=2.5,color=paint))
            else:ax.scatter([q[0]],[q[1]],s=170,facecolors='none',edgecolors=paint,linewidths=2)
        ax.set_title(version,fontproperties=font,fontsize=16);ax.set_xlim(0,3.3);ax.set_ylim(-1.35,1.35);ax.set_aspect('equal');ax.grid(alpha=.15)
        ax.set_xticks([]);ax.set_yticks([])
        for spine in ax.spines.values():spine.set_color('#D4DFE1')
    fig.text(.5,.045,'矢印：指示した色ごとの水平速度の向き　●：各人物の前の目標点　▲：機体',fontproperties=font,ha='center',fontsize=12,color='#52656D')
    fig.subplots_adjust(left=.015,right=.985,top=.87,bottom=.16,wspace=.15)
    fig.savefig(W/'figures_round02_english'/f'probe_{fid:02d}.png',dpi=180,bbox_inches='tight');plt.close(fig)
