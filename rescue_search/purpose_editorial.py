"""Native typography for the purpose slide of the existing local video."""
from cover_editorial import backdrop,put,font,GOLD
from finish_cover import ROOT
from PIL import Image,ImageDraw
import json

OUT=ROOT/'output/video/purpose_editorial'
OUT.mkdir(exist_ok=True)
im=backdrop('column');d=ImageDraw.Draw(im)
x=140
items=[
    ('災害救助ドローンとは',284,25,'bold',GOLD),
    ('人が立ち入りにくい建物を、',397,52,'bold','#f4f4ee'),
    ('小型ドローンで捜索',471,52,'bold','#f4f4ee'),
    ('言葉の指示で捜索を任せ、',635,52,'bold','#f4f4ee'),
    ('操縦の負担を減らす',709,52,'bold','#f4f4ee'),
]
boxes=[]
for text,y,size,kind,color in items:
    bbox=d.textbbox((x,y),text,font=font(size,kind),anchor='ls')
    assert bbox[2]<910 and bbox[3]<940,(text,bbox)
    put(d,text,x,y,size,kind,color)
    boxes.append(dict(text=text,bbox=bbox))
im.save(OUT/'purpose_uniform_type.png')
im.resize((960,540),Image.Resampling.LANCZOS).save(OUT/'purpose_uniform_type_540p.png')
(OUT/'purpose_uniform_type.json').write_text(json.dumps(dict(
    text_boxes=boxes,video_modified=False,
    intent='Two approved messages: search inaccessible buildings with a small drone, and delegate search through language to reduce piloting workload',
    scope_note='This slide describes the intended purpose; demonstrated scope belongs to the demonstration introduction.'
),ensure_ascii=False,indent=2),encoding='utf8')
print(OUT/'purpose_uniform_type.png')
