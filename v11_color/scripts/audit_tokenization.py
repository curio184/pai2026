import os,json
from pathlib import Path
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
from transformers import AutoTokenizer
W=Path(__file__).resolve().parents[1];P=W.parent
config=json.loads((P/'outputs/smolvla_training_realism_precision_02/final/config.json').read_text())
tokenizer=AutoTokenizer.from_pretrained(config['vlm_model_name'],local_files_only=True)
prompts=json.loads((P/'outputs/vla_data_realism_precision_02/manifest.json').read_text(encoding='utf-8'))['prompts']
rows=[]
for task,text in enumerate(prompts):
    for variant,prompt in zip(['bilingual','Japanese','English'],[text,text.split('. ',1)[1],text.split('. ',1)[0]+'.']):
        full=tokenizer(prompt)['input_ids'];trunc=tokenizer(prompt,padding='max_length',max_length=48,truncation=True)
        rows.append(dict(task=task,variant=variant,prompt=prompt,untruncated_tokens=len(full),truncated=len(full)>48,used_token_ids=trunc['input_ids'],decoded_used=tokenizer.decode([x for x,m in zip(trunc['input_ids'],trunc['attention_mask']) if m])))
assert rows[0]['used_token_ids']!=rows[3]['used_token_ids']
assert rows[1]['used_token_ids']!=rows[4]['used_token_ids']
(W/'protocol/tokenization_audit.json').write_text(json.dumps(dict(tokenizer=config['vlm_model_name'],rows=rows,policy_inference_executed=False),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(prompts=len(rows),truncated=sum(r['truncated'] for r in rows),maximum_tokens=max(r['untruncated_tokens'] for r in rows))))
