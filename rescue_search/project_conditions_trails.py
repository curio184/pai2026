"""Reuse the verified camera projection for each tested optical environment."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
source=(HERE/'project_demo_trail.py').read_text(encoding='utf8')
for condition in ['fog_light','fog_dense','dust']:
 code=source.replace("HERE/'demo_movie'","HERE/'conditions_movie'/condition")
 code=code.replace("OUT.mkdir(exist_ok=True)","OUT.mkdir(parents=True,exist_ok=True)")
 code=code.replace("'runs/eval03/clear_blue'",f"'runs/eval03/{condition}_blue'")
 code=code.replace("'movie/renders/demo/poses.json'",f"'movie/renders/{condition}/poses.json'")
 code=code.replace("'scenes/clear/scene.blend'",f"'scenes/{condition}/scene.blend'")
 exec(compile(code,__file__,'exec'),{'__file__':__file__,'condition':condition})
