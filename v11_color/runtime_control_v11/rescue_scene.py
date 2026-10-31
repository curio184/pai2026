"""A forward RGB camera and two static rescue mannequins for the flight plant."""
import argparse
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from PIL import Image


def portable_asset_path(value):
    override=os.environ.get("STAMPFLY_MESH_DIR")
    if override:
        if not Path(override).is_dir():raise FileNotFoundError("STAMPFLY_MESH_DIR does not exist")
        return override
    # Archived model XML can refer to the original author's home directory.
    # A fresh Linux setup may use the same pinned assets in its own home.
    if os.name!="nt" and not Path(value).is_dir():
        local=Path.home()/"physical_ai_stampfly/stampfly_ecosystem/simulator/shared/assets/meshes/parts"
        if local.is_dir():return str(local)
    if os.name == "nt" and value.startswith("/home/"):
        return "\\\\wsl.localhost\\Ubuntu-22.04"+value.replace("/", "\\")
    return value


def create_scene(base_model, output, seed=20261024):
    tree = ET.parse(base_model)
    root = tree.getroot()
    root.find("compiler").set("meshdir", portable_asset_path(root.find("compiler").get("meshdir")))
    world = root.find("worldbody")
    drone = world.find("body[@name='drone']")
    # Lens forward (+body X), image right (-body Y), image up (+body Z).
    # FOV and lens offset remain engineering assumptions pending hardware calibration.
    ET.SubElement(drone,"camera",name="front_rgb",pos="0.014 0 0.025",xyaxes="0 -1 0 0 0 1",fovy="64")
    ET.SubElement(world,"geom",name="back_wall",type="box",pos="5 0 1.3",size="0.08 3 1.3",rgba="0.75 0.75 0.72 1")
    ET.SubElement(world,"geom",name="left_wall",type="box",pos="1 3 1.3",size="4 0.08 1.3",rgba="0.7 0.73 0.75 1")
    ET.SubElement(world,"geom",name="right_wall",type="box",pos="1 -3 1.3",size="4 0.08 1.3",rgba="0.7 0.73 0.75 1")
    rng=np.random.default_rng(seed)
    swap=int(rng.integers(2))
    targets={}
    for i,side in enumerate([-1,1]):
        color = ["blue","red"][(i+swap)%2]
        pos=[float(rng.uniform(2.9,3.4)),float(side*rng.uniform(.55,.95)),0]
        person=ET.SubElement(world,"body",name=color+"_person",pos=" ".join(map(str,pos)))
        shirt="0.04 0.18 0.9 1" if color=="blue" else "0.9 0.06 0.05 1"
        ET.SubElement(person,"geom",type="box",pos="0 0 1.03",size="0.12 0.22 0.28",rgba=shirt)
        ET.SubElement(person,"geom",type="sphere",pos="0 0 1.48",size="0.13",rgba="0.75 0.54 0.38 1")
        for y in [-.12,.12]:
            ET.SubElement(person,"geom",type="capsule",**{"fromto":f"0 {y} .12 0 {y} .70","size":".07","rgba":".12 .14 .17 1"})
        for y in [-.29,.29]:
            ET.SubElement(person,"geom",type="capsule",**{"fromto":f"0 {y} .82 0 {y} 1.20","size":".065","rgba":shirt})
        targets[color]=pos
    tree.write(output,encoding="utf-8",xml_declaration=True)
    return targets


class Camera:
    def __init__(self, path, width=320, height=240):
        self.live=None
        if Path(path).with_suffix('.render.json').is_file():
            from civic_camera import LiveCamera
            self.live=LiveCamera(path,width,height)
            self.provenance=self.live.provenance
            return
        tree=ET.parse(path)
        comp=tree.getroot().find("compiler")
        comp.set("meshdir",portable_asset_path(comp.get("meshdir")))
        self.model=mujoco.MjModel.from_xml_string(ET.tostring(tree.getroot(),encoding="unicode"))
        self.data=mujoco.MjData(self.model)
        self.renderer=mujoco.Renderer(self.model,height=height,width=width)

    def render(self, qpos, qvel=None):
        if self.live is not None:return self.live.render(qpos,qvel)
        self.data.qpos[:]=qpos
        self.data.qvel[:]=np.zeros(6) if qvel is None else qvel
        mujoco.mj_forward(self.model,self.data)
        self.renderer.update_scene(self.data,camera="front_rgb")
        return self.renderer.render().copy()

    def close(self):
        if self.live is not None:
            self.live.close();return
        self.renderer.close()


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("base",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    targets=create_scene(a.base,a.output)
    camera=Camera(a.output)
    try:
        rgb=camera.render([0,0,1.03,1,0,0,0])
        Image.fromarray(rgb).save(a.output.with_suffix(".png"))
        print(targets)
    finally: camera.close()
