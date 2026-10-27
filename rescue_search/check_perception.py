import json
from pathlib import Path
from PIL import Image, ImageDraw
from perception import PersonPerception
here=Path(__file__).resolve().parent
model=PersonPerception()
results=[]
for condition in ['clear','fog_light','fog_dense','dust']:
    for view in ['initial','forward']:
        file=here/'scenes'/condition/(view+'.png')
        image=Image.open(file).convert('RGB')
        detection=model.detect(image)
        results.append(dict(condition=condition,view=view,**detection))
        draw=ImageDraw.Draw(image)
        for p in detection['persons']:
            draw.rectangle(p['bbox'],outline=p['clothing_color'] if p['clothing_color']!='unknown' else 'white',width=2)
            draw.text(p['bbox'][:2],p['clothing_color'],fill='white')
        image.save(here/f'color_check_{condition}_{view}.jpg')
# Explicit blue-only objects must not be called people.
for name in ['blue_rectangle','blank']:
    image=Image.new('RGB',(320,240),(100,100,100))
    if name=='blue_rectangle':ImageDraw.Draw(image).rectangle([90,50,200,200],fill=(20,60,220))
    results.append(dict(condition=name,view='negative',**model.detect(image)))
(here/'perception_checks.json').write_text(json.dumps(results,indent=2),encoding='utf8')
print(json.dumps([dict(condition=r['condition'],view=r['view'],persons=r['persons']) for r in results],indent=2))
