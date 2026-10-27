"""Render recorded physics and the exact JPEGs used by the final VLA.

This replays logs only. It cannot change a flight, action, score or checkpoint.
The external view and trajectory marker are presentation aids, not VLA inputs.
"""
import argparse
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from rescue_scene import portable_asset_path

WIDTH, HEIGHT = 1280, 720
FPS, SPEED = 20, 2.0
BG, PANEL, INK, MUTED = "#0b1424", "#152238", "#f1f5fa", "#a3b3c8"
TEAL, ORANGE = "#47dfc1", "#ffbb6b"
LABELS = {"takeoff": "離陸して", "hover": "その場で止まって", "blue": "青い服の人の前で止まって",
          "red": "赤い服の人の前で止まって", "right": "右に90度回って", "left": "左に90度回って", "land": "着陸して"}


@lru_cache(maxsize=12)
def font(size):
    candidates = [Path(os.environ.get("WINDIR", "C:/Windows"))/"Fonts/BIZ-UDGothicR.ttc",
                  Path(os.environ.get("WINDIR", "C:/Windows"))/"Fonts/msgothic.ttc",
                  Path("/mnt/c/Windows/Fonts/BIZ-UDGothicR.ttc"),
                  Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc")]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    raise FileNotFoundError("A Japanese TrueType font is required")


def text(draw, xy, value, size=20, fill=INK):
    draw.text(xy, str(value), font=font(size), fill=fill)


class ExternalView:
    def __init__(self, scene):
        tree = ET.parse(scene)
        compiler = tree.getroot().find("compiler")
        compiler.set("meshdir", portable_asset_path(compiler.get("meshdir")))
        self.model = mujoco.MjModel.from_xml_string(ET.tostring(tree.getroot(), encoding="unicode"))
        self.model.vis.global_.offwidth = 840
        self.model.vis.global_.offheight = 480
        self.data = mujoco.MjData(self.model)
        self.options=mujoco.MjvOption()
        # A cutaway of walls improves the external presentation only. This is a
        # separate replay model; neither physics contacts nor VLA JPEGs change.
        for name in ["back_wall","left_wall","right_wall"]:
            index=mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_GEOM,name)
            if index>=0:self.model.geom_group[index]=5
        self.options.geomgroup[5]=0
        self.renderer = mujoco.Renderer(self.model, width=840, height=480)
        self.camera = mujoco.MjvCamera()
        self.camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        self.camera.lookat[:] = [1.55, 0, .7]
        self.camera.distance = 5.1
        self.camera.azimuth = 145
        self.camera.elevation = -26

    def render(self, row, trail):
        self.data.qpos[:] = row["truth"][19:26]
        self.data.qvel[:] = row["truth"][26:32]
        mujoco.mj_forward(self.model, self.data)
        self.renderer.update_scene(self.data, camera=self.camera,scene_option=self.options)
        # Geoms below are drawn after physics replay; they cannot affect contact.
        scene = self.renderer.scene
        for position in trail[::max(1, len(trail)//80)]:
            if scene.ngeom >= scene.maxgeom:
                break
            geom = scene.geoms[scene.ngeom]
            mujoco.mjv_initGeom(geom, mujoco.mjtGeom.mjGEOM_SPHERE, np.array([.018, 0, 0]),
                               np.asarray(position), np.eye(3).ravel(), np.array([.15, .85, .7, .7]))
            scene.ngeom += 1
        position = np.asarray(row["truth"][19:22])
        if scene.ngeom < scene.maxgeom:
            mujoco.mjv_initGeom(scene.geoms[scene.ngeom], mujoco.mjtGeom.mjGEOM_SPHERE,
                               np.array([.065, 0, 0]), position, np.eye(3).ravel(), np.array([1., .7, .15, .38]))
            scene.ngeom += 1
        return Image.fromarray(self.renderer.render().copy())

    def close(self):
        self.renderer.close()


class FlightRecord:
    def __init__(self, directory):
        self.directory = directory
        self.rows = [json.loads(line) for line in (directory/"trace.jsonl").read_text(encoding="utf-8").splitlines()]
        self.times = np.array([row["t"] for row in self.rows])
        self.score = json.loads((directory/"physical_score.json").read_text(encoding="utf-8"))
        events = json.loads((directory/"vla_link_events.json").read_text(encoding="utf-8"))
        self.inputs = {event["sim_time_capture"]: event for event in events if event.get("event") == "inference"}
        self.cached_input = None
        self.cached_image = None

    def at(self, moment):
        index = max(0, min(len(self.rows)-1, int(np.searchsorted(self.times, moment, side="right")-1)))
        row = self.rows[index]
        packet = self.inputs.get(row.get("model_capture_time"))
        image = None
        if packet and packet.get("image_file"):
            if packet["id"] != self.cached_input:
                file = self.directory/"observations"/packet["image_file"]
                if hashlib.sha256(file.read_bytes()).hexdigest() != packet["image_sha256"]:
                    raise ValueError("Recorded model-input JPEG checksum mismatch")
                self.cached_image = Image.open(file).convert("RGB").resize((320, 240))
                self.cached_input = packet["id"]
            image = self.cached_image
        return index, row, packet, image


def card(title, lines, accent=TEAL):
    frame = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(frame)
    draw.rectangle((68, 105, 76, 585), fill=accent)
    text(draw, (110, 118), "PHYSICAL AI / RESCUE DRONE", 22, accent)
    text(draw, (110, 183), title, 44)
    for i, line in enumerate(lines):
        text(draw, (112, 285+54*i), line, 26, MUTED)
    return np.asarray(frame)


def flight_frame(record, external, moment, profile):
    index, row, packet, onboard = record.at(moment)
    frame = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(frame)
    text(draw, (28, 16), "ことばで探す救助ドローン", 30)
    text(draw, (945, 25), "物理ログ再生 / 2倍速", 21, TEAL)
    text(draw, (29, 61), f"指示: {LABELS.get(row['phase'], row['phase'])}", 23, TEAL)
    text(draw, (980, 63), f"sim {row['t']:05.1f} s", 21, MUTED)
    trail = [r["truth"][19:22] for r in record.rows[max(0, index-1200):index:8]]
    frame.paste(external.render(row, trail), (24, 108))
    draw.rectangle((33,116,365,145),fill=BG)
    text(draw,(41,120),"壁は外部視点でのみ非表示",18,MUTED)
    draw.rounded_rectangle((884, 108, 1256, 587), radius=14, fill=PANEL)
    text(draw, (905, 119), "VLAが受け取った入力画像", 21)
    if onboard is not None:
        frame.paste(onboard, (910, 155))
    else:
        draw.rectangle((910, 155, 1230, 395), fill="#050a12")
        text(draw, (929, 260), "入力画像の受信待ち", 20, MUTED)
    age = row["t"]-packet["sim_time_capture"] if packet else None
    text(draw, (905, 408), f"画像の経過時間: {age:.2f} s" if age is not None else "画像の経過時間: -", 20, ORANGE)
    text(draw, (905, 440), "画像は推論の更新に合わせて切替", 18, MUTED)
    action = row["model_action"]
    text(draw, (905, 480), f"前進 {action[0]:+.2f} / 左 {action[1]:+.2f} m/s", 19)
    text(draw, (905, 510), f"上昇 {action[2]:+.2f} m/s", 19)
    text(draw, (905, 540), f"旋回 {math.degrees(action[3]):+.1f} deg/s", 19)
    height = -row["truth"][3]
    speed = np.linalg.norm(row["truth"][4:6])
    text(draw, (28, 603), f"物理高度 {height:.2f} m     水平速度 {speed:.2f} m/s", 22)
    text(draw, (28, 639), "外部視点・軌跡・黄色の位置マーカーは表示用。VLAへの入力には使いません。", 18, MUTED)
    status = "成功" if record.score["success"] else "未達"
    text(draw, (923, 605), f"独立採点: {status}", 26, TEAL if record.score["success"] else ORANGE)
    text(draw, (923, 648), f"CASE {profile.upper()}", 20, MUTED)
    text(draw, (28, 686), "SmolVLA + ArduPilot + MuJoCo | シミュレーション記録・実機飛行なし", 17, MUTED)
    return np.asarray(frame)


def replay_segments(record):
    start=max(16.,float(record.times[0]));end=float(record.times[-1])
    if end-start<=66:return [(start,end)]
    # Presentation only: retain the first 38 s and final 28 s at the same 2x
    # replay speed. The timestamp jump and omitted duration are labeled.
    return [(start,start+38),(end-28,end)]


def make(args):
    root = args.records
    manifest = json.loads((root/"verification_manifest.json").read_text(encoding="utf-8"))
    records = {profile: FlightRecord(root/profile) for profile in manifest["profiles"]}
    for record in records.values():
        if not record.score["learned_policy_provenance"] or record.score["checkpoints"] != [manifest["checkpoint_sha256"]]:
            raise ValueError("Video requires records of the same final learned policy")
    scene = args.scene or root/"rescue_scene.xml"
    external = ExternalView(scene)
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    if args.preview_only:
        try:
            profile = manifest["profiles"][0]
            record = records[profile]
            moment = float(record.times[len(record.times)//2])
            Image.fromarray(flight_frame(record, external, moment, profile)).save(output)
        finally:
            external.close()
        return
    duration = 6+16+4*len(records)+sum(sum(end-start for start,end in replay_segments(record))/SPEED for record in records.values())
    if duration > 180:
        raise ValueError("Labeled replay sections exceed three minutes at fixed 2x speed")
    import imageio.v2 as imageio
    count = 0
    sections = []
    try:
        with imageio.get_writer(output, fps=FPS, codec="libx264", quality=8, macro_block_size=16,
                                ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]) as writer:
            def hold(frame, seconds):
                nonlocal count
                for _ in range(round(seconds*FPS)):
                    writer.append_data(frame)
                    count += 1
            hold(card("ことばで探す救助ドローン", ["カメラ画像 + 言語指示 + 機体の自己推定状態", "学習済みSmolVLAが飛行アクションを出力", f"最終チェックポイントで必要な{len(records)}つの飛行を確認"]), 6)
            for profile, record in records.items():
                hold(card(f"CASE {profile.upper()}", ["離陸 → その場で停止 → 指示動作 → 着陸を確認", "飛行区間は2倍速。初期化の最初16秒を省略。", "長いケースは中間を省略し、原ログの時刻を表示。"]), 4)
                segments=replay_segments(record)
                sections.append(dict(profile=profile,sim_segments_s=segments,speed=SPEED,success=record.score["success"],
                                     omitted_middle_s=sum(max(0,segments[i][0]-segments[i-1][1]) for i in range(1,len(segments)))))
                for segment_index,(start,end) in enumerate(segments):
                    for moment in np.arange(start,end,SPEED/FPS):
                        frame=flight_frame(record,external,float(moment),profile)
                        if segment_index and moment-start<4:
                            overlay=Image.fromarray(frame);draw=ImageDraw.Draw(overlay)
                            draw.rectangle((36,531,842,574),fill=BG)
                            skipped=start-segments[segment_index-1][1]
                            text(draw,(47,540),f"中間 {skipped:.1f} 秒を省略 / 表示時刻は原ログ",22,ORANGE)
                            frame=np.asarray(overlay)
                        writer.append_data(frame);count+=1
                print(json.dumps(dict(profile=profile,frames_written=count)), flush=True)
            all_pass = all(record.score["success"] for record in records.values())
            hardware=json.loads((Path(__file__).parent/"outputs/hardware_sources/design_review.json").read_text(encoding="utf-8"))
            hold(card("実在する小型機への接続を想定", [f"StampFly v1.1 + RGBカメラ + 光学フロー/距離センサー",
                      f"設計重量 {hardware['assembly_design_mass_g']:.0f} g / 計画予算 {hardware['budget_planning_total_jpy']:,} 円",
                      "搭載余裕・カメラの型番別電力・無線同時動作は未検証"]), 8)
            hold(card("物理ログによる独立採点", [f"{len(records)}つの機能確認: {'すべて成功' if all_pass else '未達の項目あり（各CASEの採点を参照）'}",
                      "実行時のVLAには人物の真の位置を渡さない", "実機の搭載余裕・無線の同時動作は別途確認が必要"], TEAL if all_pass else ORANGE), 8)
    finally:
        external.close()
    report = dict(output=output.name,frames=count,fps=FPS,duration_s=count/FPS,sections=sections,
                  checkpoint_sha256=manifest["checkpoint_sha256"],same_final_model=True,
                  onboard_frames="Exact recorded JPEGs, checked by SHA256; held between inference responses",
                  physical_replay_only=True,real_flight=False,minimum_60_seconds=count/FPS>=60)
    output.with_suffix(".json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--scene", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview-only", action="store_true")
    make(parser.parse_args())
