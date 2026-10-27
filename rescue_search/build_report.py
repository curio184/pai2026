"""Update explanatory PDF to match final search evidence and video."""
from pathlib import Path
import os,json,hashlib
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);HERE=Path(__file__).resolve().parent
movie=json.loads((HERE/'movie/plan.json').read_text(encoding='utf8'))
scores=movie['scores'];records=Path(movie['records'])
assert all(s['success'] for s in scores.values())
# Reuse established, visually reviewed Japanese font, page and table helpers.
original=(ROOT/'build_submission_report.py').read_text(encoding='utf8')
helpers=original[original.index('from html import escape'):original.index("new('言葉で指示する小型救助ドローン'")]
helpers=helpers.replace('ROOT=Path(__file__).resolve().parent','ROOT=Path(os.environ["RESCUE_PROJECT_ROOT"])')
helpers=helpers.replace("OUT=ROOT/'output/pdf/説明資料_PAI最終課題_提出用.pdf'","OUT=ROOT/'output/pdf/説明資料_PAI最終課題_捜索検証版.pdf'")
helpers=helpers.replace("plan=read('tmp/rescue_presentation/plan.json');records=plan['records']\nscores={p:read(records+'/'+p+'/physical_score.json') for p in ['blue','red','turns','left']}\nassert all(s['success'] for s in scores.values())",'')
helpers=helpers.replace("c.setTitle('言葉で指示する小型救助ドローン')","c.setTitle('災害救助ドローンの開発')")
exec(helpers)

new('災害救助ドローンの開発','VLAを用いた飛行制御のシミュレーション')
paragraph('1. 目的と今回の到達点',13,True)
paragraph('人が近づきにくい場所に捜索の目を増やし、機体を1機ずつ操縦する負担を減らすことを目指す。今回は1機・1つの室内で「青い服の人を探して」という任務を受け、対象が映っていない向きから捜索し、人物の確認・接近・停止・画像付きの地上通知・着陸までを実装した。複数機による捜索や救出活動は今回の検証には含まない。')
record=records/'clear_blue';result=json.loads((record/'result.json').read_text());initial=result['search_start_observation']
images=[(record/'observations'/initial['image_file'],'捜索開始時の実入力'),(record/'notification.jpg','地上PCへ報告した実画像')]
top=y
for i,(file,label) in enumerate(images):
    c.drawImage(str(file),LEFT+i*260,top-180,240,180)
    c.setFont('JP',8.5);c.setFillColor(muted);c.drawString(LEFT+i*260,top-195,label)
y=top-219
paragraph('2. 完了条件',13,True)
paragraph('捜索開始時に対象が画角外であること、複数の画像から指定色の人物を確認したこと、人物前の目標点から25cm以内で水平速度0.08m/s以下を3秒以上維持したことを確認する。通知には実際に処理した原画像を添付し、その後に通常の着陸とモーター停止を行う。発見・報告と、飛行終了を区別する。')
paragraph('物理状態の真値はカメラ描画・センサー合成と飛行後の採点に使用する。人物座標や目標距離は、実行中のVLA・人物確認・任務進行には渡さない。初期不可視は原画像と飛行後の画角計算で確認した。',9.4,color=muted)

new('画像で確認し、VLAで飛ぶ','任務の進行・人物の確認・飛行動作・姿勢制御を組み合わせる')
paragraph('3. システムの構成',13,True)
table(['担当','実装と役割'],[
 ['任務の進行','日本語の上位指示を受け、離陸・見回し・人物確認・接近・通知・着陸を管理する。対応する服の色は青と赤。自由な任務計画を生成する機能ではない。'],
 ['人物の確認','学習済みSSDlite人物検出器と上半身の色判定を使用。同色候補が1人で、連続する3画像の人物領域が対応した場合に確認する。見失ったら停止して再確認する。'],
 ['動作の生成','追加学習したSmolVLA。前方RGB画像・工程の指示・9成分の機体情報から、32ステップ×6成分の動作を生成。工程指示は英語・日本語を併記。'],
 ['姿勢制御・物理','ArduPilotが機体を安定化。MuJoCoと公開StampFlyモデルを基に、質量・慣性・モーター・バッテリー・接触等を計算する。'],
 ['画像・通知','Blenderの前方カメラ画像をVLAと人物検出に入力。通知は地上PC内のJSONと原JPEGとして記録し、動画で可視化する。外部メール等の送信はしない。'],
 ],[100,WIDTH-100])
paragraph('4. VLAの学習と実行',13,True)
paragraph(f'直近の追加学習では{data["images"]:,}枚の画像と{data["samples"]:,}件の教師例で4,000ステップ学習した。その前に室内外観への適応を5,000ステップ実施している。本稿の4条件では同じ保存済み最終モデルを使用し、今回の捜索処理追加に伴う再学習は行っていない。')
paragraph('出力は前後・左右・上下の速度、回転速度、離陸・着陸要求の6成分。0.1秒間隔で3.2秒分を生成し、新しい画像に合わせて更新する。VLAがモーターを直接制御する構成ではない。',9.6)

new('霧・粉じんのある画像でも確認','同じ室内・人物配置・モデル・判定基準で、視覚条件を変えて検証')
paragraph('5. 最終確認の結果',13,True)
labels={'clear':'通常の見え方','fog_light':'薄い霧','fog_dense':'濃い霧','dust':'粉じん'}
table(['視覚条件','停止時間','発見・画像通知・着陸'],[
 [labels[k],f'{v["physical"]["goal_holds"]["blue"]["physical_hold"]["duration_s"]:.2f}秒','確認済み'] for k,v in scores.items()
 ],[165,100,WIDTH-265])
paragraph('各条件1回の最終確認であり、未知の環境に対する成功率や一般的な頑健性を示す統計試験ではない。霧と粉じんは実際の入力画像に含まれる体積描画である。濃さはシミュレーション上の設定で、実際の視程や粒子の物理特性には合わせていない。通常条件にも基準となる薄い粉じんが含まれる。')
paragraph('6. 工夫と途中の問題',13,True)
paragraph('人物の立ち姿・衣服・接地・床や影を整えた室内を用い、その画像で実際に飛行を確認した。今回の工夫は、見えていない対象の捜索、複数画像による人物確認、原画像付き通知までをつなぎ、視覚条件が変わっても同じ処理で実行できるか確かめた点にある。')
paragraph('途中の評価では、旋回後に角度の厳密な判定を待ち続け、飛行時間が長引いた。捜索の目的に合わせ、画像で対象を確認でき、機体の旋回も落ち着いた時点で次へ進むよう工程管理を修正した。最終確認は全条件をやり直し、失敗した記録も保持している。接近・停止の物理的な合格基準は変更していない。')
paragraph('7. 残る課題',13,True)
paragraph('1室内の静止した人物に対象を絞っている。別の部屋への移動、未知の障害物への対応、同じ色の服を着た複数人、本人の識別、負傷の判定は扱わない。次は場所・人物・照明等を変えた検証と、実機での確認が必要である。')
paragraph('最終モデル：'+movie['checkpoint_sha256'][0][:24]+'…\n今回の記録：rescue_search/runs/'+records.name,8.4,color=muted)

new('実在する機体をもとに実機化を考える','実在部品を基にした設計案。実機での成立は未検証。')
paragraph('8. 実機に向けた構成案',13,True);loop_diagram(True)
paragraph('機体はStampFly、カメラと無線通信にはXIAO ESP32S3 Senseを候補とする。地上のGPU搭載PCでVLAを動かし、コントローラーが画像と機体情報を受信してVLAへ渡す。生成された動作を飛行指令として機体へ返し、機体側で姿勢を安定させる。位置推定用センサーも構成案に含める。')
paragraph('シミュレーションは追加部品を含む50gの設計想定。実機を計測して校正した再現モデルではない。搭載重量と推力の余裕、消費電力、無線通信の同時動作と遅延、固定方法、実機での飛行は未検証である。5万円以内を目標とする構成検討であり、購入済み一式の価格や実機成立を保証するものではない。')
paragraph('9. コード・記録と再現',13,True)
paragraph('コード、固定設定、モデル識別子、入力画像、飛行ログ、採点処理、動画編集コードを提出用アーカイブに含める。保存済み記録の再採点は可能。新たな飛行にはGPU、モデル重み、Blender、WSL上のArduPilotとStampFly物理モデルが必要である。外部モデルの重みやフォントは同梱しない。')
paragraph('10. 使用技術・素材',13,True)
for line in [
 'SmolVLA / LeRobot：https://huggingface.co/lerobot/smolvla_base',
 'ArduPilot：https://github.com/ArduPilot/ardupilot （GPL-3.0-or-later）',
 'StampFly：https://github.com/M5Fly-kanazawa/stampfly_ecosystem （MIT）',
 'MuJoCo：https://mujoco.org/　Blender：https://www.blender.org/',
 '人物検出：torchvision SSDlite320 MobileNet V3 Large（学習済み重みを使用）',
 'MakeHuman / Poly Haven：使用した人物・背景素材はCC0。詳細は添付のライセンス一覧。',
 ]:paragraph(line,8.4,gap=5,color=muted)
footer();c.save();assert page==4
(OUT.with_suffix('.json')).write_text(json.dumps(dict(pages=page,sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(),records=str(records),visually_reviewed=False),indent=2))
print('SEARCH_REPORT_CREATED',OUT)
