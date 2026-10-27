"""Reproduce the unmodified StampFly firmware/SILS build in Linux or WSL.

Uses MuJoCo 3.9.0 from its official Python wheel as a C++ dependency, avoiding
an unnecessary source build. No embedded toolchain, flashing or radio needed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SPEC = json.loads((ROOT / "task_spec.json").read_text())


def execute(command, cwd=None):
    print("+", " ".join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=Path.home() / "physical_ai_stampfly")
    args = parser.parse_args()
    if sys.platform != "linux":
        raise SystemExit("Use Linux/WSL for this build script")
    import mujoco
    if mujoco.__version__ != "3.9.0":
        raise SystemExit("Install mujoco==3.9.0 into an isolated Python environment first")
    base = args.cache.resolve()
    base.mkdir(parents=True, exist_ok=True)
    repo = base / "stampfly_ecosystem"
    pin = SPEC["simulation"]["commit"]
    if not repo.exists():
        execute(["git", "clone", "--depth", "1", SPEC["simulation"]["repository"], repo])
    execute(["git", "fetch", "--depth", "1", "origin", pin], repo)
    execute(["git", "checkout", "--detach", pin], repo)
    if subprocess.check_output(["git", "diff", "--name-only"], cwd=repo, text=True).strip():
        raise SystemExit("Upstream tracked sources have local edits; use a separate cache")
    wheel = Path(mujoco.__file__).parent
    library = next(wheel.glob("libmujoco.so.*"))
    shim = base / "mujoco-wheel"
    shim.mkdir(exist_ok=True)
    (shim / "CMakeLists.txt").write_text(
        'cmake_minimum_required(VERSION 3.16)\n'
        'project(mujoco_wheel LANGUAGES C CXX)\n'
        'add_library(mujoco SHARED IMPORTED GLOBAL)\n'
        f'set_target_properties(mujoco PROPERTIES IMPORTED_LOCATION "{library}" '
        f'INTERFACE_INCLUDE_DIRECTORIES "{wheel / "include"}")\n'
    )
    execute(["cmake", "-S", repo / "simulator/sils", "-B", base / "build",
             f"-DFETCHCONTENT_SOURCE_DIR_MUJOCO={shim}",
             "-DSILS_BUILD_PYBIND_CONTROL=OFF", "-DSILS_MUJOCO_VIEWER=OFF"])
    execute(["cmake", "--build", base / "build", "--target", "emu_vehicle", "-j", "6"])
    print("Built unmodified firmware:", base / "build/emu_vehicle")


if __name__ == "__main__":
    main()
