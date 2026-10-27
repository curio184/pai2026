import time,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
deadline=time.monotonic()+1200
print('Waiting for recorded-scene render',flush=True)
while not (HERE/'intro_slow/establish_source.json').exists():
    if time.monotonic()>deadline:raise TimeoutError('Establishing render')
    time.sleep(2)
subprocess.run([sys.executable,str(HERE/'intro_slow.py'),'render'],check=True)
subprocess.run([sys.executable,str(HERE/'audit_intro_slow.py')],check=True)
