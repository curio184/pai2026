"""Reassemble accepted sections after extending the demonstration chapter card."""
from ending_movie import *
join(PARTS,[92,26,27],PREFIX,'corrected_prefix')
join(PARTS+[DEST],[92,26,27,30],COMBINED,'final')
join([PARTS[0],PARTS[2]],[92,27],ROOT/'output/video/rescue_drone_through_conditions.mp4','through_conditions')
p=OUT/'source_evidence.json'
e=json.loads(p.read_text(encoding='utf8'))
e.update(combined_duration_s=175,source_segments_sha256={str(p):sha(p) for p in PARTS},demonstration_chapter_card_s=4)
p.write_text(json.dumps(e,ensure_ascii=False,indent=2),encoding='utf8')
print('ASSEMBLY_COMPLETE',flush=True)
