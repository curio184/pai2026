import json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
READINGS={
'intro_pan':['さいがいきゅうじょどろーんとは、ひとがたちいりにくいばしょで、ひさいしゃのそうさくをしえんするどろーんです。','こんかいは、ことばによるしじでそうさくをまかせ、そうじゅうのふたんをへらすことをめざしました。'],
'mechanism_movie':['どろーんのひこうをせいぎょするために、ぶいえるえーをりようします。','ぶいえるえーは、かめらえいぞうとことばによるしじから、つぎのどうさをせいせいするえーあいです。','どろーんのえいぞうをむせんでぱそこんへおくり、ぶいえるえーがせいせいしたどうさをひこうしれいとしてかえします。','このやりとりをくりかえすことで、どろーんをじりつてきにせいぎょします。'],
'training_movie_v2':['ぶいえるえーはついかがくしゅうをおこなっています。','いどうやせんかいなどのどうさをていぎし、がぞうやしじ、きたいのじょうたいとたいおうづけています。'],
'demo_movie':['あおいふくのひとをさがして。'],
'red_movie':['あかいふくのひとをさがして。'],
'conditions_movie':['さいがいげんばでは、きりやふんじんでしかいがわるくなることもあります。','そこで、みえかたをかえたじょうけんでも、おなじもでるでそうさくできるかたしかめました。','つうじょうをふくむよっつのじょうけんで、はっけんからちゃくりくまでかんりょうしました。'],
'ending_movie':['じっきへのてんかいをみすえ、じつざいするこがたどろーんとかめら、せいぎょようぱそこんをくみあわせるこうせいをけんとうしています。','とうさいやつうしん、じっきでのひこうは、こんごのけんしょうかだいです。','こんかいは、していしたじんぶつをさがし、かくにんがぞうをほぞんするまでをじつげんしました。','こんごは、かんきょうをかえたけんしょうと、じっきでのかくにんをすすめます。']}
def mora(s):return len(re.sub('[、。ゃゅょぁぃぅぇぉっ]', '',s))+s.count('っ')
if __name__=='__main__':
 for folder,readings in READINGS.items():
  voices=json.loads((HERE/folder/'voice_manifest.json').read_text(encoding='utf8'))
  for i,(v,r) in enumerate(zip(voices,readings)):
   desired=mora(r)/9.5+r.count('、')*.16+.18
   print(folder,i,'mora',mora(r),'duration',v['duration_s'],'rate',round(mora(r)/v['duration_s'],2),'target',round(desired,2),'tempo',round(v['duration_s']/desired,2))
