"""Run required flight checks once with the final checkpoint, without training.

Run on Windows in the SmolVLA environment after finetune_smolvla.py succeeds.
The GPU model is loaded before starting physics, so model construction cannot
consume a flight deadline. Failures are kept and never trigger automatic reruns.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4*1024*1024), b""):
            value.update(block)
    return value.hexdigest()


def linux_path(path):
    path = path.resolve()
    if not path.drive or path.drive.startswith("\\"):
        raise ValueError("Expected a local Windows drive path")
    return "/mnt/"+path.drive[0].lower()+path.as_posix()[2:]


def wsl(*args, **kwargs):
    return subprocess.run(["wsl", "-d", "Ubuntu-22.04", "--exec", *map(str, args)], **kwargs)


def run(args):
    if sys.platform != "win32":
        raise RuntimeError("This orchestrator starts the Windows GPU and WSL physics")
    root = Path(__file__).resolve().parent
    training = (getattr(args,"training_run",None) or root/"outputs/smolvla_training").resolve()
    plan_file = (getattr(args,"plan",None) or root/"finetune_plan.json").resolve()
    trained = json.loads((training/"result.json").read_text(encoding="utf-8"))
    started = json.loads((training/"started.json").read_text(encoding="utf-8"))
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    if trained["optimizer_steps_completed"] != plan["steps"] or trained["selection"] != "Final step only":
        raise ValueError("Training has not completed the fixed final-step plan")
    if trained["plan_sha256"] != digest(plan_file) or trained["plan_sha256"] != started["plan_sha256"]:
        raise ValueError("Training plan provenance mismatch")
    if trained["dataset_sha256"] != started["dataset_sha256"]:
        raise ValueError("Training data provenance mismatch")
    checkpoint = training/"final"
    checkpoint_hash = digest(checkpoint/"model.safetensors")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    home = wsl("python3", "-c", "from pathlib import Path; print(Path.home())", capture_output=True, text=True, check=True).stdout.strip()
    linux_root = PurePosixPath(linux_path(root))
    linux_python = PurePosixPath(home)/"physical_ai_drone_sitl/venv/bin/python"
    selection_file=root/"review_selection.json"
    selection=json.loads(selection_file.read_text(encoding="utf-8")) if selection_file.exists() else {}
    selected_training=training.relative_to(root).as_posix()==selection.get("training_run")
    chunk_origin=getattr(args,"chunk_origin",None) or (selection.get("flight_chunk_origin","capture") if selected_training else "capture")
    selected_build=selection.get("flight_build_name","final_bridge") if training.relative_to(root).as_posix()==selection.get("training_run") else "final_bridge"
    build = PurePosixPath(getattr(args,"build",None) or PurePosixPath(home)/"physical_ai_ardupilot"/selected_build)
    linux_out = PurePosixPath(home)/"physical_ai_ardupilot"/out.name
    wsl("python3", "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).mkdir(exist_ok=False)", linux_out, check=True)
    profiles = getattr(args,"profiles",None) or ["blue", "red", "turns"]
    recovery=getattr(args,"recovery_from",None)
    if recovery:
        previous=json.loads((recovery/"verification_manifest.json").read_text(encoding="utf-8"))
        if previous["checkpoint_sha256"]!=checkpoint_hash:
            raise ValueError("Integration recovery must use exactly the same final checkpoint")
        for profile in profiles:
            previous_score=json.loads((recovery/profile/"physical_score.json").read_text(encoding="utf-8"))
            previous_link=json.loads((recovery/profile/"vla_link_events.json").read_text(encoding="utf-8"))
            if previous_score["learned_policy_provenance"] or any(e.get("event")=="inference" for e in previous_link):
                raise ValueError("Do not rerun a case that already received learned model actions")
    source_files = ["smolvla_policy.py", "vla_worker.py", "vla_link.py", "rescue_scene.py", "flight_progress.py", "revision_authorization.json", "review_selection.json", "payload_revision_50g.json", "chunk_timing_revision.json", "ardupilot_bridge/setup_bridge.py",
                    "score_mission.py", "ardupilot_bridge/rescue_mission.py", "ardupilot_bridge/plant_c.cpp"]
    source_files += ["civic_camera.py","civic_render_client.py"]
    snapshot=out/"source_snapshot"
    for name in source_files:
        destination=snapshot/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(root/name,destination)
    linux_share=Path("\\\\wsl.localhost\\Ubuntu-22.04")
    build_share=linux_share/str(build).lstrip("/").replace("/", "\\")
    for name in ["rescue_scene.xml","stampfly_payload.xml","build_result.json"]:
        shutil.copy2(build_share/name,out/name)
    optical_config=build_share/"rescue_scene.render.json"
    if optical_config.exists():shutil.copy2(optical_config,out/optical_config.name)
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                    training_run=training.relative_to(root).as_posix(),training_plan_file=plan_file.relative_to(root).as_posix(),
                    checkpoint_sha256=checkpoint_hash, profiles=profiles,
                    source_sha256={name: digest(root/name) for name in source_files},
                    training_plan_sha256=trained["plan_sha256"], dataset_sha256=trained["dataset_sha256"],
                    scene_sha256=digest(out/"rescue_scene.xml"),plant_library_sha256=digest(build_share/"libstampfly_plant.so"),
                    model_selection="final step only", automatic_retries=0,chunk_execution_origin=chunk_origin,
                    integration_recovery_from=recovery.name if recovery else None,
                    integration_recovery_scope="Only cases with zero previous policy responses" if recovery else None,
                    hyperparameter_or_gain_search=False,
                    revision_authorization_sha256=digest(root/"revision_authorization.json"),
                    note="Required functional checks of one model. Revised inference/progression explicitly authorized by the user; original failures remain preserved.")
    (out/"verification_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    shutil.copy2(plan_file,snapshot/"training_plan.json")
    ready = out/"worker_ready.json"
    records = []
    worker_log = (out/"worker.log").open("w", encoding="utf-8")
    worker = subprocess.Popen([sys.executable, str(root/"vla_worker.py"), "--checkpoint", str(checkpoint),
                               "--sessions", str(len(profiles)), "--ready-file", str(ready),
                               "--connect-timeout", "120"], stdout=worker_log, stderr=subprocess.STDOUT)
    renderer=None;renderer_log=None
    try:
        loading_started = time.monotonic()
        while not ready.exists():
            if worker.poll() is not None:
                raise RuntimeError(f"Policy worker exited during loading: {worker.returncode}")
            if time.monotonic()-loading_started > 900:
                raise TimeoutError("Policy loading exceeded 900 seconds; no automatic restart")
            time.sleep(.5)
        loaded = json.loads(ready.read_text(encoding="utf-8"))
        if loaded["checkpoint_sha256"] != checkpoint_hash:
            raise ValueError("Loaded policy checkpoint mismatch")
        if optical_config.exists():
            optical_ready=out/"optical_ready.json"
            renderer_log=(out/"optical_renderer.log").open("w",encoding="utf8")
            optical_settings=json.loads(optical_config.read_text())
            optical_blend=root/optical_settings.get('blend_relative','assets/civic_world/civic_world.blend')
            renderer=subprocess.Popen([r"C:\Program Files\Blender Foundation\Blender 3.1\blender.exe","--background","--factory-startup","--python",str(root/"civic_render_client.py"),"--",str(len(profiles)),str(optical_ready),str(optical_blend)],stdout=renderer_log,stderr=subprocess.STDOUT)
            optical_started=time.monotonic()
            while not optical_ready.exists():
                if renderer.poll() is not None:raise RuntimeError('Optical renderer failed to start')
                if time.monotonic()-optical_started>90:raise TimeoutError('Optical warmup timed out')
                time.sleep(.25)
            if json.loads(optical_ready.read_text())["blend_sha256"]!=json.loads(optical_config.read_text())["blend_sha256"]:raise ValueError('Optical scene mismatch')
        for profile in profiles:
            if worker.poll() is not None:
                raise RuntimeError(f"Worker exited before {profile}: {worker.returncode}; no automatic restart")
            print(json.dumps(dict(event="starting_flight_check", profile=profile)), flush=True)
            linux_record = linux_out/profile
            with (out/f"{profile}_runner.log").open("w", encoding="utf-8") as handle:
                completed = wsl(linux_python, linux_root/"ardupilot_bridge/rescue_mission.py",
                                "--build", build, "--scene", build/"rescue_scene.xml",
                                "--output", linux_record, "--profile", profile,"--chunk-origin",chunk_origin,
                                stdout=handle, stderr=subprocess.STDOUT, timeout=240)
                score_run = wsl(linux_python, linux_root/"score_mission.py", linux_record,
                                "--scene", build/"rescue_scene.xml", stdout=handle, stderr=subprocess.STDOUT,
                                timeout=60) if completed.returncode == 0 else None
            source = Path("\\\\wsl.localhost\\Ubuntu-22.04")/str(linux_record).lstrip("/").replace("/", "\\")
            if not source.is_dir():
                raise RuntimeError(f"WSL case {profile} exited {completed.returncode} without a record directory; inspect its runner log. No automatic retry.")
            shutil.copytree(source, out/profile)
            score_file = out/profile/"physical_score.json"
            score = json.loads(score_file.read_text(encoding="utf-8")) if score_file.exists() else None
            record = dict(profile=profile, runner_exit=completed.returncode,
                          scorer_exit=score_run.returncode if score_run else None,
                          success=bool(score and score["success"]),
                          checkpoint_matches=bool(score and score["checkpoints"] == [checkpoint_hash]))
            records.append(record)
            (out/"progress.json").write_text(json.dumps(records, indent=2)+"\n", encoding="utf-8")
            print(json.dumps(record), flush=True)
        worker.wait(timeout=30)
        summary = dict(success=all(r["success"] and r["checkpoint_matches"] for r in records),
                       checks=records, worker_exit=worker.returncode, checkpoint_sha256=checkpoint_hash,
                       real_hardware_feasibility_verified=False)
        (out/"result.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(summary, indent=2), flush=True)
    except BaseException as error:
        (out/"orchestrator_failure.json").write_text(json.dumps(dict(error=repr(error), checks=records), indent=2)+"\n", encoding="utf-8")
        raise
    finally:
        if renderer is not None and renderer.poll() is None:
            renderer.terminate();renderer.wait(timeout=15)
        if renderer_log is not None:renderer_log.close()
        if worker.poll() is None:
            worker.terminate()
            try:
                worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait()
        worker_log.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).parent/"outputs/ardupilot/final_policy_01")
    parser.add_argument("--profiles", nargs="+", choices=["blue","red","turns","left"])
    parser.add_argument("--recovery-from",type=Path)
    parser.add_argument("--training-run",type=Path)
    parser.add_argument("--plan",type=Path)
    parser.add_argument("--build",type=str,help="Absolute WSL path; defaults to the selected review build")
    parser.add_argument("--chunk-origin",choices=["capture","receipt","split"])
    run(parser.parse_args())
