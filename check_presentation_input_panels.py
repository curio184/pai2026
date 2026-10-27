"""Check that sampled decoded movie panels contain the synchronized actual inputs."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from make_demo_video import FlightRecord
ROOT=Path(__file__).resolve().parent
def main():
    plan=json.loads((ROOT/'tmp/rescue_presentation/plan.json').read_text(encoding='utf8'))
    qa=json.loads((ROOT/'output/video/presentation_qa.json').read_text(encoding='utf8'))
    records={p:FlightRecord(ROOT/plan['records']/p) for p in ['blue','red','turns','left']}
    results=[]
    for i,t in enumerate(qa['extracted_times_s'],1):
        flight=next((f for f in plan['flights'] if f['start']+.22<t<f['end']-.04),None)
        if flight is None:continue
        moment=min(flight['sim_end'],flight['sim_start']+max(0,t-flight['start']-flight['lead_s'])*flight['speed'])
        _,row,packet,onboard=records[flight['profile']].at(moment)
        if onboard is None:continue
        decoded=Image.open(ROOT/f'tmp/rescue_presentation/final_qa/frame_{i:03}.jpg').convert('RGB').crop((1372,262,1820,598))
        expected=onboard.resize((448,336),Image.Resampling.NEAREST)
        mae=float(np.abs(np.asarray(decoded,dtype=float)-np.asarray(expected,dtype=float)).mean())
        results.append(dict(video_time_s=t,profile=flight['profile'],simulation_time_s=row['t'],image_file=packet['image_file'],image_sha256=packet['image_sha256'],decoded_pixel_mean_absolute_error=mae))
    # Lossy H.264 and the QA JPEG add compression error; a wrong image is not permitted.
    success=bool(results) and all(r['decoded_pixel_mean_absolute_error']<8 for r in results) and {r['profile'] for r in results}==set(records)
    output=dict(success=success,video_sha256=qa['sha256'],sampled_panels=len(results),maximum_pixel_mae=max(r['decoded_pixel_mean_absolute_error'] for r in results),threshold_pixel_mae=8,samples=results)
    (ROOT/'output/video/presentation_input_panel_review.json').write_text(json.dumps(output,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in output.items() if k!='samples'}),flush=True)
    assert success
if __name__=='__main__':main()
