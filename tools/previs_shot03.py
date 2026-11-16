# -*- coding: utf-8 -*-
"""白模预演：县医院病房 · shot03「许宁踮脚捧住姥姥的手」双人近景（Blender 相机调度）。

开篇重场：姥姥住院，许宁刚比床沿高出一截，踮脚把两只手伸进床栏捧住姥姥的手。
本镜为低调度静态瞬间（动态交给 H3），只有相机从女孩肩后缓慢推近。

E02 实测（probe_e02）：地面 z=-0.50，床垫面 z≈+0.50，床头/枕头在 +x，
床头柜 +x 1.3~1.8，IV 架 +x 1.8~2.3。床沿约 1.0m，C01 身高 1.1m——
「刚比床沿高出一截」与原文吻合，直接采用。

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot03.py   (5 帧构图测试)
  blender.exe --background --python tools/previs_shot03.py                          (192 帧全量)
"""
import json
import math
import os

import bpy
from mathutils import Vector, Matrix, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames03")

FPS = 24
DURATION_S = 8
N_FRAMES = FPS * DURATION_S
RES_X, RES_Y = 1280, 720

FLOOR_Z = -0.50
MATTRESS_Z = 0.50

# rigged GLB 骨架原点在髋部：C08(1.6m) 髋高 0.80，C01(1.1m) 髋高 0.55
HIP_C08, HIP_C01 = 0.80, 0.55

# ---- staging ----
# 姥姥平躺：头朝 -x（模型枕头端在 x≈-2.4，前期探测确认；+x 是床尾/床头柜侧），
# 髋部在床垫上方约 0.12m，头枕在枕头位置（x≈-1.85）
C08_HIP_POS = (-1.35, 0.05, MATTRESS_Z + 0.12)
# 许宁站在床沿近侧（-y），朝向姥姥伸出的手，踮脚
C01_POS = (-0.10, -1.05, FLOOR_Z + HIP_C01 + 0.05)

# 平躺姿态：local Y(面朝) -> 世界 +Z(仰卧)，local Z(头顶) -> 世界 -X(头朝枕头端)
# local X -> 世界 -Y。矩阵行 [[0,0,-1],[-1,0,0],[0,1,0]]，det=+1
LIE_MATRIX = Matrix(((0, 0, -1), (-1, 0, 0), (0, 1, 0)))

# 姥姥：头微倾向女孩一侧(-y)并略抬，右手伸向床沿
POSE_C08 = [
    ("mixamorig:Head",       (1, 0, 0), 22),   # 脸从朝上转向女孩方向(-y)
    ("mixamorig:Neck",       (1, 0, 0), 12),
    ("mixamorig:RightArm",   (0, 0, 1), -28),  # 右臂沿床面向外抬
    ("mixamorig:RightForeArm", (0, 1, 0), 30),
    ("mixamorig:RightHand",  (0, 1, 0), 15),
    ("mixamorig:LeftArm",    (0, 0, 1), 15),   # 左臂贴近毯面
    ("mixamorig:LeftForeArm", (0, 1, 0), 12),
]
# 许宁：身体前倾、仰头，双臂向前上方伸过床栏
POSE_C01 = [
    ("mixamorig:Spine",      "lean", 12),
    ("mixamorig:Spine1",     "lean", 8),
    ("mixamorig:Neck",       "lean", -14),  # 抬头看姥姥
    ("mixamorig:Head",       "lean", -10),
    ("mixamorig:RightArm",   (0, 0, 1), -62),   # 双臂向前上方伸
    ("mixamorig:RightForeArm", (0, 1, 0), 18),
    ("mixamorig:LeftArm",    (0, 0, 1), -55),
    ("mixamorig:LeftForeArm", (0, 1, 0), 12),
]

# 机位：床头端左前上方，视线越过床尾护栏，姥姥仰起的脸为落点，许宁在右侧
CAM_START_POS = (-2.90, -2.30, 1.95)
CAM_END_POS = (-2.25, -1.75, 1.68)
CAM_LENS = 32


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


def make_matte():
    mat = bpy.data.materials.new("previz_matte03")
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


def place_character(cid, pos, rot_z, pose, lie=False):
    path = os.path.join(MODELS, cid, "tex_mesh_v04_rigged.glb")
    import_glb(path)
    for o in [o for o in bpy.context.scene.objects
              if o.type == "MESH" and "棱角球" in o.name]:
        bpy.data.objects.remove(o, do_unlink=True)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    arm_obj = arms[-1]
    arm_obj.location = pos
    if lie:
        arm_obj.rotation_mode = "QUATERNION"
        arm_obj.rotation_quaternion = (
            Matrix.Rotation(math.radians(rot_z), 3, "Z") @ LIE_MATRIX
        ).to_quaternion()
    else:
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
    """病房外壳：地板、三面墙、带窗后墙、天花板、暖气片块、立柜块。"""
    wall = make_matte()
    # 地板 / 天花板
    add_box("floor", (0, 0, FLOOR_Z - 0.05), (9.0, 8.0, 0.1), wall)
    add_box("ceiling", (0, 0, 2.35), (9.0, 8.0, 0.1), wall)
    # 后墙 y=+2.4，窗户 x∈[-1.3,1.3]，窗台 z=0.55，窗顶 z=2.05
    wy = 2.4
    add_box("wall_back_left", (-2.85, wy, 0.9), (3.3, 0.12, 2.9), wall)
    add_box("wall_back_right", (2.85, wy, 0.9), (3.3, 0.12, 2.9), wall)
    add_box("wall_back_sill", (0, wy, -0.225), (2.4, 0.12, 0.55), wall)
    add_box("wall_back_top", (0, wy, 2.2), (2.4, 0.12, 0.5), wall)
    # 侧墙
    add_box("wall_left", (-3.6, 0, 0.9), (0.12, 4.9, 2.9), wall)
    add_box("wall_right", (3.6, 0, 0.9), (0.12, 4.9, 2.9), wall)
    # 窗框 + 玻璃（自发光亮面，给 H3 一个强光源提示）
    glass_mat = bpy.data.materials.new("window_glass03")
    glass_mat.use_nodes = True
    for n in glass_mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
            n.inputs["Roughness"].default_value = 0.1
            if "Emission Color" in n.inputs:
                n.inputs["Emission Color"].default_value = (1.0, 1.0, 0.97, 1.0)
                n.inputs["Emission Strength"].default_value = 2.2
    add_box("window_glass", (0, wy, 1.30), (2.5, 0.04, 1.5), glass_mat)
    # 窗棂十字
    add_box("window_mullion_v", (0, wy - 0.03, 1.30), (0.06, 0.05, 1.5), wall)
    add_box("window_mullion_h", (0, wy - 0.03, 1.30), (2.5, 0.05, 0.06), wall)
    # 暖气片（窗下）
    add_box("radiator", (0, wy - 0.25, 0.0), (1.8, 0.18, 0.6), wall)
    # 立柜（左墙）
    add_box("wardrobe", (-3.3, 0.8, 0.55), (0.55, 1.0, 2.1), wall)
    # 小木凳（右前，画面层次）
    add_box("stool", (2.2, -1.3, FLOOR_Z + 0.22), (0.36, 0.36, 0.44), wall)


def add_lighting():
    world = bpy.data.worlds.new("previz_world03")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.35, 0.37, 0.42, 1.0)
            n.inputs[1].default_value = 0.45
    bpy.context.scene.world = world
    # 窗户外强日光（病房白亮基调）
    bpy.ops.object.light_add(type="AREA", location=(0, 4.2, 1.9))
    key = bpy.context.active_object
    key.data.energy = 1600
    key.data.size = 3.0
    # 区域灯沿局部 -Z 发射：-70° 使其朝 -y 下方打入病房
    key.rotation_euler = (math.radians(-70), 0, 0)
    # 室内补光（避免背光脸黑）
    bpy.ops.object.light_add(type="AREA", location=(-1.5, -1.5, 2.1))
    fill = bpy.context.active_object
    fill.data.energy = 600
    fill.data.size = 2.5
    fill.rotation_euler = (math.radians(35), 0, math.radians(-25))


def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    build_room()
    add_lighting()

    # 病房家具（床+床头柜+IV架），已烘焙 2.5 倍缩放
    pre_existing = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, "E02", "tex_mesh_scaled.glb"))
    bpy.context.view_layer.update()
    # 剔除重建失真的 IV 架：单网格，按区域删顶点（x>1.65 且 z>0.9 的锥状高件）
    import bmesh
    for o in [o for o in bpy.context.scene.objects if o not in pre_existing and o.type == "MESH"]:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        doomed = [v for v in bm.verts
                  if (o.matrix_world @ v.co).x > 1.80 and (o.matrix_world @ v.co).z > 0.60]
        if doomed:
            bmesh.ops.delete(bm, geom=doomed, context="VERTS")
            bm.to_mesh(o.data)
            print(f"[previs03] removed {len(doomed)} IV-stand verts from {o.name}", flush=True)
        bm.free()
    env_meshes = mesh_objects()
    print(f"[previs03] env meshes={len(env_meshes)}", flush=True)

    # 角色：姥姥仰卧，头朝 +x；许宁站近侧面向姥姥
    c08_rot = 0.0  # 平躺由 LIE_MATRIX 决定，rot_z 为附加水平角
    c01_rot = face_rot_z(C01_POS, (-0.95, -0.35))  # 面向姥姥伸出的手
    print(f"[previs03] C01 rot_z={c01_rot:.1f}", flush=True)
    granny = place_character("C08", C08_HIP_POS, c08_rot, POSE_C08, lie=True)
    girl = place_character("C01", C01_POS, c01_rot, POSE_C01)

    h8 = head_world(granny)
    h1 = head_world(girl)
    tgt_mid = h8 * 0.45 + h1 * 0.55
    print(f"[previs03] head C08=({h8.x:.2f},{h8.y:.2f},{h8.z:.2f}) "
          f"C01=({h1.x:.2f},{h1.y:.2f},{h1.z:.2f}) "
          f"tgt=({tgt_mid.x:.2f},{tgt_mid.y:.2f},{tgt_mid.z:.2f})", flush=True)
    cam_start_tgt = Vector((tgt_mid.x, tgt_mid.y, tgt_mid.z))
    cam_end_tgt = Vector((tgt_mid.x + 0.06, tgt_mid.y, tgt_mid.z - 0.04))

    apply_matte([o for o in mesh_objects() if "window_glass" not in o.name])

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

    cam_data = bpy.data.cameras.new("previs_cam03")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.data.objects.new("previs_cam03", cam_data)
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
            print(f"[previs03] frame {f}/{N_FRAMES}", flush=True)

    with open(os.path.join(OUT_DIR, "previs03_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS03_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
