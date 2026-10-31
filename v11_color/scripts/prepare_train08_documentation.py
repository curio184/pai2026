"""Prepare gated publication templates for train08; do not generate final artifacts."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
p=W/'scripts/prepare_readme_round02_english.py';s=p.read_text(encoding='utf8')
s=s.replace("assert candidate=='train07_en'","assert candidate=='train08_en'")
s=s.replace("data_manifest=read(W/'data/dataset07_en/manifest.json')","data_manifest=read(W/'data/dataset08_en/manifest.json')")
s=s.replace('[学習条件](v11_color/protocol/train07_english.json) / [データの照合記録](v11_color/data/dataset07_en/audit.json)', '[学習条件](v11_color/protocol/train08_english.json) / [データの照合記録](v11_color/data/dataset08_en/audit.json)')
marker='### 学習データとモデル'
paragraph='''この候補 `train07_en` は基本試験7/8でした。8件とも離陸後の静止と各動作の停止条件を満たしましたが、1件で接近・停止後の着陸中に前へ流れ、人物との距離が0.447mとなりました。0.45mの基準を緩めず不合格とし、厳しい開発試験や最終評価には進めませんでした。次の候補では、それ以外の教師則を維持し、教師の停止位置だけを10cm手前に戻しました。これは学習上の安全余裕であり、採点の目標点は人物の前0.9mのままです。[8件の全結果](v11_color/runs/dev_train07_en/summary.json) / [距離不足の工程と時系列](v11_color/results/train07_dev02_clearance_development_diagnostic.json)

'''
assert s.count(marker)==1;s=s.replace(marker,paragraph+marker)
s=s.replace('接近では人物の前0.9mを目標点とし、位置誤差に係数1.4を掛け','接近の教師は人物の前1.0mを目標点とし、位置誤差に係数1.4を掛け')
ast.parse(s);p.write_text(s,encoding='utf8')
p=W/'scripts/build_report_round02_english.py';s=p.read_text(encoding='utf8')
s=s.replace("assert selected['candidate']=='train07_en'","assert selected['candidate']=='train08_en'")
s=s.replace("{step_text}ステップ、各段階の最終重みを使用", "計{sum(h['steps'] for h in history):,}ステップ（{len(history)}段階）。各段階の最終重みを使用")
s=s.replace('視点を増やし、遅れて実行される動作列と停止教師の関係を見直した。最終段階では教師の停止位置を採点点と揃えた。採点基準・制御器は変えていない。','視点と停止教師を見直した次の候補は基本試験7/8で、着陸中の距離不足が残った。最終段階では教師の停止位置を10cm手前に戻した。採点点・基準・制御器は変えていない。')
ast.parse(s);p.write_text(s,encoding='utf8')
print('Publication templates now describe train08; output remains gated on full evidence.')
