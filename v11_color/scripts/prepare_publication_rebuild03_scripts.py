"""Adapt distribution tooling to the final plan-tracking evidence contract."""
from pathlib import Path
W=Path(__file__).resolve().parents[1]
s=(W/'scripts/assemble_review_navfocus.py').read_text(encoding='utf-8')
for a,b in [('publication_candidate_navfocus','publication_candidate_rebuild03'),('all_trials_navfocus','all_trials_rebuild03'),('pdf_navfocus','pdf_rebuild03'),('README_navfocus','README_rebuild03'),('ALL_TRIALS_NAVFOCUS','ALL_TRIALS_REBUILD03'),('verify_navfocus.py','verify_rebuild03.py'),('verify_probe_navfocus.py','verify_probe_rebuild03.py')]:s=s.replace(a,b)
s=s.replace("assert report['preregistered_goal_met'] or a.review_incomplete", "assert report['preregistered_goal_met']")
start=s.index('    resources=');end=s.index('    pdfcheck=',start)
s=s[:start]+'''    verification=read(W/'reports/rebuild03_final_execution_verified.json')
    assert verification['all_verified'] and verification['records']==42
    assert len(report['all_executed_cases'])==454 and report['publication_evidence_complete']
    assert all(r['ws_cpu']<=4 and r['ws_memory_bytes']<=8*1024**3 for r in verification['cases'])
'''+s[end:]
s=s.replace("    'navfocus_work_checkpoint.json',", "    'navfocus_work_checkpoint.json',\n    'rebuild10h_goal.json','rebuild10h_work_checkpoint.json','rebuild10h_status.json',\n    'advance_rebuild01.py','advance_rebuild03.py','advance_v10_reference.py',")
s=s.replace("'runtime_navfocus','scenes'", "'runtime_navfocus','runtime_rebuild01','runtime_rebuild02','runtime_rebuild03','scenes'")
s=s.replace("'runtime_rebuild03','scenes'", "'runtime_rebuild03','runtime_rebuild03_v10ref','scenes'")
s=s.replace("'figures_navfocus','runs'", "'figures_navfocus','figures_rebuild03','probe_rebuild03','runs'")
s=s.replace("    (out/'VERSION').write_text", "    (out/'requirements-verify-v1.1.txt').write_text('numpy==2.2.6\\nPillow==13.0.0\\n',encoding='utf-8')\n    (out/'VERSION').write_text")
s=s.replace("copy(W/'reports/navfocus_records_verified.json','v11_color/results/REPLAY_VERIFICATION.json','independent rescoring of all42 final trials; preceding295 replays in reports')", "copy(W/'reports/rebuild03_final_execution_verified.json','v11_color/results/REPLAY_VERIFICATION.json','independent rescoring of all42 final trials; prior attempts retained')")
point=s.index("    prior=P/'validation_v1_1'")
extra='''    for pattern in ['rebuild*_verified.json','rebuild*_failure_details.json','rebuild*_layout_separation.json','rebuild03_role_source_audit.json','rebuild03_v10_decoder_preflight.json','rebuild_latency_same_case.json','flow_steps_benchmark01.json','endpoint_offline01.json','probe_rebuild03_verified.json','receipt_*.json','teacher_contract_review_*.md','teacher_contract_*.json','portable_rebuild03_verified.json']:
        for src in sorted((W/'reports').glob(pattern)):
            if src.name not in LOCAL_ONLY_NAMES:copy(src,'v11_color/reports/'+src.name,'recorded plan-tracking, timing and final verification evidence')
    copy(W/'ALL_TRIALS_RECEIPT.md','v11_color/ALL_TRIALS_RECEIPT.md','prior failed receipt-origin fixed confirmation; retained')
    copy(W/'ALL_TRIALS_NAVFOCUS.md','v11_color/ALL_TRIALS_NAVFOCUS.md','prior fixed confirmation; retained')
'''
s=s[:point]+extra+s[point:]
s=s.replace('VLAが人物の選択と接近・減速・停止を担い、離陸・定角旋回・着陸は通常の制御へ分離しました。', 'VLAが人物を選び、接近・減速・停止の動作列を生成します。実行部は動作列から復元した到達先を機体自身の推定状態で追従します。離陸・定角旋回・着陸は通常の制御へ分離しました。')
s=s.replace('離着陸要求の出所を新しい分担に合わせた採点と、旧来の要求元を必須とする採点の両方を保存しています。','離着陸要求と計画追従の出所を新しい分担に合わせて照合し、旧来の要求元を必須とする採点も保存しています。')
s=s.replace("    release=f'''", "    reference_stat=next(x for x in report['reference_statistics'] if x['group']=='all')\n    release=f'''")
s=s.replace("v1.0は{old_stat['k']}/{old_stat['n']}、v1.1は{new_stat['k']}/{new_stat['n']}件成功しました。", "共通変換でv1.0は{old_stat['k']}/{old_stat['n']}、v1.1は{new_stat['k']}/{new_stat['n']}件成功しました。旧版の教師定義に対応した変換でもv1.0を16件確認し、{reference_stat['k']}/{reference_stat['n']}件成功でした。教師の動作定義や指示言語の差を含むため、学習単独の効果とは扱いません。")
s=s.replace("'probe_rebuild03','runs'", "'probe_rebuild03','probe_v10_language','runs'")
s=s.replace("'advance_rebuild01.py','advance_rebuild03.py','advance_v10_reference.py',", "'advance_rebuild01.py','advance_rebuild03.py','advance_v10_reference.py','write_rebuild03_completion.py',")
s=s.replace("'probe_rebuild03_verified.json','receipt_*.json'", "'probe_rebuild03_verified.json','v10_language_reference_verified.json','receipt_*.json'")
(W/'scripts/assemble_review_rebuild03.py').write_text(s,encoding='utf-8')
s=(W/'scripts/check_publication_navfocus.py').read_text(encoding='utf-8')
for a,b in [('publication_candidate_navfocus','publication_candidate_rebuild03'),('all_trials_navfocus','all_trials_rebuild03'),('publication_navfocus','publication_rebuild03'),('verify_navfocus.py','verify_rebuild03.py'),('verify_probe_navfocus.py','verify_probe_rebuild03.py'),('expected==337','expected==454')]:s=s.replace(a,b)
s=s.replace("('intervention_metrics','v11_color/scripts/verify_probe_rebuild03.py')", "('intervention_metrics','v11_color/scripts/verify_probe_rebuild03.py'),('v10_teacher_reference','v11_color/scripts/verify_v10_teacher_reference.py')")
s=s.replace("assert result['preregistered_goal_met'] or a.review_incomplete", "assert result['preregistered_goal_met']")
s=s.replace("('v10_teacher_reference','v11_color/scripts/verify_v10_teacher_reference.py')", "('v10_teacher_reference','v11_color/scripts/verify_v10_teacher_reference.py'),('v10_language_reference','v11_color/scripts/verify_v10_language_reference.py')")
(W/'scripts/check_publication_rebuild03.py').write_text(s,encoding='utf-8')
s=(W/'scripts/verify_navfocus_layout_separation.py').read_text(encoding='utf-8').replace('protocol/navfocus_layouts.json','protocol/rebuild_final_layouts.json').replace('reports/navfocus_layout_separation.json','reports/rebuild03_layout_separation.json')
(W/'scripts/verify_rebuild03_layout_separation.py').write_text(s,encoding='utf-8')
