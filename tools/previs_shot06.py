# -*- coding: utf-8 -*-
"""白模预演：火车站 shot06「站台送别」（Blender 相机调度 + 走动动画）。

剧本（四 L193-201）：许宁（大学）送妈妈进站。隔着闸机挥了两次手。
妈妈转身后，她仍站在原处，直到那个熟悉的背影混进拖着行李的人群。

本镜为低调度走位镜头：
- 许宁 C05 站定目送，抬手挥别（手动姿态关键帧）
- 妈妈 C10：面向许宁 → 沿站台走向车厢门（Walk_Loop）→ 停步半转身（Idle）→ 再走几步混入人群
- 镜头缓推，视点始终贴着许宁一侧

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot06.py   (5 帧构图测试)
  blender.exe --background --python tools/previs_shot06.py                          (192 帧全量)
"""
import json
import math
import os

import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames06")

FPS = 24
DURATION_S = 8
N_FRAMES = FPS * DURATION_S
RES_X, RES_Y = 1280, 720

PLATFORM_Z = 0.0          # 站台面
ARM_Z = 0.78              # 绑骨骨架原点离地高（脚底在 origin-0.82 处，实测校准）

# E04 列车网格实测原始跨度 x24.5 y101.8 z30.3，轴向压回真实比例
TRAIN_SCALE = (3.0 / 24.5, 26.0 / 101.8, 4.2 / 30.3)
TRAIN_LOC = (3.2, 0.0, 1.45)   # 车体中心：侧面朝站台，轮底沉入站台面下

# ---- 走位时间轴 ----
F_START_IDLE = 1            # 妈妈面向许宁
F_WALK1 = 11                # 起步沿 +y 走
F_WALK1_END = 110
F_TURN = 111                # 停步、半转身面向镜头方向
F_TURN_END = 150
F_WALK2 = 161               # 转身继续走向人群
MOM_START = Vector((-1.15, -1.4, ARM_Z))
MOM_Y_WALK1_END = 5.0
MOM_Y_FINAL = 6.8
CROWD_CENTER = (1.7, 8.2)   # 车厢门口聚集人群

XU_POS = (-2.55, -2.6, ARM_Z)

CAM_START_POS = (-2.9, -6.9, 1.75)
CAM_END_POS = (-2.3, -4.7, 1.5)
CAM_LENS = 35


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def make_matte(name="previz_matte06", shade=0.78):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (shade, shade, shade, 1.0)
            n.inputs["Roughness"].default_value = 0.95
            n.inputs["Metallic"].default_value = 0.0
    return mat


def add_box(name, loc, dims, mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    box = bpy.context.active_object
    box.name = name
    box.location = loc
    box.dimensions = dims
    if mat is not None:
        box.data.materials.append(mat)
    return box


def build_station():
    """程序化站台 + 雨棚 + 站房墙；E04 网格作列车。"""
    wall = make_matte()
    # 站台地面
    add_box("platform", (-1.2, 0, PLATFORM_Z - 0.2), (4.8, 32.0, 0.4), wall)
    # 安全白线
    line_mat = make_matte("white_line", 0.92)
    add_box("safety_line", (0.75, 0, PLATFORM_Z + 0.005), (0.12, 32.0, 0.012), line_mat)
    # 雨棚柱 + 顶棚
    for i, y in enumerate(range(-15, 16, 6)):
        add_box(f"pillar_{i}", (-3.0, y, 1.9), (0.14, 0.14, 3.8), wall)
    add_box("canopy", (-1.1, 0, 4.0), (5.0, 32.0, 0.12), wall)
    # 站房墙面（背景）
    add_box("station_wall", (-3.75, 0, 2.2), (0.25, 32.0, 4.4), wall)

    # E04 列车
    pre = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, "E04", "tex_mesh.glb"))
    for o in [o for o in bpy.context.scene.objects if o not in pre]:
        if o.type == "MESH":
            o.scale = TRAIN_SCALE
            o.location = TRAIN_LOC
    bpy.context.view_layer.update()

    # 人群（胶囊体）+ 行李，车厢门口
    crowd_mat = make_matte("crowd_matte", 0.55)
    crowd = [(-0.6, 7.4), (0.2, 8.0), (1.0, 7.0), (1.9, 8.6), (2.6, 7.8), (0.6, 9.0)]
    for i, (cx, cy) in enumerate(crowd):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.19, location=(cx, cy, PLATFORM_Z + 1.5))
        s = bpy.context.active_object
        s.name = f"crowd_{i}"
        s.scale = (1.0, 1.0, 3.2)
        bpy.ops.object.transform_apply(scale=True)
        s.data.materials.append(crowd_mat)
        if i % 2 == 0:
            add_box(f"lug_{i}", (cx + 0.35, cy - 0.2, PLATFORM_Z + 0.25),
                    (0.45, 0.28, 0.5), crowd_mat)


def add_lighting():
    world = bpy.data.worlds.new("previz_world06")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.42, 0.44, 0.50, 1.0)
            n.inputs[1].default_value = 0.55
    bpy.context.scene.world = world
    # 清晨偏冷的顶光
    bpy.ops.object.light_add(type="AREA", location=(2.0, -2.0, 9.0))
    key = bpy.context.active_object
    key.data.energy = 1800
    key.data.size = 7.0
    key.data.color = (0.88, 0.92, 1.0)
    key.rotation_euler = (0, 0, 0)
    # 正面柔补
    bpy.ops.object.light_add(type="AREA", location=(-3.0, -5.0, 2.2))
    fill = bpy.context.active_object
    fill.data.energy = 700
    fill.data.size = 4.0
    fill.data.color = (0.95, 0.95, 1.0)
    fill.rotation_euler = (math.radians(65), 0, math.radians(-20))


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


def key_pb(arm_obj, bone_name, world_axis, angle_deg, f1, f2=None, v2=None):
    """在 f1（可选 f2）关键帧写一个姿态骨旋转；f2 时角度为 v2。"""
    pb = arm_obj.pose.bones.get(bone_name)
    if pb is None:
        return
    rotate_pose_bone_world(arm_obj, bone_name, world_axis, angle_deg)
    pb.keyframe_insert("rotation_quaternion", frame=f1)
    if f2 is not None:
        rotate_pose_bone_world(arm_obj, bone_name, world_axis, v2)
        pb.keyframe_insert("rotation_quaternion", frame=f2)


def import_character(cid, glb, pos, rot_z):
    pre = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, cid, glb))
    new = [o for o in bpy.context.scene.objects if o not in pre]
    for o in new:
        if o.type == "MESH" and "棱角球" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE" and o in new] or \
           [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    arm_obj = arms[-1]
    arm_obj.rotation_mode = "XYZ"
    arm_obj.location = pos
    arm_obj.rotation_euler = (0, 0, math.radians(rot_z))
    bpy.context.view_layer.update()
    return arm_obj


def setup_xu(arm_obj):
    """许宁：手臂放下（f1）→ 抬右手挥别（f55-70 起保持）。面向 +y（妈妈方向）rot=180。
    C05 是 T-pose 骨架：手臂放下 = 绕 (0,1,0) ∓90（右臂 -、左臂 +），抬起同轴反向。"""
    for bone, ang in (("mixamorig:RightArm", -90), ("mixamorig:LeftArm", 90)):
        rotate_pose_bone_world(arm_obj, bone, (0, 1, 0), ang)
        arm_obj.pose.bones[bone].keyframe_insert("rotation_quaternion", frame=1)
    for bone, ang in (("mixamorig:RightForeArm", -8), ("mixamorig:LeftForeArm", 8)):
        rotate_pose_bone_world(arm_obj, bone, (0, 1, 0), ang)
        arm_obj.pose.bones[bone].keyframe_insert("rotation_quaternion", frame=1)
    # 右手臂抬起挥别：f55 开始抬，f70 到位保持（右臂 +90 = 上，探针实测）
    key_pb(arm_obj, "mixamorig:RightArm", (0, 1, 0), -90, 55, 70, 90)
    key_pb(arm_obj, "mixamorig:RightForeArm", (0, 1, 0), -8, 55, 70, -22)
    # 头部微仰目送
    rotate_pose_bone_world(arm_obj, "mixamorig:Neck", (1, 0, 0), -6)
    arm_obj.pose.bones["mixamorig:Neck"].keyframe_insert("rotation_quaternion", frame=1)


def find_actions():
    """Lux3D 重定向 glb 动作名是 animation_1/2；按提交顺序 Walk 在前 Idle 在后，
    用帧数辅助判断（walk 周期短）。"""
    acts = {}
    walk = idle = None
    for ac in bpy.data.actions:
        if ac.name.lower() == "animation_1":
            walk = ac
        elif ac.name.lower() == "animation_2":
            idle = ac
    if walk and idle and (idle.frame_range[1] - idle.frame_range[0]) < \
            (walk.frame_range[1] - walk.frame_range[0]):
        walk, idle = idle, walk
    if walk:
        acts["walk"] = walk
    if idle:
        acts["idle"] = idle
    return acts


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def mom_state(f):
    """返回 (y, rot_z, action_key)。rot_z=0 面向 -y（许宁/镜头侧），180 面向 +y。"""
    if f < F_WALK1:
        return MOM_START.y, 0.0, "idle"
    if f <= F_WALK1_END:
        t = (f - F_WALK1) / (F_WALK1_END - F_WALK1)
        y = MOM_START.y + (MOM_Y_WALK1_END - MOM_START.y) * t
        return y, 180.0, "walk"
    if f <= F_TURN_END:
        t = ease((f - F_TURN) / (F_TURN_END - F_TURN))
        # 半转身面向镜头/许宁一侧（335°），停步
        return MOM_Y_WALK1_END, 180.0 + 155.0 * t, "idle"
    if f < F_WALK2:
        t = ease((f - F_TURN_END) / (F_WALK2 - F_TURN_END))
        return MOM_Y_WALK1_END, 335.0 - 155.0 * t, "idle"
    t = (f - F_WALK2) / (N_FRAMES - F_WALK2)
    y = MOM_Y_WALK1_END + (MOM_Y_FINAL - MOM_Y_WALK1_END) * t
    return y, 180.0, "walk"


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    build_station()
    add_lighting()

    # 许宁（无动画，手动姿态）
    xu = import_character("C05", "tex_mesh_v08_rigged.glb", XU_POS, 180.0)
    setup_xu(xu)

    # 妈妈（带 Walk/Idle 动画）
    mom = import_character("C10", "tex_mesh_v08_animated.glb", MOM_START, 0.0)
    acts = find_actions()
    print(f"[previs06] actions found: {list(acts.keys())}", flush=True)

    # 妈妈的行李袋，跟随妈妈平移
    bag_mat = make_matte("bag_matte", 0.4)
    bag = add_box("mom_bag", (0, 0, 0), (0.34, 0.16, 0.42), bag_mat)

    apply_matte = make_matte()
    for o in mesh_objects():
        if o.name in ("mom_bag",) or o.name.startswith("crowd_") or o.name.startswith("lug_"):
            continue
        if o.type == "MESH" and len(o.data.materials) == 0:
            o.data.materials.append(apply_matte)
    for o in mesh_objects():
        if o.name.startswith("crowd_"):
            continue
        if "white_line" not in o.name and not o.name.startswith("lug_"):
            o.data.materials.clear()
            o.data.materials.append(apply_matte)

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

    cam_data = bpy.data.cameras.new("previs_cam06")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.data.objects.new("previs_cam06", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    xu_head = None
    pb = xu.pose.bones.get("mixamorig:Head")
    if pb is not None:
        xu_head = xu.matrix_world @ pb.head

    sp = Vector(CAM_START_POS)
    ep = Vector(CAM_END_POS)
    last_key = None

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    frames_iter = [1, 32, 64, 96, 128, 160, 192] if test_mode else range(1, N_FRAMES + 1)
    for f in frames_iter:
        t = ease((f - 1) / (N_FRAMES - 1))
        # 妈妈走位
        y, rot, key = mom_state(f)
        mom.location.y = y
        mom.rotation_euler.z = math.radians(rot)
        if key in acts:
            if last_key != key:
                mom.animation_data.action = acts[key]
                last_key = key
        scene.frame_set(f)
        # 行李袋挂在妈妈身侧（世界坐标随行）
        bag.location = (mom.location.x - 0.32, mom.location.y + 0.05, PLATFORM_Z + 0.28)
        # 相机
        cam.location = sp.lerp(ep, t)
        mom_head = mom.matrix_world @ mom.pose.bones["mixamorig:Head"].head
        if f <= F_TURN_END:
            tgt = mom_head * 0.62 + xu_head * 0.38
        else:
            crowd_pt = Vector((CROWD_CENTER[0], CROWD_CENTER[1], 1.4))
            tgt = (mom_head * 0.5 + crowd_pt * 0.5) * 0.7 + xu_head * 0.3
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs06] frame {f}/{N_FRAMES} mom y={y:.2f} rot={rot:.0f} key={key}", flush=True)

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS}
    with open(os.path.join(OUT_DIR, "previs06_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS06_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
