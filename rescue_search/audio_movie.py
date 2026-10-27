import json
import os
from pathlib import Path
import sys
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);sys.path.insert(0,str(ROOT))
HERE=Path(__file__).resolve().parent;OUT=HERE/'movie'
import make_rescue_presentation_audio as original
def plan():
    movie=json.loads((OUT/'plan.json').read_text(encoding='utf8'))
    sections={s['name']:s for s in movie['timeline']};clips=[]
    def add(at,length,text,caption):
        clips.append(dict(index=len(clips),start=at,max_s=length,text=text,caption=caption,file=f'voice_{len(clips):02}.wav'))
    # The first four seconds deliberately contain music only.
    add(4.5,7.1,'人が近づきにくい場所に、捜索の目を増やす。操縦者の負担も減らしたい。','人が近づきにくい場所に捜索の目を増やし、操縦者の負担を減らす。')
    add(12,7.1,'そのために、言葉で任務を伝える仕組みを作りました。今回は、一機で確かめます。','言葉で捜索の任務を伝える仕組み。今回は1機で検証します。')
    m=sections['mechanism']['start']
    add(m+.4,6.3,'任務の進行はプログラムが管理し、カメラ画像から人物と服の色を確認します。','任務の進行はプログラムが管理。人物検出と服の色の確認を組み合わせます。')
    add(m+7,7.2,'ブイエルエーは、画像と指示、機体の状態から、飛行動作を生成するエーアイです。','VLAは、画像・工程の指示・機体の状態から、飛行動作を生成します。')
    add(m+14.6,6.3,'数秒分の動作をまとめて出力し、飛行制御が機体の姿勢を安定させます。','VLAが数秒分の動作を出力し、飛行制御が機体の姿勢を安定させます。')
    d=sections['demo'];s=movie['scores']['clear'];sim_start=16
    add(d['start']+.4,6.4,'青い服の人を探して。対象は、まだカメラに映っていません。','「青い服の人を探して」。最初は対象の人物がカメラに映っていません。')
    add(d['start']+7.2,4.6,'カメラの向きを変え、室内を見渡します。','カメラの向きを変え、室内を見渡します。')
    found=d['start']+(s['discovery_time_s']-sim_start)/2
    notice=d['start']+(s['notification_time_s']-sim_start)/2
    add(found+.15,min(5.9,notice-found-.4),'青い服の人物を確認。近づいて、その場で停止します。','画像から青い服の人物を確認。接近し、その場で停止します。')
    add(notice+.2,min(6.3,d['end']-notice-.8),'確認した画像を地上のパソコンに記録。このあと着陸し、飛行を終えます。','確認画像を地上PCに記録。その後、着陸して飛行を終えます。')
    c=sections['conditions']['start']
    add(c+.4,7,'霧や粉じんを表現した画像を、ブイエルエーと人物検出の両方に入力して試しました。','霧・粉じんを表現した画像を、VLAと人物検出の両方に入力しました。')
    add(c+8.2,6.8,'同じモデルで、薄い霧、濃い霧、粉じんの各条件を確認しました。','同じモデルで、薄い霧・濃い霧・粉じんの各条件を確認しました。')
    add(c+15.6,7.4,'四つの条件で、発見から着陸まで完了。霧の濃さは、シミュレーション上の設定です。','各条件1回、4条件で完了。霧・粉じんの濃さは、現実の見通せる距離には合わせていません。')
    h=sections['hardware']['start']
    add(h+.4,6.6,'実機への展開も考え、実在する機体と部品を基に、構成を設計しています。','実機への展開に向け、実在する機体と部品を基に構成を設計しています。')
    add(h+7.3,7.1,'映像を無線で地上のパソコンへ。ブイエルエーの出力を、コントローラーから機体へ返します。','カメラ映像を無線で地上PCへ。VLAの出力を、コントローラーから機体へ返します。')
    add(h+14.8,7.1,'実在する部品を使う設計ですが、搭載や通信、実機での飛行は未検証です。','今回はシミュレーションで検証。搭載・電源・通信・実機飛行は未検証です。')
    e=sections['closing']['start']
    add(e+.5,10.1,'見えていない人を探し、確認した画像を届ける。次は、場所や人物を変えた検証と、実機での確認へ進みます。','今回の室内で、捜索から画像の報告まで実現。次は環境を変えた検証と実機での確認です。')
    assert all(a['start']+a['max_s']<=b['start'] for a,b in zip(clips,clips[1:])),[(a['index'],a['start']+a['max_s'],b['start']) for a,b in zip(clips,clips[1:])]
    assert all(c['max_s']>2 for c in clips)
    (OUT/'narration_plan.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding='utf8')
    voice=(ROOT/'tmp/presentation_v2/voice.ps1').read_text(encoding='utf8')
    (OUT/'voice.ps1').write_text(voice,encoding='utf-8-sig')
if __name__=='__main__':
    if sys.argv[1]=='plan':plan()
    else:
        original.TMP=OUT;original.PLAN=json.loads((OUT/'plan.json').read_text(encoding='utf8'))
        # Reuse locally composed music and narration mix; no fabricated microphone sound.
        original.PLAN['flights']=[]
        original.mix()
