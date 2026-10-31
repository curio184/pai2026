"""Write a dated Japanese status report from current completed records."""
import datetime,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
verification=read(W/'reports/train12_en_all_records_verified.json');assert verification['evidence_consistent']
progress=read(W/'models/train13_en/progress.json');state=read(W/'pipeline_train13_resume01_status.json')
assert state['stage']=='training_resume01' and 3000<=progress['step']<6000
assert not (W/'models/train13_en/result.json').exists()
suites=[]
for path in sorted((W/'runs').glob('*/summary.json')):
    d=read(path)
    if all(k in d for k in ['completed','planned','successes']):
        suites.append(f"  {path.parent.name}: {d['successes']}/{d['completed']} 成功、予定 {d['planned']} 件")
text=f'''災害救助ドローン v1.1 中間報告
記録時刻：{now:%Y-%m-%d %H:%M:%S} JST

結論
採用する v1.1 はまだ確定していません。未知配置での最終比較、動画の全場面の再確認、説明PDFとREADMEの完成は未完了です。

直近の結果と対応
・train12 の基本試験は 8 件を完走し、7 件成功・1 件失敗でした。
・失敗した dev01_blue は、発見時に画面右端にいた青い服の人を接近中に見失いました。停止条件は達成していません。
・既存の学習画像には画面端の人物も含まれる一方、接近の教師では旋回をゼロとしていました。train13 では、指定した人物へ向きを合わせながら接近する教師を追加しました。
・画像・指示・機体状態は既存データのままです。離着陸・静止・見回しの教師、実行時の制御器、検出器、任務管理、採点基準は変更していません。
・train13 は事前に定めた 6,000 ステップ中 {progress['step']:,} ステップまで進んでいます。現在の処理：{state['stage']}。
・2,000 ステップの保存時に Windows のファイル置換エラーで停止しました。保存内容を検査し、重み・AdamW・NumPy/CPU/GPU の乱数状態を復元して再開しました。学習のやり直しや、中間重みの成績による選別はしていません。
・3,000 ステップの別名保存は正常に完了し、内容も検査済みです。

記録の保全と確認
・完了済みの開発・比較記録 {verification['records']} 件は、成功・失敗を含めて独立に再採点し、保存結果と一致しました。異なる候補・条件をまとめた成功率は報告しません。
・今回の追加学習用 8,408 画像は、描画結果や既存画像と照合済みです。描画濃度 0.004 に対し、霧・粉じんの評価値は 0.06/0.12 です。これは描画パラメーターの比であり、現実の視程の比ではありません。
・動画、YouTube、v1.0 の最終重みと既存の飛行記録は変更していません。GitHub への push、タグ付け、再提出もしていません。
・WSL の飛行試験は 4 CPU / 8 GiB 以下で 1 件ずつ実行します。学習は Windows 側の GPU です。
・E: の空きは記録時点で {shutil.disk_usage(W).free/1024**3:.2f} GiB です。

試験群の一覧（条件とモデルが異なるため合算しない）
{chr(10).join(suites)}

v1.1開発・比較の全実行の個別一覧と保存先
{W/'ALL_TRIALS_ROUND02_ENGLISH.md'}
{W/'runs'}

直近の失敗分析
{W/'reports/train12_failure_analysis.json'}

現在の学習条件と保存エラーからの再開記録
{W/'protocol/train13_english.json'}
{W/'protocol/train13_resume01.json'}
{W/'reports/train13_interrupted_save_integrity.json'}
{W/'reports/train13_resume01_save_verified.json'}

未完了
1. train13 の 6,000 ステップ完了と最終重みの照合。
2. 基本試験、既知配置での厳しい試験、動画の全場面、元の配置交換失敗の再確認。
3. 上記を通過した場合に、未使用の 4 配置で v1.0/v1.1 を各 16 回比較し、固定画像での色・指示交換も検査。
4. 結果と限界を反映した約 4 ページの説明PDF、README、公開用記録の作成・確認。
5. 公開・タグ付け・再提出は、完成物の確認後に利用者の承認を得て実施。

停止基準は「目標点から25cm以内、水平速度0.08m/s以下を3秒以上」のままです。
最終評価の新しい配置・開始条件・シードは未使用のまま維持しています。
'''
out=W/'reports'/f'中間報告_{now:%Y%m%d_%H%M%S}.txt';assert not out.exists();out.write_text(text,encoding='utf8')
print(json.dumps(dict(report=str(out),training_step=progress['step'],completed_records=verification['records'],final_goal_achieved=False),ensure_ascii=False))
