"""Prepare offline aggregation with unchanged acceptance and retained history."""
import ast
from pathlib import Path
W=Path(__file__).resolve().parents[1]
text=(W/'scripts/summarize_navfocus.py').read_text(encoding='utf-8')
for before,after in [
    ('protocol/navfocus_final.json','protocol/navfocus_receipt.json'),
    ('runs/navfocus_final','runs/navfocus_receipt'),
    ("suite='navfocus_final'","suite='navfocus_receipt'"),
    ('reports/navfocus_records_verified.json','reports/receipt_records_verified.json'),
    ('reports/navfocus_execution_audit.json','reports/receipt_execution_audit.json'),
    ("configuration='navfocus'","configuration='navfocus_receipt'"),
    ("dest=W/'results/all_trials_navfocus.json'","dest=W/'results/all_trials_receipt.json'"),
    ("original=read(W/'results/all_trials_control_v11.json')","original=read(W/'results/all_trials_navfocus.json')"),
    ("if r['suite']!='navfocus_final'","if r['suite']!='navfocus_receipt'")]:text=text.replace(before,after)
text=text.replace("comparison='Both models use the same new navfocus controller and English prompts.",
                  "comparison='Both models use receipt-origin chunks, the same navfocus controller and English prompts.")
text=text.replace("limitations=['Same room", "limitations=['Layouts were absent from training but prior evaluation informed the execution-origin revision; not an independent fresh holdout.', 'Same room")
ast.parse(text)
with (W/'scripts/summarize_receipt.py').open('x',encoding='utf-8') as f:f.write(text)
text=(W/'scripts/describe_navfocus_failures.py').read_text(encoding='utf-8')
text=text.replace('protocol/navfocus_final.json','protocol/navfocus_receipt.json').replace('runs/navfocus_final','runs/navfocus_receipt')
text=text.replace('results/all_trials_navfocus.json','results/all_trials_receipt.json').replace('reports/navfocus_failure_details.json','reports/receipt_failure_details.json')
ast.parse(text)
with (W/'scripts/describe_receipt_failures.py').open('x',encoding='utf-8') as f:f.write(text)
