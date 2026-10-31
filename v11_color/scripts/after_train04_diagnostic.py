"""Wait for the actual flight pipeline to exit before using the GPU for diagnosis."""
import argparse
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path
import psutil

W = Path(__file__).resolve().parents[1]


def status(stage, **values):
    row = dict(stage=stage, updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), **values)
    (W / 'diagnostic_train04_status.json').write_text(json.dumps(row, indent=2), encoding='utf-8')
    print(json.dumps(row), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pipeline-pid', type=int, required=True)
    args = parser.parse_args()
    process = psutil.Process(args.pipeline_pid)
    assert any(x.replace('\\', '/').endswith('v11_color/scripts/pipeline_train04_en.py') for x in process.cmdline())
    status('waiting_for_live_flight_pipeline', pid=process.pid, created=process.create_time())
    while process.is_running():
        time.sleep(5)
    terminal = json.loads((W / 'pipeline_train04_en_status.json').read_text())
    assert terminal['stage'] == 'development_review' and terminal['failed_suite'] == 'stress', terminal
    status('diagnostic_inference', scope='Exposed round-1 images only')
    with (W / 'logs/train04_diagnostic_probe.log').open('x', encoding='utf-8') as log:
        result = subprocess.run([sys.executable, str(W / 'scripts/run_train04_diagnostic_probe.py')], stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Diagnostic failed; preserve outputs and inspect the log')
    status('diagnostic_ready', final_round02_not_used=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        status('diagnostic_error', error=repr(exc))
        raise
