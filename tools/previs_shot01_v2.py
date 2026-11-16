# -*- coding: utf-8 -*-
"""白模预演 v2：老厂区楼道口 · 结尾幻觉镜头（shot01 重做）。

修复 shot01 v1 的问题（见 .workbuddy/memory/2026-11-01.md 续 7）：
1. 陷腰：所有角色 z≈-0.2、脚在 -1.0。v2 按世界 bbox 实测，自动把每只脚
   落到期望地面高度（ground_z 按 E01 缩放后的楼层：ground -1.35 /
   mid-stair -0.72 / landing -0.225）。
2. 相机目标改用头骨世界坐标（mixamorig:Head），不再拍估算高度。

Run:
  PREVIS_TEST=1 blender.exe --background --python tools/previs_shot01_v2.py   # 5 帧试渲
  blender.exe --background --python tools/previs_shot01_v2.py                 # 全量 192 帧
"""
import json
import math
import os

import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames_v2")

FPS = 24
DURATION_S = 8
N_FRAMES = FPS * DURATION_S
RES_X, RES_Y = 1280, 720

# E01 scaled 1.5x about its base: ground z=-1.35, mid-stair ~-0.72, landing ~-0.225.
GROUND = {"ground": -1.35, "mid": -0.72, "landing": -0.225}

PLACEMENTS = {
    "C08": {"file": "tex_mesh_v04_rigged.glb", "pos": (0.60, 0.62), "ground": "landing",
            "rot_z": 155, "raise_right": True},
    "C09": {"file": "tex_mesh_v04_rigged_scaled16.glb", "pos": (-0.95, 0.45), "ground": "landing",
            "rot_z": 200, "raise_right": False},
    "C12": {"file": "tex_mesh_v04_rigged.glb", "pos": (0.55, -1.40), "ground": "ground",
            "rot_z": 140, "raise_right": False, "point_at_bike": True},
    "C01": {"file": "tex_mesh_v04_rigged.glb", "pos": (-0.18, -0.02), "ground": "mid",
            "rot_z": 185, "raise_right": False},
}
E01_FILE = "tex_mesh.glb"
E01_SCALE = 1.5
P14_FILE = "tex_mesh.glb"
P14_TARGET = (1.15, -1.45, -1.34)
P14_SCALE = 0.32

# camera push-in path (positions kept from v1; targets replaced by head bones)
CAM_START_POS = (4.6, -7.2, 2.90)
CAM_END_POS = (3.0, -4.4, 2.20)


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.context.scene.objects if o not in before]


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def make_matte():
    mat = bpy.data.materials.new("previz_matte")
    mat.use_nodes = True
    bsdf = None
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            bsdf = n
            break
    bsdf.inputs["Base Color"].default_value = (0.78, 0.78, 0.78, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Metallic"].default_value = 0.0
    return mat


def apply_matte(objs):
    mat = make_matte()
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(mat)


def world_bbox(objs):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for corner in o.bound_box:
            w = o.matrix_world @ Vector(corner)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
    return mn, mx


def rotate_pose_bone_world(arm_obj, bone_name, world_axis, angle_deg):
    pb = arm_obj.pose.bones.get(bone_name)
    if pb is None:
        return False
    rest_q = pb.bone.matrix_local.to_quaternion()
    q_world = Quaternion(Vector(world_axis).normalized(), math.radians(angle_deg))
    q_local = rest_q.inverted() @ q_world @ rest_q
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = q_local
    return True


def pose_character(cid, cfg):
    path = os.path.join(MODELS, cid, cfg["file"])
    imported = import_glb(path)
    # build all lists BEFORE removing gizmos (touching a removed object raises)
    gizmos = [o for o in imported if o.type == "MESH" and "棱角球" in o.name]
    arm = [o for o in imported if o.type == "ARMATURE"]
    new_meshes = [o for o in imported if o.type == "MESH" and "棱角球" not in o.name]
    for o in gizmos:
        bpy.data.objects.remove(o, do_unlink=True)
    if arm:
        arm_obj = arm[-1]
        arm_obj.location = (cfg["pos"][0], cfg["pos"][1], 0.0)
        arm_obj.rotation_euler = (0, 0, math.radians(cfg["rot_z"]))
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="POSE")
        if cfg.get("raise_right"):
            rotate_pose_bone_world(arm_obj, "mixamorig:RightArm", (0, 1, 0), 108)
            rotate_pose_bone_world(arm_obj, "mixamorig:RightForeArm", (1, 0, 0), -70)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftArm", (0, 1, 0), -78)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftForeArm", (1, 0, 0), -22)
        elif cfg.get("point_at_bike"):
            rotate_pose_bone_world(arm_obj, "mixamorig:RightArm", (0, 1, 0), 150)
            rotate_pose_bone_world(arm_obj, "mixamorig:RightForeArm", (1, 0, 0), -35)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftArm", (0, 1, 0), -80)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftForeArm", (1, 0, 0), -20)
        else:
            rotate_pose_bone_world(arm_obj, "mixamorig:RightArm", (0, 1, 0), -76)
            rotate_pose_bone_world(arm_obj, "mixamorig:RightForeArm", (1, 0, 0), -25)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftArm", (0, 1, 0), 76)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftForeArm", (1, 0, 0), -25)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.update()
        # --- grounding fix: feet exactly on the intended floor ---
        mn, _ = world_bbox(new_meshes)
        target_z = GROUND[cfg["ground"]]
        arm_obj.location.z += target_z - mn.z
        bpy.context.view_layer.update()
        print(f"[previs01v2] {cid} foot_z {mn.z:.3f} -> {target_z:.3f}, "
              f"arm_z {arm_obj.location.z:.3f}", flush=True)
        return arm_obj
    return None


def head_world(arm_obj):
    pb = arm_obj.pose.bones.get("mixamorig:Head")
    if pb is None:
        return None
    return arm_obj.matrix_world @ pb.head


def add_ribbon(arm_obj):
    pb = arm_obj.pose.bones.get("mixamorig:RightHand")
    if pb is None:
        return None
    hand_world = arm_obj.matrix_world @ pb.head
    bpy.ops.mesh.primitive_cube_add(size=0.035)
    strip = bpy.context.active_object
    strip.scale = (0.7, 0.3, 11.0)
    bpy.ops.object.transform_apply(scale=True)
    strip.location = (hand_world.x, hand_world.y, hand_world.z - 0.24)
    mat = bpy.data.materials.new("ribbon_red")
    mat.use_nodes = True
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (0.72, 0.10, 0.12, 1.0)
            n.inputs["Roughness"].default_value = 0.6
    strip.data.materials.append(mat)
    return strip


def add_lighting():
    world = bpy.data.worlds.new("previz_world")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.42, 0.44, 0.48, 1.0)
            n.inputs[1].default_value = 0.55
    bpy.context.scene.world = world
    bpy.ops.object.light_add(type="AREA", location=(2.5, -3.5, 3.2))
    key = bpy.context.active_object
    key.data.energy = 900
    key.data.size = 2.5
    bpy.ops.object.light_add(type="AREA", location=(-2.0, 1.5, 2.5))
    fill = bpy.context.active_object
    fill.data.energy = 350
    fill.data.size = 3.0


def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    add_lighting()

    import_glb(os.path.join(MODELS, "E01", E01_FILE))
    env_meshes = mesh_objects()
    for o in env_meshes:
        o.scale = (E01_SCALE, E01_SCALE, E01_SCALE)
    bpy.context.view_layer.update()

    import_glb(os.path.join(MODELS, "P14", P14_FILE))
    bike_meshes = [o for o in mesh_objects() if o not in env_meshes]
    for o in bike_meshes:
        o.scale = (P14_SCALE, P14_SCALE, P14_SCALE)
    bpy.context.view_layer.update()
    for o in bike_meshes:
        o.rotation_euler = (0, 0, math.radians(90))
    bpy.context.view_layer.update()
    bmn, bmx = world_bbox(bike_meshes)
    shift = Vector(P14_TARGET) - Vector(((bmn.x + bmx.x) / 2, (bmn.y + bmx.y) / 2, bmn.z))
    for o in bike_meshes:
        o.location += shift
    bpy.context.view_layer.update()

    arms = {}
    for cid, cfg in PLACEMENTS.items():
        arms[cid] = pose_character(cid, cfg)
    if arms.get("C08") is not None:
        add_ribbon(arms["C08"])

    apply_matte([o for o in mesh_objects() if not o.name.startswith("Cube")])

    # camera targets from actual head bones (granny weighted: she holds the ribbon)
    h8 = head_world(arms["C08"])
    h1 = head_world(arms["C01"])
    h9 = head_world(arms["C09"])
    h2 = head_world(arms["C12"])
    if None not in (h8, h1, h9, h2):
        tgt_start = h8 * 0.30 + h1 * 0.30 + h9 * 0.20 + h2 * 0.20
        tgt_end = h8 * 0.35 + h1 * 0.30 + h9 * 0.15 + h2 * 0.20
        print(f"[previs01v2] heads C08={tuple(round(v,2) for v in h8)} "
              f"C01={tuple(round(v,2) for v in h1)} tgt_start={tuple(round(v,2) for v in tgt_start)}", flush=True)
    else:
        tgt_start = Vector((0.10, 0.15, 0.50))
        tgt_end = Vector((0.35, 0.30, 0.55))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = N_FRAMES
    if os.environ.get("PREVIS_VIDEO") == "1":
        scene.render.image_settings.file_format = "FFMPEG"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
        scene.render.filepath = os.path.join(OUT_DIR, "previs_shot01_v2.mp4")
    else:
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGB"

    cam_data = bpy.data.cameras.new("previs_cam")
    cam_data.type = "PERSP"
    cam_data.lens = 32
    cam = bpy.data.objects.new("previs_cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    sp = Vector(CAM_START_POS)
    ep = Vector(CAM_END_POS)
    st = Vector(tgt_start)
    et = Vector(tgt_end)

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y],
              "grounding": GROUND, "views": {}}
    test_mode = os.environ.get("PREVIS_TEST") == "1"
    frames_iter = [1, 48, 96, 144, 192] if test_mode else range(1, N_FRAMES + 1)
    for f in frames_iter:
        t = ease_in_out((f - 1) / (N_FRAMES - 1))
        pos = sp.lerp(ep, t)
        tgt = st.lerp(et, t)
        cam.location = pos
        direction = tgt - pos
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        if os.environ.get("PREVIS_VIDEO") != "1":
            scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f in (1, N_FRAMES // 2, N_FRAMES):
            report["views"][str(f)] = scene.render.filepath
        if f % 48 == 0:
            print(f"[previs01v2] frame {f}/{N_FRAMES}", flush=True)

    with open(os.path.join(OUT_DIR, "previs_report_v2.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS_V2_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
