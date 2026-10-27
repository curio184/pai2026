import time,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;deadline=time.monotonic()+1200
while not (HERE/'intro_pan/scene_source.json').exists():
    if time.monotonic()>deadline:raise TimeoutError('Pan render')
    time.sleep(2)
subprocess.run([sys.executable,str(HERE/'intro_pan.py'),'render'],check=True)
subprocess.run([sys.executable,str(HERE/'audit_intro_pan.py')],check=True)
