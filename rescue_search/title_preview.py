"""Render a standalone revised title card; leave the completed movie intact."""
from edit_movie import Movie, darken, rect, text, GOLD, WHITE, ROOT

movie = object.__new__(Movie)
im = darken(movie.world(2), .56)
text(im, (108, 220), 'PHYSICAL AI', 25, GOLD, 'en')
rect(im, (65, 208, 73, 716), GOLD)
text(im, (102, 319), '災害救助ドローンの開発', 82, WHITE, 'bold')
text(im, (108, 466), '― 言語指示による自律飛行と人物捜索 ―', 35, WHITE)
text(im, (108, 900), 'SmolVLA  ×  ArduPilot', 29, GOLD, 'en')
out = ROOT / 'output/video/title_bar_restored_preview.png'
im.save(out)
print(out)
