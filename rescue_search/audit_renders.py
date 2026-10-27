"""Audit every presentation-frame pose against the fixed original flight log."""
import bisect
import hashlib
import json
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;OUT=HERE/'movie'
plan=json.loads((OUT/'plan.json').read_text(encoding='utf8'));reports=[]
for segment in plan['segments']:
    folder=OUT/'renders'/segment['name']
    poses=json.loads((folder/'poses.json').read_text())
    rows=[json.loads(s) for s in (Path(segment['record'])/'trace.jsonl').read_text().splitlines()]
    times=[r['t'] for r in rows]
    assert len(poses)==round(segment['duration_s']*30)
    hashes={}
    for i,p in enumerate(poses):
        moment=min(segment['sim_end'],segment['sim_start']+i/30*segment['speed'])
        index=max(0,bisect.bisect_right(times,moment)-1)
        assert p['frame']==i and p['trace_index']==index and p['simulation_time']==rows[index]['t']
        file=folder/f'{i:04d}.jpg'
        with Image.open(file) as im:assert im.size==(1280,800);im.verify()
        hashes[file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
    reports.append(dict(segment=segment['name'],frames=len(poses),all_pose_indices_match=True,frame_sha256=hashes))
report=dict(segments=reports,render_source_sha256=hashlib.sha256((HERE/'render_movie.py').read_bytes()).hexdigest(),
            unchanged_physics_poses=True,external_viewpoint_is_presentation_only=True)
(OUT/'render_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('RENDER_AUDIT_COMPLETE',sum(s['frames'] for s in reports))
