"""Reserve unseen final layouts before development results; no policy execution."""
import datetime,json,hashlib
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1]
def main():
    seed=202610310601;rng=np.random.default_rng(seed);layouts=[]
    for i in range(4):
        positions=[[float(rng.uniform(2.65,3.65)),float(rng.uniform(.52,1.1)),0.],
                   [float(rng.uniform(2.65,3.65)),float(rng.uniform(-1.1,-.52)),0.]]
        layouts.append(dict(name=f'heldout_rebuild_{i+1:02d}',positions=positions,blue_actor=i%2))
    plan=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),layout_seed=seed,
        heldout_layouts=layouts,layout_sampling=dict(x=[2.65,3.65],positive_y=[.52,1.1],negative_y=[-1.1,-.52],
        filtering='None. Retain all four generated layouts.',shirt_assignment='alternating actors'),
        use='Reserved final evaluation only. Not to be rendered/inferred for development or added to training.',
        final_runs='both models, both colors, two repetitions per layout, fixed start jitter seeds; register exact cases and implementation before flights.',
        physical_acceptance='Unchanged <=.25m, <=.08m/s for >=3s, all other existing physical and task criteria retained.',
        threshold='v1.1 >=14/16, each color>=7/8, each layout>=3/4; video9/9 and knownswap1/1.',
        prior_layouts_status='Previous heldout_navfocus layouts now development, not fresh final evidence.')
    with (W/'protocol/rebuild_final_layouts.json').open('x',encoding='utf-8') as f:json.dump(plan,f,indent=2)
    print(json.dumps(dict(reserved_layouts=4,policy_executions=0)))
if __name__=='__main__':main()
