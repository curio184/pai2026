"""Read existing conversation and flight evidence; no inference, flight or training.

Produces a local design-review record, not a submission or success certificate.
"""
from pathlib import Path
import datetime
import hashlib
import json

W = Path(__file__).resolve().parents[1]
SESSION = Path(r'<USER_HOME>\.codex\sessions\2026\10\22\rollout-2026-10-22T21-02-09-01a1637d-7959-7dd2-9588-5e49c61d4c55.jsonl')

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def source(path, needle):
    lines = path.read_text(encoding='utf-8').splitlines()
    found = [i + 1 for i, line in enumerate(lines) if needle in line]
    assert found, (path, needle)
    return dict(path=str(path), sha256=sha(path), lines=found, excerpt=needle)

def classification(index):
    if index < 65:
        return '探索した代替案。最終テーマの必須機能ではない。完成可能性・面白さ・実機との接点という価値は継続。'
    if index < 105:
        return '機体・入力・物理・予算・実機可能性の要件。学習回数制限は後続発話で変更。'
    if index < 264:
        return '作品と映像の制作・承認。後の動画固定指示に従い保全。多室探索は延期。'
    if index < 281:
        return '提出と公開・技術的説明。初回公開承認は更新版の公開承認には流用しない。'
    if index == 281:
        return 'v1.0追加検証。後続v1.1の別学習許可で学習禁止は更新。採点・証拠保全・公開承認は継続。'
    if index == 283:
        return 'v1.1の目的・完了条件・証拠の要件を定義する中心発話。'
    if index == 300:
        return 'VLA指示を英語だけにする変更。日本語理解の達成を主張しない。'
    if index in (282, 296, 315, 316, 318, 328):
        return '保存先・移動・容量。最新のE集約と不要物整理許可を適用。唯一の重み・試験記録は保全。'
    if index in (322, 323, 324, 325, 326, 327):
        return 'WSLは後続許可により利用可。ただし4CPU・8GB以内、過負荷を避ける。'
    if index >= 379:
        return '直近の実行制約と目的の再確認。1時間・追加の試行錯誤禁止・条件緩和禁止・手段を再考。'
    return '進捗確認・継続指示・環境情報。達成条件を緩める指示ではない。'

def main():
    human = []
    excluded = dict(goal=0, environment=0, page=0)
    index = 0
    with SESSION.open(encoding='utf-8') as stream:
        for line in stream:
            obj = json.loads(line)
            p = obj.get('payload', {})
            if obj.get('type') != 'response_item' or p.get('type') != 'message' or p.get('role') != 'user':
                continue
            index += 1
            text = '\n'.join(c.get('text', '') for c in p.get('content', []) if c.get('type') in ('input_text', 'text')).strip()
            if text.startswith('<codex_internal_context'):
                excluded['goal'] += 1
                continue
            if text.startswith('<environment_context>'):
                excluded['environment'] += 1
                continue
            if text.startswith('<external_codex_apps_open_page>'):
                excluded['page'] += 1
                continue
            if index > 392:
                continue  # Fixed historical scope through the explicit review request.
            human.append(dict(index=index, message_id=p.get('id'), timestamp=obj.get('timestamp'),
                              text=text, text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                              context=classification(index)))
    assert len(human) == 278 and len({h['message_id'] for h in human}) == 278

    summary = read(W/'runs/stress_train15_en/summary.json')
    failure = read(W/'reports/train15_failure_analysis.json')
    cases = []
    for entry in summary['cases']:
        record = Path(entry['record'])
        physical = read(record/'physical_score.json')
        result = read(record/'result.json')
        stages = read(record/'stages.json')
        color = entry['case']['color']
        hold = physical['goal_holds'][color]['physical_hold']
        target_stages = [s for s in stages if s['phase'] == color]
        row = dict(id=entry['id'], record=str(record), original_success=entry['success'],
                   requested_color=color, requested_goal_hold_s=hold['duration_s'],
                   minimum_requested_goal_distance_m=physical['goal_holds'][color]['minimum_goal_distance_m'],
                   initial_hover_hold_s=physical['explicit_hover_instruction_hold']['duration_s'],
                   minimum_person_clearance_m=physical['minimum_person_clearance_m'],
                   notification_saved=result.get('notification') is not None,
                   rotation=physical['rotations']['right'], observation_age_s=physical['observation_age_s'],
                   re_acquire_stages=sum(s['phase']=='reacquire' for s in stages),
                   score_sha256=sha(record/'physical_score.json'), stage_sha256=sha(record/'stages.json'))
        if hold['duration_s'] >= 3 and target_stages:
            first_three_seconds_in_longest_hold = hold['end_s'] - hold['duration_s'] + 3
            row['longest_valid_hold_reached_3s_at'] = first_three_seconds_in_longest_hold
            row['last_target_stage_end_s'] = target_stages[-1]['end']
            row['delay_after_this_already_valid_hold_s'] = target_stages[-1]['end'] - first_three_seconds_in_longest_hold
            row['delay_scope'] = 'Postflight diagnosis only. This is not a runtime trigger and is not necessarily the first valid interval.'
        cases.append(row)
    assert len(cases) == 16 and sum(c['original_success'] for c in cases) == 9
    runtime = W/'runtime_english'
    contracts = dict(
        velocity_to_attitude=source(runtime/'search_mission.py', 'accel = np.clip(desired-velocity,-.8,.8)'),
        loop_period=source(runtime/'search_mission.py', 'if t-last_control >= .05'),
        stop_command_window=source(runtime/'flight_progress.py', 'def __init__(self, hold_s=4.0, command_limit_m_s=.065)'),
        stop_progress=source(runtime/'search_mission.py', 'navigation_complete=stop_window.update(t,model_action[:2],valid) and confirmed'),
        visual_confirmation=source(runtime/'confirmation.py', "return len(self.hits)>=3 and self.hits[-1]['t']-self.hits[-3]['t']>=.4"),
        offline_goal_criterion=source(runtime/'score_mission.py', 'mask=(phases==color)&(distance<=.25)&(speed<=.08)&(height>=.8)&(height<=1.25)'),
        aggregate_search_rotation=source(runtime/'score_search.py', 'search_rotation_completed=bool'),
    )
    document = dict(
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        kind='local_goal_and_design_review_not_submission_not_new_experiment',
        goal='言葉で指定した色の相手にVLAが画像から動作を生成し、未学習配置で接近・停止できる救助ドローンを完成させる。既存動画の場面を維持し、公平な比較・反復・全記録で裏付け、約4ページのPDFとREADMEを仕上げる。',
        human_turns_reviewed=len(human), historical_scope_last_user_index=392,
        excluded_automatic_context=excluded, private_conversation_ledger=human,
        constraints=dict(deadline_utc='2026-10-30T10:56:36+00:00', no_further_trial_and_error=True,
                         no_video_changes=True, no_truth_to_runtime=True, original_scores_unchanged=True,
                         preserve_all_trials_and_final_weights=True, no_publication_without_approval=True,
                         storage='E:', wsl_cpu_limit=4, wsl_memory_gib_limit=8),
        method_goal_separation=[
            'VLAが画像と言葉から相手に向かう動作を出すことは目的。すべての低レベル補正をニューラルネットに学ばせることは目的ではない。',
            '62本の開発段階一式はエージェントの手順。ユーザー指定の独立した完成条件ではない。ただし既存登録・失敗を消したり、結果から都合よく試験を削ったりしない。',
            '既存の制御器固定指示と最新の手段再考指示の関係を明示し、変更する場合はv1.0を保存して別構成にする。現時点で実行系は変更していない。',
            '未達を説明する資料を完成品に置き換える方針はユーザーが拒否した。これを今後の自動処理の到達点にしない。',
        ],
        source_contracts=contracts, all_latest_completed_cases=cases,
        findings=[
            dict(claim='色選択だけでは全失敗を説明できない。指定目標で3秒停止12/16、任務全体9/16。', evidence=str(W/'reports/train15_failure_analysis.json'), certainty='observed'),
            dict(claim='低速のVLAに画像に基づく移動と自己状態による補正を同時に学ばせている。速度変換は20Hzの比例制御で、定常外乱を積分補償する項がない。', evidence='source_contracts.velocity_to_attitude and loop_period', certainty='source fact; contribution to each failure is not isolated'),
            dict(claim='停止指令の平均が小さいことと、正しい目標位置に止まっていることは同値ではない。H08は通知を保存したが目標まで最小0.3527m。', evidence='H08', certainty='observed counterexample'),
            dict(claim='H09は目標で22.11秒停止したが、初期静止と着陸中の距離条件に失敗した。色選択の追加学習だけで解決すると判断できない。', evidence='H09', certainty='observed'),
            dict(claim='再旋回を許す実行系に対し、採点はright工程を合算して35〜145度を要求する。H16は約173度でこの条件に不合格。目標停止にも失敗しており、採点を変えれば成功するとは言わない。', evidence='H16 and source_contracts.aggregate_search_rotation', certainty='observed; original failure retained'),
        ],
        rebuilding_decision=dict(
            preferred_boundary='VLAは指示色に基づく接近・停止の意図と動作を担い、速い機体安定化は推定自己状態だけを使う制御部で担う。色判定器に目標動作の生成を肩代わりさせない。',
            original_freeze_conflict='速度→姿勢の変換または工程完了判定を変更する案は、先の固定指示に関わる。提案を固定構成から区別し、無断で旧記録・採点・比較条件を書き換えない。',
            comparison='変更する構成ではv1.0/v1.1双方に同じ制御部と同じ試験を適用する。旧構成との改善をモデル単体の効果と呼ばない。',
            no_guarantee='単純化した数式や保存済みログは新構成の飛行成功の証明にならない。全体成功は最後の固定した実行で確認が必要。',
            next='単一の修正仕様を具体化する。新しい教師の当て直し、候補追加、条件探索を再開しない。'),
        current_computation='既開始のtrain16最終6000ステップのみ進行。自動評価の親プロセスは停止中。中間重みは評価しない。',
        supersedes_next_actions_in=['reports/user_one_hour_20261030.json', 'reports/current_work_checkpoint.json'],
        prohibited_inference='本資料は成功報告でも提出PDFの代替でもない。既存16件の結果・採点を一切変更しない。',
    )
    output = W/'reports/goal_reconstruction_20261030.json'
    with output.open('x', encoding='utf-8') as f:
        json.dump(document, f, ensure_ascii=False, indent=2)
        f.write('\n')
    checkpoint = W/'reports/current_work_checkpoint.json'
    old = read(checkpoint)
    old.update(updated_utc=document['created_utc'], user_reconstruction_review=str(output),
               user_reconstruction_review_sha256=sha(output), automatic_pipeline_suspended=True,
               next='Respect one-hour cap and no new trials. Concrete architecture review is authoritative in reports/goal_reconstruction_20261030.json. Preserve existing train16 to fixed final step. No incomplete substitute PDF, automatic trial pipeline, or publication.',
               last_goal_turn_classification='progress: reviewed278humanturns; tied failure decomposition to all16unalteredrecords and7sourcecontracts; recorded goal/method separation and unresolved controller-freeze scope')
    checkpoint.write_text(json.dumps(old, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(output=str(output), sha256=sha(output), human_turns=len(human),
                          cases=len(cases), successes=sum(c['original_success'] for c in cases),
                          source_contracts=len(contracts), no_new_trial=True), ensure_ascii=False))

if __name__ == '__main__':
    main()
