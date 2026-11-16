# -*- coding: utf-8 -*-
"""白模预演：家中卧室 · shot05「清晨枕下发带」双人床沿（Blender 相机调度）。

开篇下一场：姥姥去世后的清晨，许宁醒得很早，红发带在枕头下焐热了。
她坐在床上等妈妈来扎辫子，妈妈推门进来，在床边坐下，说姥姥去世了。
许宁听见了，仍把发带递过去。妈妈接住，捏在手里，许久没有动。

本镜为低调度静态瞬间（过程描述交 H3 提示词），只有相机缓推。
复用 E03 卧室（+1.2 x 平移）+ C01 + C09。

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot05.py   (5 帧构图测试)
  blender.exe --background --python tools/previs_shot05.py                          (192 帧全量)
"""
import json
import math
import os

import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames05")

FPS = 24
DURATION_S = 8
N_FRAMES = FPS * DURATION_S
RES_X, RES_Y = 1280, 720

FLOOR_Z = -0.60
E03_SHIFT_X = 1.2
# 床沿坐高：床垫面约 z=0.0（floor+0.6），坐姿髋 = 床面 + 0.10
SIT_HIP_Z = 0.12

# ---- staging ----
# 床实测（+1.2 平移后，顶视探针校准）：床面 x 0.28~1.50（宽 1.2m 单人床），
# 床头 y≈+2.1（枕头端），床尾近端 y≈-1.1，床垫/毯面 z≈0.0~0.1
# 母女并坐床尾短边沿，面向 -y（镜头方向），腿垂在床尾前方空地上
# 角色 glb 骨架原生面向 -y，rotation_euler 对导入骨架不生效，rot 一律用 0
C01_POS = (0.52, -1.02, SIT_HIP_Z)   # 许宁，画面左侧
C09_POS = (1.02, -0.98, SIT_HIP_Z)   # 妈妈，在她左边（画面右侧），同坐床尾沿
# 红发带在两人伸出的手之间：许宁左手递，妈妈右手接

# 许宁：坐姿，左手把发带递向妈妈（+x 方向）
POSE_C01 = [
    ("mixamorig:RightUpLeg",  (1, 0, 0), -88),   # 大腿向前平抬（面向 -y）
    ("mixamorig:LeftUpLeg",   (1, 0, 0), -88),
    ("mixamorig:RightLeg",    (1, 0, 0), 85),    # 小腿垂下
    ("mixamorig:LeftLeg",     (1, 0, 0), 85),
    ("mixamorig:Spine",       (1, 0, 0), 4),     # 微微前倾，注意力在手上
    ("mixamorig:Neck",        (1, 0, 0), 6),
    ("mixamorig:Head",        (1, 0, 0), 4),
    ("mixamorig:LeftArm",     (0, 0, 1), -52),   # 左臂伸向妈妈（+x 前伸）
    ("mixamorig:LeftForeArm", (0, 0, 1), -20),   # 肘部前屈
    ("mixamorig:RightForeArm",(0, 0, 1), 12),    # 右手自然搭在腿边
]
# 妈妈：坐姿，右手接过发带，低头看它
POSE_C09 = [
    ("mixamorig:RightUpLeg",  (1, 0, 0), -88),
    ("mixamorig:LeftUpLeg",   (1, 0, 0), -88),
    ("mixamorig:RightLeg",    (1, 0, 0), 85),
    ("mixamorig:LeftLeg",     (1, 0, 0), 85),
    ("mixamorig:Spine",       (1, 0, 0), 10),    # 俯身
    ("mixamorig:Neck",        (1, 0, 0), 18),    # 低头看发带
    ("mixamorig:Head",        (1, 0, 0), 12),
    ("mixamorig:RightArm",    (0, 0, 1), 52),    # 右臂伸向许宁（-x 前伸）
    ("mixamorig:RightForeArm",(0, 0, 1), 20),
    ("mixamorig:LeftArm",     (0, 0, 1), -70),   # 左臂收放到腿上
    ("mixamorig:LeftForeArm", (0, 0, 1), -25),
]

# 机位：床尾正面偏左，缓推（前墙内表面 y≈-3.14，机位 y 不得越界）
CAM_START_POS = (0.55, -3.05, 1.25)
CAM_END_POS = (1.00, -2.55, 1.08)
CAM_LENS = 35


def face_rot_z(src, dst):
    dx, dy = dst[0] - src[0], dst[1] - src[1]
    return math.degrees(math.atan2(-dx, dy)) % 360


def bend_axis(rot_z_deg):
    t = math.radians(rot_z_deg)
    return (-math.cos(t), -math.sin(t), 0.0)


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def make_matte(name="previz_matte05"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (0.78, 0.78, 0.78, 1.0)
            n.inputs["Roughness"].default_value = 0.95
            n.inputs["Metallic"].default_value = 0.0
    return mat


def apply_matte(objs):
    mat = make_matte()
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(mat)


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


def place_character(cid, glb, pos, rot_z, pose):
    path = os.path.join(MODELS, cid, glb)
    import_glb(path)
    for o in [o for o in bpy.context.scene.objects
              if o.type == "MESH" and "棱角球" in o.name]:
        bpy.data.objects.remove(o, do_unlink=True)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    arm_obj = arms[-1]
    arm_obj.rotation_mode = "XYZ"
    arm_obj.location = pos
    arm_obj.rotation_euler = (0, 0, math.radians(rot_z))
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")
    lean = bend_axis(rot_z)
    for bone, axis, angle in pose:
        ax = lean if axis == "lean" else axis
        rotate_pose_bone_world(arm_obj, bone, ax, angle)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def head_world(arm_obj):
    pb = arm_obj.pose.bones.get("mixamorig:Head")
    if pb is None:
        return arm_obj.matrix_world.translation
    return arm_obj.matrix_world @ pb.head


def hand_world(arm_obj, bone="mixamorig:RightHand"):
    pb = arm_obj.pose.bones.get(bone)
    if pb is None:
        return None
    return arm_obj.matrix_world @ pb.head


def add_box(name, loc, dims, mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    box = bpy.context.active_object
    box.name = name
    box.location = loc
    box.dimensions = dims
    if mat is not None:
        box.data.materials.append(mat)
    return box


def build_room():
    """卧室外壳（复用 E03 布局，晨光偏冷一点——失去后的清晨）。"""
    wall = make_matte()
    add_box("floor", (0.8, 0, FLOOR_Z - 0.05), (10.0, 8.0, 0.1), wall)
    add_box("ceiling", (0.8, 0, 2.40), (10.0, 8.0, 0.1), wall)
    add_box("wall_right", (3.9, 0, 0.9), (0.12, 6.0, 3.0), wall)
    add_box("wall_left", (-2.4, 0, 0.9), (0.12, 6.4, 3.0), wall)
    add_box("wall_back", (0.8, 2.8, 0.9), (6.4, 0.12, 3.0), wall)
    add_box("wall_front", (0.8, -3.2, 0.9), (6.4, 0.12, 3.0), wall)
    # 窗（+y 墙）
    wy = 2.74
    add_box("wall_win_left", (-0.95, wy, 0.9), (2.9, 0.12, 3.0), wall)
    add_box("wall_win_right", (3.35, wy, 0.9), (1.0, 0.12, 3.0), wall)
    add_box("wall_win_sill", (1.2, wy, -0.55), (2.0, 0.12, 1.1), wall)
    add_box("wall_win_top", (1.2, wy, 2.25), (2.0, 0.12, 0.3), wall)
    glass_mat = bpy.data.materials.new("window_glass05")
    glass_mat.use_nodes = True
    for n in glass_mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (0.95, 0.95, 1.0, 1.0)
            n.inputs["Roughness"].default_value = 0.1
            if "Emission Color" in n.inputs:
                n.inputs["Emission Color"].default_value = (0.9, 0.92, 1.0, 1.0)
                n.inputs["Emission Strength"].default_value = 1.6
    add_box("window_glass", (1.2, wy, 1.30), (2.1, 0.04, 1.6), glass_mat)
    add_box("window_mullion_v", (1.2, wy - 0.03, 1.30), (0.06, 0.05, 1.6), wall)
    add_box("window_mullion_h", (1.2, wy - 0.03, 1.30), (2.1, 0.05, 0.06), wall)
    # 梳妆台+镜（背景右）
    mirror_mat = bpy.data.materials.new("mirror_glass05")
    mirror_mat.use_nodes = True
    for n in mirror_mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (0.9, 0.92, 0.94, 1.0)
            n.inputs["Roughness"].default_value = 0.05
            n.inputs["Metallic"].default_value = 0.6
            if "Emission Color" in n.inputs:
                n.inputs["Emission Color"].default_value = (0.8, 0.83, 0.86, 1.0)
                n.inputs["Emission Strength"].default_value = 0.4
    add_box("mirror_glass", (3.82, 0.10, 1.15), (0.04, 1.2, 1.6), mirror_mat)
    add_box("mirror_frame_top", (3.83, 0.10, 1.98), (0.08, 1.34, 0.08), wall)
    add_box("mirror_frame_bot", (3.83, 0.10, 0.32), (0.08, 1.34, 0.08), wall)
    add_box("mirror_frame_l", (3.83, -0.56, 1.15), (0.08, 0.08, 1.74), wall)
    add_box("mirror_frame_r", (3.83, 0.76, 1.15), (0.08, 0.08, 1.74), wall)


def add_ribbon(girl_arm, mom_arm):
    """红发带：横在两人伸出的手之间。"""
    # 红发带：许宁左手 ↔ 妈妈右手
    gh = hand_world(girl_arm, "mixamorig:LeftHand")
    mh = hand_world(mom_arm, "mixamorig:RightHand")
    if gh is None or mh is None:
        return None
    center = (gh + mh) / 2
    center.z += 0.05
    d = mh - gh
    bpy.ops.mesh.primitive_cube_add(size=0.02)
    rib = bpy.context.active_object
    rib.name = "ribbon_prop"
    rib.dimensions = (0.05, 0.26, 0.04)
    rib.location = center
    flat = Vector((d.x, d.y, 0.0))
    if flat.length < 1e-6:
        flat = Vector((0, 1, 0))
    rib.rotation_mode = "QUATERNION"
    rib.rotation_quaternion = flat.normalized().to_track_quat("Y", "Z")
    mat = bpy.data.materials.new("ribbon_red05")
    mat.use_nodes = True
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (0.85, 0.05, 0.10, 1.0)
            n.inputs["Roughness"].default_value = 0.5
            if "Emission Color" in n.inputs:
                n.inputs["Emission Color"].default_value = (0.85, 0.05, 0.10, 1.0)
                n.inputs["Emission Strength"].default_value = 0.35
    rib.data.materials.append(mat)
    return rib


def add_lighting():
    world = bpy.data.worlds.new("previz_world05")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.38, 0.40, 0.46, 1.0)
            n.inputs[1].default_value = 0.5
    bpy.context.scene.world = world
    # 晨光（偏冷的晴光）
    bpy.ops.object.light_add(type="AREA", location=(1.2, 4.5, 1.9))
    key = bpy.context.active_object
    key.data.energy = 1300
    key.data.size = 3.0
    key.data.color = (0.92, 0.94, 1.0)
    key.rotation_euler = (math.radians(-70), 0, 0)
    # 正面柔补
    bpy.ops.object.light_add(type="AREA", location=(-1.0, -2.5, 1.7))
    fill = bpy.context.active_object
    fill.data.energy = 450
    fill.data.size = 2.5
    fill.rotation_euler = (math.radians(60), 0, math.radians(-30))


def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    build_room()
    add_lighting()

    pre_existing = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, "E03", "tex_mesh_scaled.glb"))
    for o in [o for o in bpy.context.scene.objects if o not in pre_existing]:
        o.location.x += E03_SHIFT_X
    bpy.context.view_layer.update()
    print(f"[previs05] env meshes={len(mesh_objects())}", flush=True)

    # 角色：glb 骨架原生面向 -y（镜头方向），rot 用 0
    rot = 0.0
    girl = place_character("C01", "tex_mesh_v04_rigged.glb", C01_POS, rot, POSE_C01)
    mom = place_character("C09", "tex_mesh_v04_rigged_scaled16.glb", C09_POS, rot, POSE_C09)
    add_ribbon(girl, mom)

    h1 = head_world(girl)
    h9 = head_world(mom)
    tgt_mid = h1 * 0.56 + h9 * 0.44
    print(f"[previs05] head C01=({h1.x:.2f},{h1.y:.2f},{h1.z:.2f}) "
          f"C09=({h9.x:.2f},{h9.y:.2f},{h9.z:.2f}) "
          f"tgt=({tgt_mid.x:.2f},{tgt_mid.y:.2f},{tgt_mid.z:.2f})", flush=True)
    cam_start_tgt = Vector((tgt_mid.x, tgt_mid.y, tgt_mid.z))
    cam_end_tgt = Vector((tgt_mid.x, tgt_mid.y + 0.04, tgt_mid.z - 0.03))

    apply_matte([o for o in mesh_objects()
                 if "window_glass" not in o.name and "mirror_glass" not in o.name
                 and o.name != "ribbon_prop"])

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = N_FRAMES
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    cam_data = bpy.data.cameras.new("previs_cam05")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.data.objects.new("previs_cam05", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    sp = Vector(CAM_START_POS)
    st = cam_start_tgt
    ep = Vector(CAM_END_POS)
    et = cam_end_tgt

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y],
              "lens": CAM_LENS, "views": {}}
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
        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f in (1, N_FRAMES // 2, N_FRAMES):
            report["views"][str(f)] = scene.render.filepath
        if f % 48 == 0:
            print(f"[previs05] frame {f}/{N_FRAMES}", flush=True)

    with open(os.path.join(OUT_DIR, "previs05_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS05_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
