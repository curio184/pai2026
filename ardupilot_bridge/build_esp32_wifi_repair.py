"""Build a locally reviewed ESP32 communication repair in an isolated worktree.

Never flashes hardware, changes the original checkout, commits, or publishes.
The firmware still needs human and hardware validation before actual use.
"""
import hashlib
import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess

PIN="38687117133582049734ebd39f8a7af6f487716a"
IDF_PIN="cc3203dc4f087ab41b434afff1ed7520c6d90993"


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def build(resume=False):
    root=Path(__file__).resolve().parents[1]
    home=Path.home();base=home/"physical_ai_ardupilot";original=base/"ardupilot";tree=base/"ardupilot_wifi_repair"
    review=root/"outputs/hardware_sources/esp32_wifi_lock_review_02"
    tested=json.loads((review/"result.json").read_text())
    patch=review/"esp32_wifi_locks.patch"
    if not tested["results"]["after"]["all_pass"] or digest(patch)!=tested["patch_sha256"]:
        raise ValueError("Repair patch has not passed the recorded host tests")
    if subprocess.check_output(["git","rev-parse","HEAD"],cwd=original,text=True).strip()!=PIN:raise ValueError("Wrong upstream pin")
    if any(digest(original/name)!=value for name,value in tested["source_sha256"].items()):raise ValueError("Original source differs from tested source")
    out=root/"outputs/esp32_wifi_repair"
    if resume:
        if not (out/"build.log").is_file() or not tree.is_dir() or (out/"result.json").exists():
            raise ValueError("No incomplete isolated build to resume")
        if subprocess.check_output(["git","rev-parse","HEAD"],cwd=tree,text=True).strip()!=PIN:
            raise ValueError("Existing repair tree has changed revision")
    else:
        out.mkdir(parents=True,exist_ok=False)
        if tree.exists():raise FileExistsError("Isolated worktree already exists; inspect its process and status")
    with (out/"build.log").open("a" if resume else "x") as log:
        def run(*args,cwd=tree):
            log.write("COMMAND "+shlex.join(map(str,args))+"\n");log.flush()
            subprocess.run(list(map(str,args)),cwd=cwd,stdout=log,stderr=subprocess.STDOUT,check=True)
        if not resume:
            run("git","worktree","add","--detach",tree,PIN,cwd=original)
            run("git","submodule","update","--init","--recursive")
            run("git","apply","--check",patch)
            run("git","apply",patch)
        for name,value in tested["patched_source_sha256"].items():
            if digest(tree/name)!=value:raise ValueError("Applied patch bytes differ from tested repair")
        changed=set(subprocess.check_output(["git","diff","--name-only"],cwd=tree,text=True).splitlines())
        if changed!=set(tested["patched_source_sha256"]):raise ValueError("Unexpected tracked source change")
        idf=tree/"modules/esp_idf"
        if not idf.exists():
            # ESP-IDF is an external SDK in this pinned AP revision, not a
            # tracked AP submodule. Reuse the already installed exact SDK;
            # its sources are not changed by this isolated board build.
            installed=original/"modules/esp_idf"
            if subprocess.check_output(["git","rev-parse","HEAD"],cwd=installed,text=True).strip()!=IDF_PIN:
                raise ValueError("Installed external ESP-IDF revision differs")
            idf.symlink_to(installed,target_is_directory=True)
        if subprocess.check_output(["git","rev-parse","HEAD"],cwd=idf,text=True).strip()!=IDF_PIN:
            raise ValueError("ESP-IDF revision differs from the previously built version")
        tools=base/"esp32_tools"
        script="\n".join(["#!/usr/bin/env bash","set -euo pipefail",
            "export PATH="+shlex.quote(str(tools/"usr/bin"))+':"$PATH"',
            "export LD_LIBRARY_PATH="+shlex.quote(str(tools/"usr/lib/x86_64-linux-gnu"))+':"${LD_LIBRARY_PATH:-}"',
            "export IDF_CCACHE_ENABLE=0","cd "+shlex.quote(str(tree)),
            "source modules/esp_idf/export.sh",
            "python waf configure --board esp32s3m5stampfly --disable-scripting --disable-dds",
            "python waf copter -j 4",""])
        script_file=out/"build.sh";script_file.write_text(script)
        run("bash",script_file)
    artifacts={}
    for name in ["ardupilot.bin","bootloader.bin","partition-table.bin"]:
        matches=list((tree/"build/esp32s3m5stampfly").rglob(name))
        if len(matches)!=1:raise ValueError(f"Expected exactly one {name}, got {len(matches)}")
        target=out/name;shutil.copy2(matches[0],target);artifacts[name]=digest(target)
    original_unchanged=all(digest(original/name)==value for name,value in tested["source_sha256"].items())
    if not original_unchanged:raise ValueError("Original checkout was changed")
    report=dict(ardupilot_commit=PIN,esp_idf_commit=IDF_PIN,board="esp32s3m5stampfly",build_exit=0,
                patch_sha256=tested["patch_sha256"],modified_sources=tested["patched_source_sha256"],
                original_checkout_changed=False,isolated_worktree=str(tree),artifact_sha256=artifacts,
                host_test_record="outputs/hardware_sources/esp32_wifi_lock_review_02/result.json",
                hardware_flashed=False,real_flight_tested=False,upstream_review_complete=False,
                AI_assisted_local_patch=True,
                scope="Compile plus deterministic host lock tests only. No radio throughput, timing, sensor/actuator or real-flight validation.")
    (out/"result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--resume",action="store_true")
    build(p.parse_args().resume)
