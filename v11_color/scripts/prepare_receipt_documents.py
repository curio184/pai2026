"""Prepare gated document generators; do not generate an unverified success PDF."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def create(name,text):
    ast.parse(text)
    with (W/'scripts'/name).open('x',encoding='utf-8') as f:f.write(text)
common=[('results/all_trials_navfocus.json','results/all_trials_receipt.json'),
 ('protocol/navfocus_final.json','protocol/navfocus_receipt.json'),
 ('reports/navfocus_records_verified.json','reports/receipt_records_verified.json'),
 ('reports/navfocus_execution_audit.json','reports/receipt_execution_audit.json'),
 ('reports/navfocus_failure_details.json','reports/receipt_failure_details.json'),
 ('ALL_TRIALS_NAVFOCUS.md','ALL_TRIALS_RECEIPT.md')]
for old,new in [('trial_index_navfocus.py','trial_index_receipt.py'),
                ('prepare_readme_navfocus.py','prepare_readme_receipt.py'),
                ('build_report_navfocus.py','build_report_receipt.py')]:
    t=(W/'scripts'/old).read_text(encoding='utf-8')
    for a,b in common:t=t.replace(a,b)
    t=t.replace('README_navfocus_','README_receipt_').replace('pdf_navfocus_','pdf_receipt_').replace('report_navfocus_','report_receipt_')
    if old=='trial_index_navfocus.py':t=t.replace('新構成 navfocus：','実行起点を見直した構成 navfocus_receipt：')
    if old=='prepare_readme_navfocus.py':
        t=t.replace('結果に応じた追加試行や係数変更は行っていません。','この固定確認の途中では、設定・係数を変更せず、各条件を一度ずつ実行しました。')
        t=t.replace('この診断に使った配置を最終評価から分け、新しい4配置を同じ範囲から無選別で生成して固定しました。モデルの追加学習は行っていません。',
                    'この診断の後、別の4配置を同じ範囲から無選別で生成しました。その42件の確認では新版11/16、動画回帰8/9でした。動作列の実行方法を診断し、今回の確認では同じ配置・乱数を再使用しています。モデルの追加学習は行っていません。')
        t=t.replace('今回の4配置は別途事前に固定し、教師データに入れていません。',
                    '今回の4配置は教師データに入れていませんが、前回の評価結果を実行方式の修正検討に使用しています。独立した新規評価配置ではありません。')
        marker='### v1.1で変更した制御\n'
        note='''### 動作列の実行起点の修正

前回の固定確認では新版11/16、動画回帰8/9でした。保存済みの動作列を調べると、撮影時刻からの経過時間に合わせて途中の要素を採用し、接近の先頭部分を飛ばして減速部分を使う場合がありました。今回は動作列を受信後に先頭から実行する `--chunk-origin receipt` に固定しました。旧・新モデルで同じ設定を使用し、重み・制御ゲイン・採点条件は変更していません。画像の古さに対する保護も維持しています。

配置は学習には未使用ですが、前回の評価が今回の実行方式の修正に影響しています。「修正後の固定再確認」として報告し、独立した新規配置の評価とは扱いません。前回42件も全試験一覧に残しています。[前回の全結果](v11_color/results/all_trials_navfocus.json) / [今回の事前条件](v11_color/protocol/navfocus_receipt.json) / [実行箇所](v11_color/scripts/run_suite_receipt.py)

'''
        assert marker in t;t=t.replace(marker,note+marker)
    if old=='build_report_navfocus.py':
        oldparagraph='初回の評価は旧モデル2/16、候補6/16。その後の制御見直しに使った配置も最終評価から分けた。以下は重みと構成を固定後に事前登録した新しい4配置×2色×2開始条件（位置±5cm、向き±5度）。両者に同じ新版の制御器と英語を使用。v1.0は英日併記で学習しており、言語適応の影響は分離していない。失敗も全件含む。'
        newparagraph='前回の固定確認は新版11/16、動画回帰8/9。接近指令を飛ばして減速部分を使う実行方法を見直し、動作列を受信後に先頭から実行する方式に固定した。以下は同じ4配置×2色×2開始条件の再確認（位置±5cm、向き±5度）。配置は学習には未使用だが、実行方式の検討に使っており、独立した新規評価ではない。両モデルに同じ制御器・英語を使い、重み・ゲイン・採点を変えず、失敗も全件含めた。'
        assert oldparagraph in t;t=t.replace(oldparagraph,newparagraph)
        t=t.replace('学習設計の各変更の寄与を分離した実験ではない。','学習・英語への適応・制御変更の寄与を個別に分離した実験ではない。')
        t=t.replace('失敗の分析 → 学習と制御の見直し → 未学習配置での固定試験','配置への依存を調べ、学習と実行方法を見直して固定再確認')
    create(new,t)
