"""Build the external bridge. Run with the WSL MuJoCo environment's Python."""
import argparse
import ctypes
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

STAMP_PIN = "9467f1a156326b95a01383e11c44dd665a55b536"
AP_PIN = "38687117133582049734ebd39f8a7af6f487716a"


def build(source, ap_source, output, camera_mass_g=7., camera_size_mm=(22.,24.,20.), fresh=False):
    for repo, pin in ((source, STAMP_PIN), (ap_source, AP_PIN)):
        actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        if actual != pin:
            raise RuntimeError(f"Unexpected source revision: {actual}")
    output.mkdir(parents=True, exist_ok=not fresh)
    tree = ET.parse(source / "simulator/sils/models/stampfly.xml")
    root = tree.getroot()
    root.find("compiler").set("meshdir", str(source / "simulator/shared/assets/meshes/parts"))
    body = root.find("worldbody/body[@name='drone']")
    # Payload masses, locations and dimensions are frozen engineering assumptions.
    # All locations use the original body FLU frame, not an invented new CG frame.
    camera_mass=camera_mass_g/1000
    camera_x,camera_y,camera_z=np.asarray(camera_size_mm)/1000
    if camera_mass<=0 or min(camera_x,camera_y,camera_z)<=0:
        raise ValueError("Camera mass and dimensions must be positive")
    parts = [
        (0.037, np.zeros(3), np.diag([9.16e-6, 13.3e-6, 20.4e-6])),
        (camera_mass, np.array([0, 0, 0.022]), np.diag([camera_y**2+camera_z**2, camera_x**2+camera_z**2, camera_x**2+camera_y**2])*camera_mass/12),
        # Manufacturer MTF-02P: 1.5 g, 21.6 x 16 x 6.5 mm.
        (0.0015, np.array([0, 0, -0.020]), np.diag([0.016**2+0.0065**2, 0.0216**2+0.0065**2, 0.0216**2+0.016**2])*0.0015/12),
        (0.0035, np.array([0, 0, 0.008]), np.eye(3)*0.0035*0.020**2/6),
    ]
    mass = sum(p[0] for p in parts)
    com = sum(m*r for m, r, _ in parts)/mass
    inertia = sum(I + m*((r-com)@(r-com)*np.eye(3)-np.outer(r-com, r-com)) for m, r, I in parts)
    inertial = body.find("inertial")
    inertial.attrib.clear()
    inertial.set("mass", str(mass))
    inertial.set("pos", " ".join(map(str, com)))
    inertial.set("fullinertia", " ".join(map(str, [inertia[0,0], inertia[1,1], inertia[2,2], inertia[0,1], inertia[0,2], inertia[1,2]])))
    # Explicit collision/landing clearance for the below-frame sensor.
    for x in (-0.025, 0.025):
        for y in (-0.025, 0.025):
            ET.SubElement(body, "geom", type="capsule", **{"fromto":f"{x} {y} -0.010 {x} {y} -0.029", "size":"0.003", "mass":"0", "rgba":"0.2 0.2 0.2 1"})
    ET.SubElement(body, "geom", type="box", pos="0 0 0.022", size=" ".join(map(str,[camera_x/2,camera_y/2,camera_z/2])), mass="0", rgba="0.1 0.5 0.2 1")
    ET.SubElement(body, "geom", type="box", pos="0 0 -0.020", size="0.0108 0.008 0.00325", mass="0", rgba="0.2 0.2 0.2 1")
    tree.write(output / "stampfly_payload.xml", encoding="utf-8", xml_declaration=True)
    mj = Path(mujoco.__file__).parent
    sils = source / "simulator/sils"
    vehicle = source / "firmware/vehicle/components"
    here = Path(__file__).parent
    command = ["g++", "-shared", "-fPIC", "-O2", "-std=c++17", str(here/"plant_c.cpp"), str(sils/"plant/plant.cpp")]
    for inc in [sils/"plant", sils/"frames", vehicle/"sf_math/include", vehicle/"sf_core/include", mj/"include"]:
        command += ["-I", str(inc)]
    command += [str(next(mj.glob("libmujoco.so.*"))), "-Wl,-rpath,"+str(mj), "-o", str(output/"libstampfly_plant.so")]
    subprocess.run(command, check=True)
    lib = ctypes.CDLL(str(output/"libstampfly_plant.so"))
    lib.sf_create.argtypes = [ctypes.c_char_p, ctypes.c_float]; lib.sf_create.restype = ctypes.c_void_p
    lib.sf_hover.argtypes = [ctypes.c_void_p]; lib.sf_hover.restype = ctypes.c_float
    lib.sf_thrust.argtypes = [ctypes.c_void_p, ctypes.c_float]; lib.sf_thrust.restype = ctypes.c_float
    lib.sf_destroy.argtypes = [ctypes.c_void_p]
    ptr = lib.sf_create(str(output/"stampfly_payload.xml").encode(), mass)
    if not ptr:
        raise RuntimeError("MuJoCo plant initialization failed")
    report = dict(stampfly_commit=STAMP_PIN, ardupilot_commit=AP_PIN, mass_kg=mass,
                  camera_design_mass_g=camera_mass_g,camera_design_size_mm=list(camera_size_mm),
                  com_body_flu_m=com.tolist(), inertia_about_com_kg_m2=inertia.tolist(),
                  payload_measured=False, hover_duty_nominal=lib.sf_hover(ptr),
                  hover_duty_label_correction="Legacy field name: equilibrium at INITIAL battery voltage (4.15 V), not nominal 3.7 V; equal motor loads only, ignores offset CG",
                  max_static_thrust_per_motor_N=lib.sf_thrust(ptr, 1.0),
                  model_calibrated_for_this_assembly=False,
                  note="Motor/sensor/battery plant source unchanged; payload is a proposed assembly, not a validated digital twin.")
    lib.sf_destroy(ptr)
    (output/"build_result.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stampfly", type=Path, default=Path.home()/"physical_ai_stampfly/stampfly_ecosystem")
    parser.add_argument("--ardupilot", type=Path, default=Path.home()/"physical_ai_ardupilot/ardupilot")
    parser.add_argument("--output", type=Path, default=Path.home()/"physical_ai_ardupilot/bridge")
    parser.add_argument("--camera-mass-g",type=float,default=7.)
    parser.add_argument("--camera-size-mm",type=float,nargs=3,default=[22.,24.,20.])
    parser.add_argument("--fresh",action="store_true")
    args = parser.parse_args()
    build(args.stampfly, args.ardupilot, args.output,args.camera_mass_g,args.camera_size_mm,args.fresh)
