import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile
ROOT=Path(os.environ['RESCUE_PROJECT_ROOT']);HERE=Path(__file__).resolve().parent;MOVIE=HERE/'movie'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((MOVIE/'plan.json').read_text(encoding='utf8'))
qa=json.loads((MOVIE/'final_qa.json').read_text(encoding='utf8'))
assert all(v['success'] for v in plan['scores'].values())
dest=ROOT/'output/video/presentation_v3';dest.mkdir(exist_ok=False)
for name in ['plan.json','final_qa.json','voice_manifest.json','audio_review.json','narration_plan.json','composite_evidence.json','render_audit.json']:
    shutil.copy2(MOVIE/name,dest/name)
reviews=dest/'reviews';reviews.mkdir()
for file in (HERE/'reviews').glob('*'):shutil.copy2(file,reviews/file.name)
for file in HERE.glob('*review.md'):shutil.copy2(file,reviews/file.name)
voices=json.loads((MOVIE/'voice_manifest.json').read_text(encoding='utf8'))
script=['災害救助ドローンの開発','― VLAを用いた飛行制御のシミュレーション ―','','00:00–00:04　タイトル：音楽のみ','']
for v in voices:
    script += [f'{int(v["start"]//60):02d}:{v["start"]%60:04.1f}',v['text'],'字幕：'+v['caption'],'']
(dest/'台本.txt').write_text('\n'.join(script),encoding='utf8')
readme=f'''災害救助ドローンの開発 - 捜索検証版

動画：../rescue_drone_presentation_v3.mp4（{plan['duration_s']}秒、1920×1080、30fps）
字幕：../rescue_drone_presentation_v3.srt
説明資料：../../pdf/説明資料_PAI最終課題_捜索検証版.pdf
コード：../../code/rescue_drone_search_source.zip

今回は1機・1室内。「青い服の人を探して」という任務で、最初は対象が画角外。
人物検出と服の色の確認、VLAによる飛行、任務の進行を管理するプログラムを組み合わせ、
捜索・発見・接近・停止・原画像付き通知・着陸を実行しました。
通常の見え方、薄い霧、濃い霧、粉じんの4条件で各1回の最終確認を実施。
途中の失敗した実験記録もコードアーカイブ内に保持しています。

VLAは画像・工程の指示・機体状態から飛行動作を生成します。
任務全体の計画や人物の発見判定をVLAだけが行う構成ではありません。
動画の外部視点は、実際の物理ログを同じ光学シーンで再描画したものです。
実入力パネルは保存した原JPEGです。通知も実際に入力した画像を使用しています。
霧・粉じんは実入力に反映されますが、実際の視程や粒子特性には合わせていません。

実機構成は実在する部品を基にした設計案です。搭載・電源・通信・実機飛行は未検証です。
購入、外部への連絡、GitHub・YouTubeへの公開、課題提出は行っていません。
タイトルの4秒は音楽のみ。音声はローカル音声合成、音楽は手続き的に作成したものです。

検証の詳細：final_qa.json、plan.json、reviews/
音声の形式・音量・切れ・字幕タイミングは検査しました。独立した実聴レビューの有無はQAに記録します。
'''
(dest/'README.txt').write_text(readme,encoding='utf8')
guide=f'''提出物の準備（捜索検証版）

1. 説明PDF
output/pdf/説明資料_PAI最終課題_捜索検証版.pdf
提出時に「説明資料_PAI最終課題_ご自身のOmniCampusアカウント名.pdf」へ変更してください。
氏名が含まれる場合は、課題資料の指定に従ってアカウントIDを使ってください。

2. 動画
output/video/rescue_drone_presentation_v3.mp4（{plan['duration_s']}秒）
YouTubeへのタイトルは「PAI最終課題_ご自身のアカウント名またはアカウントID」。
課題PDFでは最低限「限定公開」、優秀生選出の加点を目指す場合は「公開」が推奨されています。

説明欄の例：
災害救助を目指し、言語指示によるドローンの捜索をシミュレーションで検証しました。
人物検出、SmolVLA、ArduPilot、MuJoCo、Blenderを組み合わせ、対象が画角外の状態から
捜索・人物確認・接近・停止・画像の報告・着陸まで実行します。
今回は1機・1室内で、通常の見え方と霧・粉じんを含む4条件を各1回確認しました。
実機への搭載や通信、実機飛行は未検証です。
ソースコード：（ご自身で公開したGitHubリポジトリのURL）

3. コード
output/code/rescue_drone_search_source.zip を展開し、READMEとコードが読める形でGitHubへ公開します。
保存した飛行の再採点手順と、新規実行に必要な環境・別途用意するモデル重みをREADMEに記載しています。

4. 提出
説明PDF・GitHubのURL・YouTubeのURLをOmniCampusへ提出します。
最優秀・優秀生選出を希望する場合は、通常提出後に「最終課題_優秀生選出用」にも提出します。
改訂版課題PDFの締切は2026年11月2日（月）10:00です。提出先の最新表示もご自身で確認してください。

公開と提出はユーザーご自身で行います。以前の動画・PDF・コードは保存したままです。
'''
(dest/'提出手順.txt').write_text(guide,encoding='utf8')
code_readme='''# 災害救助ドローンの開発

追加学習済みSmolVLAによる飛行と画像ベースの人物確認を組み合わせた、1室内での捜索シミュレーションです。
実機構成は設計案です。購入・実機飛行・実機通信の確認はしていません。

## 今回の成果

上位指示「青い服の人を探して」から、離陸、見回し、人物確認、接近・停止、画像付きの地上通知、着陸を実行。
任務進行は状態機械、人物確認はSSDlite人物検出と服の色・3画像の一致確認、動作生成はSmolVLA、姿勢制御はArduPilotです。
VLA単体が捜索計画から報告まで生成するものではありません。

同じ最終モデルで通常・薄い霧・濃い霧・粉じんを各1回確認しました。詳細はrescue_search/runs/の最終audit.json。
旧評価の失敗も全件保持。最終確認4例は一般的な成功率の統計ではありません。
目標付近25cm以内・水平速度0.08m/s以下・3秒以上の停止を、飛行終了後の真値で採点します。
物理状態の真値はカメラ描画・センサー合成と飛行後の採点に使用します。
人物座標や目標距離は、実行中のVLA・人物判定・任務進行には渡しません。原画像のSHA256も検証します。

## 保存済み記録の再採点（Windows PowerShell）

Python、NumPyを用意し、このREADMEのあるディレクトリで実行してください。

```powershell
$env:RESCUE_PROJECT_ROOT=(Get-Location).Path
$env:PYTHONUTF8='1'
python rescue_search/audit_run.py FINAL_RUN_NAME
```

スコアJSONは再生成されます。原trace/入力JPEGは変更しません。既存physical_score.jsonを再利用する仕様です。
新規に独立採点する場合は、記録フォルダーをコピーしてコピー側のphysical_score.jsonだけを外して実行します。

## 新たな飛行

Windows GPU側：PyTorch/CUDA、LeRobot、torchvision、Pillow、OpenCV、Blender 3.1.2。
WSL Ubuntu 22.04側：MuJoCo、pymavlink、固定revisionのStampFly plantとArduPilot SITL。
モデル重み、外部リポジトリとビルドは別途必要です。元の環境手順はREADME_previous.mdを参照してください。
GPU側はsearch_worker.py、カメラはcivic_render_client.py、WSL側はsearch_mission.pyです。
ポートはlocalhost 17866/17867とSITL用9002/5760。実機を操作する接続先はありません。
run_search.pyは元のWindows/WSL配置を前提とするため、パスを環境に合わせて設定してください。

## データと権利

rescue_search/scenes/に最終の4光学シーンと物理形状、runs/に最終・途中評価の原入力とログを収録。
source_snapshot/は各試行を開始した時点のソースです。現在の実行コードと区別できます。
人物・背景素材はMakeHuman/Poly Havenの使用素材のライセンス一覧を参照してください。
SSDlite重みはtorchvision公式配布元から取得（SHA256を各推論記録に記載）。外部モデル重み・フォント・実機ファームウェアは同梱しません。
再現用ソースには元の絶対パスが監査情報として残ります。動画の再編集にはmovie/plan.jsonのパスを手元の配置に読み替えてください。
'''.replace('FINAL_RUN_NAME',Path(plan['records']).name)
archive=ROOT/'output/code/rescue_drone_search_source.zip';assert not archive.exists()
base=ROOT/'output/code/rescue_drone_submission_source.zip'
with zipfile.ZipFile(base) as z:
    roots={n.split('/')[0] for n in z.namelist() if '/' in n};prefix=next(iter(roots)) if len(roots)==1 else 'rescue-drone-vla'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        for item in z.infolist():
            name=item.filename
            if name==prefix+'/README.md':name=prefix+'/README_previous.md'
            out.writestr(name,z.read(item))
        out.writestr(prefix+'/README.md',code_readme)
        for file in HERE.glob('*.py'):
            if file.name.startswith(('prepare_','refine_')):continue
            out.write(file,prefix+'/rescue_search/'+file.name)
        for file in [HERE/'plant_search.cpp',HERE/'scene_conditions.json']:
            out.write(file,prefix+'/rescue_search/'+file.name)
        for folder in ['scenes','runs','reviews']:
            for file in (HERE/folder).rglob('*'):
                if not file.is_file() or '__pycache__' in file.parts:continue
                if file.suffix in ('.bin','.BIN') or file.name.endswith('_render.log'):continue
                out.write(file,prefix+'/rescue_search/'+file.relative_to(HERE).as_posix())
        for file in [HERE/'build/build_result.json',HERE/'build/initial_pose_check.json']:
            out.write(file,prefix+'/rescue_search/'+file.relative_to(HERE).as_posix())
        for file in MOVIE.glob('*'):
            if file.is_file() and file.suffix in ('.json','.ps1'):
                out.write(file,prefix+'/rescue_search/movie/'+file.name)
        out.writestr(prefix+'/rescue_search/README.txt',readme)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
delivery=dict(video=str(ROOT/'output/video/rescue_drone_presentation_v3.mp4'),video_sha256=qa['video_sha256'],
              pdf=str(ROOT/'output/pdf/説明資料_PAI最終課題_捜索検証版.pdf'),
              pdf_sha256=sha(ROOT/'output/pdf/説明資料_PAI最終課題_捜索検証版.pdf'),
              code=str(archive),code_sha256=sha(archive),code_bytes=archive.stat().st_size,
              duration_s=plan['duration_s'],hardware_tested=False,submitted=False,published=False,
              final_run=Path(plan['records']).name)
(dest/'delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'output/video/rescue_drone_presentation_v3.json').write_text(json.dumps(dict(**delivery,
    report_directory=str(dest),final_evidence=str(Path(plan['records'])),
    implementation_directory=str(HERE),goal_complete_pending_final_archive_replay=True),ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(delivery,ensure_ascii=False,indent=2))
