"""Build the pinned upstream ArduCopter SITL without editing firmware sources.

Linux/WSL; run with Python from the environment containing the requirements.
The compiler, make and git must already be installed.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

PIN = "38687117133582049734ebd39f8a7af6f487716a"
SUBMODULES = ["modules/waf", "modules/mavlink", "modules/gtest",
              "modules/DroneCAN/DSDL", "modules/DroneCAN/libcanard",
              "modules/DroneCAN/dronecan_dsdlc", "modules/DroneCAN/pydronecan",
              "modules/littlefs", "modules/lwip"]


def setup(workdir):
    workdir.mkdir(parents=True, exist_ok=True)
    repo = workdir/"ardupilot"
    if not (repo/".git").exists():
        subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout",
                        "https://github.com/ArduPilot/ardupilot.git", str(repo)], check=True)
        subprocess.run(["git", "fetch", "--depth=1", "origin", PIN], cwd=repo, check=True)
        subprocess.run(["git", "checkout", "--detach", PIN], cwd=repo, check=True)
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    if actual != PIN:
        raise RuntimeError("Existing checkout has a different revision; no files changed")
    subprocess.run(["git", "diff", "--quiet"], cwd=repo, check=True)
    subprocess.run(["git", "submodule", "update", "--init", "--recursive", "--depth=1", *SUBMODULES], cwd=repo, check=True)
    env = dict(os.environ, PATH=str(Path(sys.executable).parent)+os.pathsep+os.environ["PATH"])
    commands = [[sys.executable, "waf", "configure", "--board", "sitl", "--disable-scripting", "--disable-dds"],
                [sys.executable, "waf", "copter", "-j", "6"]]
    for command in commands:
        subprocess.run(command, cwd=repo, env=env, check=True)
    report = {"revision": PIN, "source_modified": False,
              "binary": str(repo/"build/sitl/bin/arducopter"), "commands": commands,
              "hardware_esp32_build_verified": False}
    (workdir/"sitl_build_result.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--workdir", type=Path, default=Path.home()/"physical_ai_ardupilot")
    setup(p.parse_args().workdir)
