import time,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;deadline=time.monotonic()+1800
print('Waiting for atmospheric render',flush=True)
while not (HERE/'intro_atmosphere/scene_source.json').exists():
    if time.monotonic()>deadline:raise TimeoutError('Atmospheric render')
    time.sleep(2)
subprocess.run([sys.executable,str(HERE/'intro_atmosphere.py'),'render'],check=True)
subprocess.run([sys.executable,str(HERE/'audit_intro_atmosphere.py')],check=True)
