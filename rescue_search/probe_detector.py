from pathlib import Path
import torch,json,time,hashlib
from PIL import Image,ImageDraw
from torchvision.models.detection import ssdlite320_mobilenet_v3_large,SSDLite320_MobileNet_V3_Large_Weights
from torchvision.transforms.functional import to_tensor
ROOT=Path.cwd();OUT=ROOT/'tmp/rescue_search'
torch.set_num_threads(4)
weights=SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
model=ssdlite320_mobilenet_v3_large(weights=weights).eval()
records=ROOT/'outputs/ardupilot/realism_precision_03'
results=[]
with torch.inference_mode():
    for profile in ['blue','red','turns']:
        files=sorted((records/profile/'observations').glob('*.jpg'))
        for i in [0,len(files)//3,len(files)//2,2*len(files)//3]:
            im=Image.open(files[i]).convert('RGB');at=time.monotonic();result=model([to_tensor(im)])[0]
            keep=[dict(box=[round(float(v),1) for v in box],score=float(score),label=int(label)) for box,score,label in zip(result['boxes'],result['scores'],result['labels']) if label==1 and score>.35]
            row=dict(profile=profile,file=files[i].name,people=keep,seconds=time.monotonic()-at);results.append(row)
            draw=ImageDraw.Draw(im)
            for k in keep:draw.rectangle(k['box'],outline='lime',width=2)
            im.resize((640,480)).save(OUT/f'detector_{profile}_{i:03}.jpg')
(OUT/'detector_probe.json').write_text(json.dumps(dict(weights_url=weights.url,categories=weights.meta['categories'],results=results),indent=2),encoding='utf8')
print(json.dumps(results,indent=2))
