from pathlib import Path
W=Path(__file__).resolve().parents[1]
s=(W/'scripts/build_report_navfocus.py').read_text(encoding='utf-8').split("start('PHYSICAL AI'")[0]
s=s.replace("assert report['preregistered_goal_met'] or args.review_incomplete", "assert report['preregistered_goal_met']")
s=s.replace("review=not report['preregistered_goal_met']", "assert report['publication_evidence_complete']\nreview=False")
for a,b in [('all_trials_navfocus','all_trials_rebuild03'),('selected_navfocus','selected_rebuild03'),('probe_navfocus','probe_rebuild03'),('figures_navfocus','figures_rebuild03')]:s=s.replace(a,b)
s=s.replace("('飛行と物理計算',['制御器・ArduPilotで安定化','MuJoCoで物理状態を更新'])", "('計画に追従して飛行',['実行部・ArduPilotで安定化','MuJoCoで物理状態を更新'])")
s+=(W/'scripts/report_rebuild03_body.py').read_text(encoding='utf-8')
(W/'scripts/build_report_rebuild03.py').write_text(s,encoding='utf-8')
