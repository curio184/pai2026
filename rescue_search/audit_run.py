import argparse
import json
from pathlib import Path
from score_search import audit
HERE=Path(__file__).resolve().parent
def main(args):
    run=HERE/'runs'/args.name
    manifest=json.loads((run/'manifest.json').read_text(encoding='utf8'))
    reports=[]
    for case in manifest['cases']:
        record=run/(case['condition']+'_'+case['profile'])
        reports.append(dict(**case,**audit(record,HERE/'scenes'/case['condition']/'physics/rescue_scene.xml')))
    summary=dict(success=all(r['success'] for r in reports),cases=reports,
                 stage_completion_is_not_physical_success=True,all_attempts_retained=True)
    (run/'audit.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print(json.dumps(dict(success=summary['success'],cases=[dict(condition=r['condition'],success=r['success']) for r in reports])))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');main(p.parse_args())
