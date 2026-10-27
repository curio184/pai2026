import subprocess
import sys
from pathlib import Path
here=Path(__file__).resolve().parent
for script,args in [('edit_movie.py',['render']),('master_movie.py',[])]:
    print('STARTING',script,flush=True)
    subprocess.run([sys.executable,str(here/script),*args],check=True)
print('MOVIE_READY_FOR_FINAL_REVIEW',flush=True)
