"""List every completed attempt, including failures; no pooled reliability claim."""
import json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    r=read(W/'results/all_trials_rebuild01.json');rows=r['all_executed_cases']
    lines=['# 全試験の記録','','異なるモデル・構成・既知条件の試験を合算した成功率は示しません。以下は実行の所在を示す一覧です。失敗と中断も保存しています。',
      '',f"新構成 rebuild01：{r['completed']}/{r['planned']}件完了。全合格条件の確認：{'完了' if r['preregistered_goal_met'] else '未完了'}。",'',
      'VLAが指定人物を選び、接近・減速・停止する動作を生成します。離陸・定角旋回・着陸は通常の制御が担います。新旧モデルとも同じ新構成で比較し、動画のv1.0旧構成とは区別します。','',
      '| 試験群 | モデル | ケース | 成否 | 停止の継続秒 | 最小目標距離m | 最小人物距離m | 記録 |',
      '| --- | --- | --- | --- | --- | --- | --- | --- |']
    def num(x):return '—' if x is None else f'{x:.3f}'
    for row in rows:
        c=row['case'];name=row['record'];score=row.get('score_path');link=f'[採点]({score})' if score else f'[実行結果]({name}/outcome.json)'
        lines.append(f"| {row['suite']} | {c['model']} | {c['id']} | {'成功' if row['success'] else '失敗'} | {num(row.get('hold_s'))} | {num(row.get('min_goal_distance_m'))} | {num(row.get('min_person_clearance_m'))} | {link} / [入力・動作記録]({name}/record) |")
    lines+=['','## 実行しなかった条件','','旧構成 control_v11 はユーザーが分担変更を承認した時点でバッチを終了しました。実行済み8件は全件掲載し、残る34件は未実行です。失敗を成功に置き換えたり、分母から既実行の失敗を除外したりしていません。[終了記録](runs/control_v11_final/batch_closed.json)','',
       f"現在の新構成で未完了のケース：{len(r['pending_cases'])}件。",'']
    lines += [f"- {c['id']} / {c['model']}" for c in r['pending_cases']]
    lines+=['','以前の開発で合格条件を満たさず着手しなかった後続評価は、各計画と[当時の集計](results/all_trials_round02_english.json)に残しています。未実行の条件を実験の成功・失敗数には数えません。','',
      '## 起動エラーと途中中断','','| 種類 | 記録 |','| --- | --- |']
    for p in sorted((W/'runs').glob('*/*/startup_failure.json')):lines.append(f"| 飛行前の起動エラー | [原記録]({p.relative_to(W).as_posix()}) |")
    for p in sorted((W/'runs').glob('*/*/outcome.json')):
        o=read(p)
        if o.get('user_interrupted'):lines.append(f"| 利用者の指示による途中中断 | [原記録]({p.relative_to(W).as_posix()}) |")
    lines+=['','新構成の原記録には、従来の要求元条件による採点と、承認された役割分担に対応した採点の両方があります。物理基準は同じです。`physical_score_original_contract.json` は旧来の「VLAの離着陸要求」を必須とするため、新構成では不成功となります。新しい採点で要求元を偽装していません。','']
    (W/'ALL_TRIALS_REBUILD01.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(dict(executed=len(rows),current=r['completed'],pending=len(r['pending_cases']))))
if __name__=='__main__':main()
