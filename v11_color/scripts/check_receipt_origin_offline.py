"""Check existing execution option on saved outputs, without a flight or VLA."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

W=Path(__file__).resolve().parents[1]
source=W/'runtime_navfocus/search_link.py'
digest=hashlib.sha256(source.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('review_existing_search_link',source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
record=W/'runs/navfocus_final/NFH13_v1.1/record/vla_link_events.json'
events=json.loads(record.read_text(encoding='utf-8'))
packet=next(e for e in events if e.get('event')=='inference' and e['id']==70)
prompt=packet['instruction'];capture=packet['sim_time_capture'];receipt=capture+1.
checks={}
gate=module.ActionGate(chunk_origin='receipt')
action,status=gate.apply(packet,receipt,prompt,True)
checks['starts_at_zero_after_one_second_old_image']=status=='policy' and gate.selected_chunk_index==0
checks['preserves_first_four_policy_components']=bool(np.allclose(action[:4],packet['action_chunk'][0][:4]))
action,status=gate.apply(packet,receipt+.25,prompt,True)
checks['advances_from_receipt_not_capture']=status=='policy' and gate.selected_chunk_index==2
new_packet=copy.deepcopy(packet);new_packet.update(id=71,sim_time_capture=capture+.8)
action,status=gate.apply(new_packet,receipt+.8,prompt,True)
checks['new_packet_resets_to_zero']=status=='policy' and gate.selected_chunk_index==0
action,status=gate.apply(new_packet,new_packet['sim_time_capture']+2.51,prompt,True)
checks['stale_camera_still_hovers_after_2_5s']=status=='stale_hover' and bool(np.all(action==0))
action,status=gate.apply(new_packet,new_packet['sim_time_capture']+8.01,prompt,True)
checks['watchdog_still_lands_after_8s']=status=='watchdog_land' and action[5]==1 and bool(np.all(action[:5]==0))
gate=module.ActionGate(chunk_origin='receipt')
_,status=gate.apply(packet,receipt,'Different instruction.',True)
checks['old_instruction_rejected']=status=='old_instruction'
legacy=module.ActionGate(chunk_origin='split')
old_action,status=legacy.apply(packet,receipt,prompt,True)
checks['comparison_confirms_existing_split_skips_prefix']=status=='policy' and legacy.selected_chunk_index==10 and legacy.selected_yaw_chunk_index==0
checks['source_unchanged']=hashlib.sha256(source.read_bytes()).hexdigest()==digest
assert all(checks.values()),checks
report=dict(scope='Software contract check only; no flight, inference, training, runtime edits or scoring changes.',
    all_checks_passed=True,checks=checks,source_sha256=digest,
    saved_packet_file=str(record.relative_to(W)),saved_packet_sha256=hashlib.sha256(record.read_bytes()).hexdigest(),
    packet_id=70,receipt_horizontal_norm_m_s=float(np.linalg.norm(packet['action_chunk'][0][:2])),
    split_horizontal_norm_m_s=float(np.linalg.norm(old_action[:2])),
    caveat='Using a recorded packet on a synthetic clock proves code behavior, not successful flight under the proposed setting.')
(W/'reports/receipt_origin_offline_check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
