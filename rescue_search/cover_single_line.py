"""One-line title variant, using the existing native title-card layout."""
from cover_editorial import backdrop, put, tracked, font, GOLD, OUT
from PIL import Image, ImageDraw

im=backdrop('column')
d=ImageDraw.Draw(im)
x=140
d.rectangle((88,314,94,555),fill=GOLD)
tracked(d,'PHYSICAL AI',(x,342),font(25,'en'),GOLD,2.2)
put(d,'災害救助ドローン',x,460,82,'bold')
put(d,'― VLAによる自律飛行と被災者捜索 ―',x,546,31,fill='#dae1e2')
d.line((x,625,796,625),fill='#39484e',width=1)
for i,(name,role) in enumerate([('SmolVLA','（動作生成）'),('ArduPilot','（姿勢制御）'),('StampFly','（ドローン）')]):
    center=240+i*228
    put(d,name,center-font(33,'en').getlength(name)/2,695,33,'en',GOLD)
    put(d,role,center-font(25).getlength(role)/2,739,25,fill='#c4cfd2')
    if i<2:
        put(d,'×',center+114-font(24).getlength('×')/2,720,24,fill='#819097')
im.save(OUT/'cover_single_line.png')
im.resize((960,540),Image.Resampling.LANCZOS).save(OUT/'cover_single_line_540p.png')
print(OUT/'cover_single_line.png')
