"""Frozen image-only person detection and torso clothing color evidence."""
import hashlib
import time
from pathlib import Path
import cv2
import numpy as np
import torch
from torchvision.models.detection import ssdlite320_mobilenet_v3_large, SSDLite320_MobileNet_V3_Large_Weights
from torchvision.transforms.functional import to_tensor


class PersonPerception:
    def __init__(self):
        torch.set_num_threads(4)
        weights = SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
        self.model = ssdlite320_mobilenet_v3_large(weights=weights).eval().cpu()
        file = Path(torch.hub.get_dir()) / 'checkpoints' / weights.url.rsplit('/', 1)[-1]
        self.provenance = dict(model='torchvision SSDlite320 MobileNet V3 Large',
                               weights_url=weights.url, weights_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                               person_threshold=.65, torso_roi=[.2,.18,.8,.60],
                               color_fraction_threshold=.20, color_margin=.12,
                               source='RGB only; no simulator metadata')

    @torch.inference_mode()
    def detect(self, image):
        start = time.perf_counter()
        rgb = np.asarray(image.convert('RGB'))
        h, w = rgb.shape[:2]
        output = self.model([to_tensor(image)])[0]
        persons = []
        for box, score, label in zip(output['boxes'], output['scores'], output['labels']):
            if int(label) != 1 or float(score) < .65:
                continue
            x1,y1,x2,y2 = box.tolist()
            xa,xb = max(0,int(x1+.2*(x2-x1))), min(w,int(x1+.8*(x2-x1)))
            ya,yb = max(0,int(y1+.18*(y2-y1))), min(h,int(y1+.6*(y2-y1)))
            if xb-xa < 4 or yb-ya < 4:
                continue
            hsv=cv2.cvtColor(rgb[ya:yb,xa:xb],cv2.COLOR_RGB2HSV)
            hue,sat,val = hsv[:,:,0],hsv[:,:,1],hsv[:,:,2]
            valid=(sat>=55)&(val>=35)
            blue=float(np.mean(valid&(hue>=90)&(hue<=130)))
            red=float(np.mean(valid&((hue<=12)|(hue>=168))))
            color='blue' if blue>=.2 and blue-red>=.12 else 'red' if red>=.2 and red-blue>=.12 else 'unknown'
            persons.append(dict(bbox=[x1,y1,x2,y2], confidence=float(score), torso_roi=[xa,ya,xb,yb],
                                clothing_color=color,blue_fraction=blue,red_fraction=red))
        return dict(persons=persons, elapsed_s=time.perf_counter()-start, **self.provenance)


class VisualConfirmation:
    """Three distinct recent model input images; no target locations."""
    def __init__(self, color):
        self.color=color
        self.hits=[]
        self.last_id=None
        self.last_seen=None

    def update(self, packet, now):
        if packet is None or now-packet['sim_time_capture']>2.5:
            return False
        if packet['id'] != self.last_id:
            self.last_id=packet['id']
            candidates=[p for p in packet.get('perception',{}).get('persons',[]) if p['clothing_color']==self.color]
            if len(candidates)==1:
                current=candidates[0]
                if self.hits:
                    a=self.hits[-1]['person']['bbox']; b=current['bbox']
                    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
                    union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-intersection
                    if intersection/max(union,1)<.20:
                        self.hits=[]
                self.last_seen=packet['sim_time_capture']
                self.hits.append(dict(id=packet['id'],t=packet['sim_time_capture'], image_file=packet['image_file'],
                                      image_sha256=packet['image_sha256'],person=current))
            else:
                self.hits=[]
        self.hits=[h for h in self.hits if now-h['t']<=5]
        return len(self.hits)>=3 and self.hits[-1]['t']-self.hits[-3]['t']>=.4
