# -*- coding: utf-8 -*-
"""白模预演：家中卧室镜前 · shot04「妈妈给许宁扎辫子」双人侧景（Blender 相机调度）。

第一章：上小学第一天清晨，妈妈给许宁扎辫子，她仰头问出那句
"你也没有妈妈给你扎头发了吗"。本镜为低调度静态瞬间，只有相机缓推。

E03 实测（probe_e03_bins）：地面 z=-0.60；床在 x -2.2~-1.2（沿 y 轴），
梳妆台在 x +1~+2.2。模型整体 +1.2 平移：床 x -1.0~0.2，梳妆台 x 2.2~3.4。
镜子 img-to-3d 无法重建，Blender 程序化补（镜框+镜面，+x 墙上）。

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot04.py   (5 帧构图测试)
  blender.exe --background --python tools/previs_shot04.py                          (192 帧全量)
"""
import json
import math
import os

import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames04")

FPS = 24
DURATION_S = 8
N_FRAMES = FPS * DURATION_S
RES_X, RES_Y = 1280, 720

FLOOR_Z = -0.60
E03_SHIFT_X = 1.2

# rigged GLB 骨架原点在髋部
HIP_C09 = 0.78   # 妈妈 1.6m

# ---- staging ----
# 许宁坐在梳妆台前小凳上（程序化方凳），面向 +x 镜子
C01_POS = (1.90, 0.00, FLOOR_Z + 0.50)   # 坐姿髋高约 0.50（凳高 0.44+臀肉）
# 妈妈在许宁身后偏 +y 侧（与相机成斜角，双侧面构图两人都露脸）
C09_POS = (1.85, 0.62, FLOOR_Z + HIP_C09)

# 许宁坐姿：大腿抬平向前、小腿垂下；仰头；手放腿上
POSE_C01 = [
    ("mixamorig:RightUpLeg",  (0, 1, 0), -88),
    ("mixamorig:LeftUpLeg",   (0, 1, 0), -88),
    ("mixamorig:RightLeg",    (0, 1, 0), 85),
    ("mixamorig:LeftLeg",     (0, 1, 0), 85),
    ("mixamorig:RightFoot",   (1, 0, 0), -10),
    ("mixamorig:LeftFoot",    (1, 0, 0), -10),
    ("mixamorig:Spine",       "lean", 6),
    ("mixamorig:Neck",        "lean", -12),   # 仰头让妈妈梳头
    ("mixamorig:Head",        "lean", -8),
    ("mixamorig:RightArm",    (0, 1, 0), -14),  # 手自然放腿上
    ("mixamorig:LeftArm",     (0, 1, 0), -18),
    ("mixamorig:RightForeArm", (1, 0, 0), -22),
    ("mixamorig:LeftForeArm", (1, 0, 0), -22),
]
# 妈妈：面向 -y（许宁头侧）俯身，双臂前抬到她头上做梳头动作
POSE_C09 = [
    ("mixamorig:Spine",      "lean", 18),
    ("mixamorig:Spine1",     "lean", 10),
    ("mixamorig:Neck",       "lean", 12),    # 低头看孩子的头发
    ("mixamorig:Head",       "lean", 6),
    ("mixamorig:RightArm",   (1, 0, 0), -68),
    ("mixamorig:RightForeArm", (1, 0, 0), 22),
    ("mixamorig:LeftArm",    (1, 0, 0), -76),
    ("mixamorig:LeftForeArm", (1, 0, 0), 18),
]

# 机位：斜侧角，许宁 3/4 面朝画面右，妈妈在左后俯身，双侧面都可见
CAM_START_POS = (-1.30, -2.20, 1.45)
CAM_END_POS = (-0.70, -1.60, 1.25)
CAM_LENS = 36


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


def make_matte(name="previz_matte04"):
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
    """卧室外壳：地板、墙、窗（晨光）、镜框+镜面。"""
    wall = make_matte()
    add_box("floor", (0.8, 0, FLOOR_Z - 0.05), (10.0, 8.0, 0.1), wall)
    add_box("ceiling", (0.8, 0, 2.40), (10.0, 8.0, 0.1), wall)
    # 墙：+x 在 3.9（梳妆台 2.2~3.4 后），-x 在 -2.4，+y 在 2.8（窗墙），-y 在 -3.2
    add_box("wall_right", (3.9, 0, 0.9), (0.12, 6.0, 3.0), wall)
    add_box("wall_left", (-2.4, 0, 0.9), (0.12, 6.4, 3.0), wall)
    add_box("wall_back", (0.8, 2.8, 0.9), (6.4, 0.12, 3.0), wall)
    add_box("wall_front", (0.8, -3.2, 0.9), (6.4, 0.12, 3.0), wall)
    # 窗（+y 墙，晨光）：x 0.2~2.2，窗台 z=0.5，窗顶 z=2.1
    wy = 2.74
    add_box("wall_win_left", (-0.95, wy, 0.9), (2.9, 0.12, 3.0), wall)
    add_box("wall_win_right", (3.35, wy, 0.9), (1.0, 0.12, 3.0), wall)
    add_box("wall_win_sill", (1.2, wy, -0.55), (2.0, 0.12, 1.1), wall)
    add_box("wall_win_top", (1.2, wy, 2.25), (2.0, 0.12, 0.3), wall)
    glass_mat = bpy.data.materials.new("window_glass04")
    glass_mat.use_nodes = True
    for n in glass_mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (1.0, 0.95, 0.82, 1.0)
            n.inputs["Roughness"].default_value = 0.1
            if "Emission Color" in n.inputs:
                n.inputs["Emission Color"].default_value = (1.0, 0.93, 0.75, 1.0)
                n.inputs["Emission Strength"].default_value = 2.0
    add_box("window_glass", (1.2, wy, 1.30), (2.1, 0.04, 1.6), glass_mat)
    add_box("window_mullion_v", (1.2, wy - 0.03, 1.30), (0.06, 0.05, 1.6), wall)
    add_box("window_mullion_h", (1.2, wy - 0.03, 1.30), (2.1, 0.05, 0.06), wall)
    # 镜子（+x 墙，面向房间/相机）：镜面 y 0.1±0.6，z 0.35~1.95
    mirror_mat = bpy.data.materials.new("mirror_glass04")
    mirror_mat.use_nodes = True
    for n in mirror_mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (0.92, 0.94, 0.95, 1.0)
            n.inputs["Roughness"].default_value = 0.05
            n.inputs["Metallic"].default_value = 0.6
            if "Emission Color" in n.inputs:
                n.inputs["Emission Color"].default_value = (0.85, 0.88, 0.90, 1.0)
                n.inputs["Emission Strength"].default_value = 0.5
    add_box("mirror_glass", (3.82, 0.10, 1.15), (0.04, 1.2, 1.6), mirror_mat)
    add_box("mirror_frame_top", (3.83, 0.10, 1.98), (0.08, 1.34, 0.08), wall)
    add_box("mirror_frame_bot", (3.83, 0.10, 0.32), (0.08, 1.34, 0.08), wall)
    add_box("mirror_frame_l", (3.83, -0.56, 1.15), (0.08, 0.08, 1.74), wall)
    add_box("mirror_frame_r", (3.83, 0.76, 1.15), (0.08, 0.08, 1.74), wall)
    # 许宁坐的小木凳（程序化，凳面 z≈0.44 → abs -0.16）
    add_box("stool_seat", (1.90, 0.10, -0.16), (0.34, 0.34, 0.06), wall)
    for sx in (-0.13, 0.13):
        for sy in (-0.13, 0.13):
            add_box(f"stool_leg_{sx}_{sy}", (1.90 + sx, 0.10 + sy, -0.40),
                    (0.05, 0.05, 0.44), wall)


def add_comb(girl_arm):
    """妈妈手中的梳子：深色小条，放在许宁头顶后方，给 H3 梳头动作锚点。"""
    girl_head = head_world(girl_arm)
    bpy.ops.mesh.primitive_cube_add(size=0.02)
    comb = bpy.context.active_object
    comb.name = "comb_prop"
    comb.dimensions = (0.05, 0.16, 0.025)
    comb.location = (girl_head.x + 0.06, girl_head.y - 0.02, girl_head.z + 0.13)
    comb.rotation_euler = (0, math.radians(20), math.radians(15))
    mat = bpy.data.materials.new("comb_wood04")
    mat.use_nodes = True
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (0.35, 0.18, 0.08, 1.0)
            n.inputs["Roughness"].default_value = 0.6
    comb.data.materials.append(mat)


def add_lighting():
    world = bpy.data.worlds.new("previz_world04")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.42, 0.42, 0.46, 1.0)
            n.inputs[1].default_value = 0.5
    bpy.context.scene.world = world
    # 晨光：从 +y 窗外打入（暖）
    bpy.ops.object.light_add(type="AREA", location=(1.2, 4.5, 1.9))
    key = bpy.context.active_object
    key.data.energy = 1500
    key.data.size = 3.0
    key.data.color = (1.0, 0.9, 0.75)
    key.rotation_euler = (math.radians(-70), 0, 0)
    # 补光：面向人物脸部（-x 侧来光）
    bpy.ops.object.light_add(type="AREA", location=(-1.0, -1.5, 1.8))
    fill = bpy.context.active_object
    fill.data.energy = 500
    fill.data.size = 2.5
    fill.rotation_euler = (math.radians(60), 0, math.radians(-35))


def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    build_room()
    add_lighting()

    # 家具（床+梳妆台+床头柜+模型自带凳），+1.2 x 平移
    pre_existing = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, "E03", "tex_mesh_scaled.glb"))
    for o in [o for o in bpy.context.scene.objects if o not in pre_existing]:
        o.location.x += E03_SHIFT_X
    bpy.context.view_layer.update()
    print(f"[previs04] env meshes={len(mesh_objects())}", flush=True)

    # 角色
    c01_rot = face_rot_z(C01_POS, (C01_POS[0] + 1, C01_POS[1]))  # 面向 +x 镜子
    c09_rot = face_rot_z(C09_POS, (C01_POS[0] + 0.05, C01_POS[1] + 0.15))
    print(f"[previs04] C01 rot_z={c01_rot:.1f}  C09 rot_z={c09_rot:.1f}", flush=True)
    girl = place_character("C01", "tex_mesh_v04_rigged.glb", C01_POS, c01_rot, POSE_C01)
    mom = place_character("C09", "tex_mesh_v04_rigged_scaled16.glb", C09_POS, c09_rot, POSE_C09)
    add_comb(girl)

    h1 = head_world(girl)
    h9 = head_world(mom)
    tgt_mid = h1 * 0.58 + h9 * 0.42
    print(f"[previs04] head C01=({h1.x:.2f},{h1.y:.2f},{h1.z:.2f}) "
          f"C09=({h9.x:.2f},{h9.y:.2f},{h9.z:.2f}) "
          f"tgt=({tgt_mid.x:.2f},{tgt_mid.y:.2f},{tgt_mid.z:.2f})", flush=True)
    cam_start_tgt = Vector((tgt_mid.x, tgt_mid.y, tgt_mid.z))
    cam_end_tgt = Vector((tgt_mid.x + 0.05, tgt_mid.y, tgt_mid.z - 0.03))

    apply_matte([o for o in mesh_objects()
                 if "window_glass" not in o.name and "mirror_glass" not in o.name
                 and o.name != "comb_prop"])

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

    cam_data = bpy.data.cameras.new("previs_cam04")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.data.objects.new("previs_cam04", cam_data)
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
            print(f"[previs04] frame {f}/{N_FRAMES}", flush=True)

    with open(os.path.join(OUT_DIR, "previs04_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS04_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
