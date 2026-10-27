"""Verify distributed files and independently rescore the five recorded flights.

Requires only NumPy. Never writes into the original flight records.
"""
import argparse,contextlib,hashlib,io,json,os,shutil,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main(args):
 if not args.skip_manifest:
  manifest=json.loads((ROOT/'DISTRIBUTION_MANIFEST.json').read_text(encoding='utf8'))
  bad=[r['path'] for r in manifest['files'] if not (ROOT/r['path']).is_file() or sha(ROOT/r['path'])!=r['sha256']]
  if bad:raise RuntimeError('Distribution checksum mismatch: '+', '.join(bad[:8]))
 os.environ['RESCUE_PROJECT_ROOT']=str(ROOT)
 sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'rescue_search'))
 from score_search import audit
 cases=[('eval03',c+'_blue',c) for c in ['clear','fog_light','fog_dense','dust']]+[('eval_red01','clear_red','clear')]
 results=[]
 with tempfile.TemporaryDirectory(prefix='pai2026_verify_') as temp:
  for run,case,condition in cases:
   source=ROOT/'rescue_search/runs'/run/case;dest=Path(temp)/run/case
   shutil.copytree(source,dest,ignore=shutil.ignore_patterns('physical_score.json','search_score.json','*.BIN','*.bin','logs'))
   with contextlib.redirect_stdout(io.StringIO()):actual=audit(dest,ROOT/'rescue_search/scenes'/condition/'physics/rescue_scene.xml')
   expected=json.loads((source/'search_score.json').read_text(encoding='utf8'))
   result=dict(case=run+'/'+case,success=actual['success'],score_matches=actual==expected,physical_score_recomputed=True,input_images=actual['camera_frame_count'])
   results.append(result)
   if not result['success'] or not result['score_matches']:raise RuntimeError('Replay mismatch: '+result['case'])
 report=dict(success=True,cases=results,total_input_images=sum(r['input_images'] for r in results),scope='Offline scoring and image hash validation; not a new flight or model inference',original_records_modified=False)
 print(json.dumps(report,ensure_ascii=False,indent=2))
 if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--skip-manifest',action='store_true',help='For packaging before the final manifest exists')
 main(p.parse_args())
