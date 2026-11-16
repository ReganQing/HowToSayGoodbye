# -*- coding: utf-8 -*-
"""白模预演：shot18「楼下晨光·婴儿车」（剧本五 L305-311，方案 §4）。

场景 E13 楼下晨景：收摊的早点摊在画面左、低围墙与居民楼在右后方形成巷子纵深，
婴儿车停在画面中央，许宁 C06 站在车后偏左（探针站位 (-0.35, 0.75) / yaw 12°）。
C20 婴儿按方案 §5 是襁褓道具，不绑骨、不进 Lux3D，用躺姿白模 + 五官小点表示小脸。

变化三态（全部渐变，无硬切）：
  前态   推着婴儿车沿窄巷缓缓停下（车 + 人 + 轮子同步，f1-44）
  过程A  松开左手弯腰俯身，手渐移向孩子嘴角、轻擦（f45-96）
  过程B  指尖在那张柔软小脸上停住（f97-124）；缓缓抬头，想起姥姥停在头顶的手（f125-140）
  过程C  女儿小手抓住她的手指往嘴里送（f141-162）；笑着抽回（f163-176）
  后态   俯身亲一下孩子额头，再缓缓直起身（f177-192），镜头微推

关键设计（HANDOFF §5.19）：核心动作「擦嘴角 → 停小脸 → 被抓 → 抽回」不是靠 prompt，
而是靠白模里一条完整、可辨识的左手运动链。因为弯腰时 Spine 旋转会传导到手臂，
静态手 K 角度会失准，这里改用**每帧坐标下降求解**：以 HAND_TRACK 的世界坐标为
目标、以上一帧解为 seed，迭代求 LeftArm/LeftForeArm 角度，让手始终精确贴着目标轨迹。
角度初值来自 tmp_qc/probe_xu_arm18_poses.py 的四姿态实测（写入 shot18_arm_poses.json）。

已知坑（HANDOFF §5）已规避：
  §5.14 按 clip 序号名称取 action、脚高用站姿 Idle 测
  §5.15 add_box 的 dimensions 本质是 scale，驱动道具保存初始 scale
  §5.16 build_room() 末尾补 view_layer.update()
  §5.17 避免整块实心板正对相机（棚布做薄斜板、围墙沿纵深、椅背类不出现）
  §5.19 关键道具必须有完整物理链；道具不凭空出现/消失/瞬移

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot18.py
  set PREVIS_RANGE=1-64 && blender.exe --background --python tools/previs_shot18.py
  blender.exe --background --python tools/previs_shot18.py
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import previs_shot14 as p14  # noqa: E402  复用成熟的 GLB/NLA/骨骼工具

ROOT = os.path.dirname(TOOLS)
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames18")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720
CAM_LENS = 30
CAM_START = (0.28, -2.30, 1.42)
CAM_END = (0.26, -2.10, 1.38)
AIM = Vector((0.10, 1.05, 0.98))

# 站位：与 tmp_qc/probe_xu_arm18*.py 完全一致，手 K 初值才有效
XU_XY = (-0.35, 0.75)
XU_YAW = math.radians(12)
PUSH_START = 0.22          # f1 时车/人比停止位置远 0.22m（沿 +y），f44 渐停到 0

CAR_X, CAR_Y = 0.15, 0.60  # 婴儿车中心（停止时）
BABY_HEAD = (0.12, 0.61, 0.855)   # 躺姿头中心，球半径 0.095 → 脸面 z≈0.95
BABY_HEAD_R = 0.095

# 左手目标轨迹（世界坐标，停止位置口径）。端点来自四姿态实测：
#   HANDLE_V2 armX=35 armY=40 foreY=60 -> (-0.047,1.015,0.966) 手臂向前平伸
#   CHEEK   armX=-40 armY=25  foreY=20  -> (0.123,0.612,0.955)
#   MOUTH   armX=-45 armY=40  foreY=0   -> (0.097,0.583,0.946)
#   RETREAT armX=0   armY=105 foreY=-40 -> (-0.158,0.847,0.848)
# v1 的 HANDLE (0.039,0.976,0.986) 会让手臂横过胸前，f001 目检不自然，改用 HANDLE_V2。
HAND_TRACK = [
    (1,   (-0.05, 1.00, 0.96)),     # 扶车把（向前平伸）
    (44,  (-0.05, 1.00, 0.96)),
    (72,  (0.105, 0.600, 0.940)),   # 松手、弯腰、手移向嘴角
    (96,  (0.097, 0.583, 0.946)),   # 轻擦嘴角
    (108, (0.123, 0.612, 0.955)),   # 指尖停在小脸上
    (140, (0.123, 0.612, 0.955)),   # 抬头想起姥姥的手，指不离脸
    (158, (0.097, 0.583, 0.946)),   # 被女儿带向小嘴
    (176, (-0.158, 0.847, 0.848)),  # 笑着抽回手
    (186, (-0.158, 0.847, 0.848)),  # 俯身亲额头时手在身侧
    (192, (-0.100, 0.900, 0.860)),  # 直起身，手自然回身侧略前
]

BABY_HAND_HOME = (0.00, 0.68, 0.845)
BABY_HAND_GRAB = (0.075, 0.625, 0.925)

BONES_MANUAL = ("mixamorig:Head", "mixamorig:Neck",
                "mixamorig:Spine", "mixamorig:Spine1",
                "mixamorig:RightArm", "mixamorig:RightForeArm", "mixamorig:RightHand",
                "mixamorig:LeftArm", "mixamorig:LeftForeArm", "mixamorig:LeftHand")


def mat(key, shade, emission=None):
    return p14.mat("s18_" + key, shade, emission)


def add_ball(name, loc, radius, m=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc,
                                         segments=16, ring_count=10)
    o = bpy.context.active_object
    o.name = name
    if m is not None:
        o.data.materials.append(m)
    return o


def build_room():
    """E13 楼下晨景：左侧收摊早点摊 + 右侧低围墙纵深 + 后方居民楼窗。"""
    ground = mat("ground", 0.55)
    wall = mat("wall", 0.66)
    p14.add_box("ground", (0, 1.0, -0.05), (9.0, 13.0, 0.10), ground)

    # --- 左侧早点摊（参考 E13_v01：白布棚、木桌、暖壶、盖锅、碗、保温箱、叠凳）---
    tx, ty = -1.55, 1.85
    p14.add_box("stall_top", (tx, ty, 0.78), (1.50, 0.76, 0.055), mat("stall_wood", 0.50))
    # v2：不做整块深色桌裙（§5.17 会被读成「一块板子长出来」），改两根细横杆保持通透
    for z in (0.30, 0.62):
        p14.add_box(f"stall_rail_{z}", (tx, ty + 0.36, z), (1.46, 0.025, 0.028),
                    mat("stall_rail", 0.58))
    for dx in (-0.68, 0.68):
        for dy in (-0.34, 0.34):
            p14.add_box(f"stall_leg_{dx}_{dy}", (tx + dx, ty + dy, 0.39),
                        (0.045, 0.045, 0.78), mat("stall_leg", 0.42))
    # 棚布：薄斜板，不是正对相机的实心大板（§5.17）
    canopy = p14.add_box("canopy", (tx, ty, 1.98), (1.62, 0.86, 0.022),
                         mat("canopy", 0.90))
    canopy.rotation_euler.x = math.radians(7)
    for dx in (-0.72, 0.72):
        for dy in (-0.36, 0.36):
            p14.add_box(f"canopy_pole_{dx}_{dy}", (tx + dx, ty + dy, 1.38),
                        (0.035, 0.035, 1.20), mat("stall_leg", 0.42))
    p14.add_cyl("thermos", (tx - 0.42, ty - 0.05, 0.925), 0.060, 0.28,
                mat("thermos", 0.78))
    p14.add_cyl("pot", (tx + 0.30, ty + 0.02, 0.865), 0.135, 0.115,
                mat("pot", 0.34))
    p14.add_cyl("pot_lid", (tx + 0.30, ty + 0.02, 0.930), 0.145, 0.018,
                mat("pot_lid", 0.40))
    add_ball("pot_knob", (tx + 0.30, ty + 0.02, 0.948), 0.022, mat("pot", 0.34))
    for i, bx in enumerate((tx - 0.12, tx + 0.06)):
        p14.add_cyl(f"bowl_{i}", (bx, ty - 0.18, 0.842), 0.090, 0.055,
                    mat("bowl", 0.86))
    for i, bx in enumerate((tx - 0.60, tx - 0.20)):
        p14.add_box(f"cooler_{i}", (bx, ty - 0.62, 0.22), (0.36, 0.32, 0.44),
                    mat("cooler", 0.62))
    for i in range(5):
        p14.add_box(f"stool_stack_{i}", (tx + 0.58, ty - 0.52, 0.10 + i * 0.035),
                    (0.30, 0.28, 0.028), mat("stool", 0.58))

    # --- 右侧低围墙沿巷子纵深（斜向，不正对相机）+ 后墙居民楼 ---
    p14.add_box("low_wall", (1.85, 2.30, 0.58), (0.16, 7.0, 1.16), wall)
    p14.add_box("wall_cap", (1.85, 2.30, 1.18), (0.22, 7.0, 0.05),
                mat("wall_cap", 0.50))
    p14.add_box("far_building", (0.0, 5.60, 1.90), (8.0, 0.20, 3.80), wall)
    frame = mat("window", 0.44)
    for wx in (-2.1, -0.7, 0.8, 2.2):
        for wz in (1.35, 2.45):
            p14.add_box(f"far_win_{wx}_{wz}", (wx, 5.47, wz), (0.72, 0.03, 0.62), frame)
    p14.add_box("daylight_sky", (0.0, 5.80, 4.10), (9.0, 0.10, 3.0),
                mat("sky", 0.86, emission=(0.55, 0.62, 0.72, 1.0)))
    # §5.16：强制刷新依赖图，最后创建的几何体 dimensions 才会生效
    bpy.context.view_layer.update()


def build_car():
    """婴儿车 + 躺姿襁褓 + 婴儿小手；返回 (parts, wheels, baby_hand)。

    parts 是 (obj, base_y)，每帧按推车位移 off 整体平移，保证车、人、婴儿不脱节。
    """
    parts, wheels = [], []

    def reg(o):
        parts.append((o, o.location.y))
        return o

    cx, cy = CAR_X, CAR_Y
    frame = mat("car_frame", 0.52)
    basket = mat("basket", 0.80)
    swaddle = mat("swaddle", 0.92)
    ink = mat("face_ink", 0.12)

    # 四个轮子：圆柱初始轴沿 z，绕 Y 转 90° 后轴沿 x，滚动再叠加绕 X 的 roll
    for dx in (-0.30, 0.30):
        for dy in (-0.27, 0.27):
            w = p14.add_cyl(f"wheel_{dx}_{dy}", (cx + dx, cy + dy, 0.095),
                            0.095, 0.045, mat("wheel", 0.36),
                            rot=(0, math.radians(90), 0))
            reg(w)
            wheels.append(w)
    reg(p14.add_box("car_chassis", (cx, cy, 0.30), (0.64, 0.60, 0.045), frame))
    for dx in (-0.28, 0.28):
        for dy in (-0.24, 0.24):
            reg(p14.add_box(f"car_strut_{dx}_{dy}", (cx + dx, cy + dy, 0.53),
                            (0.035, 0.035, 0.46), frame))
    # 睡篮：底板 + 四壁（不封顶，婴儿脸完全可见）
    reg(p14.add_box("basket_floor", (cx, cy, 0.745), (0.74, 0.64, 0.035), basket))
    for dx in (-0.36, 0.36):
        reg(p14.add_box(f"basket_side_x_{dx}", (cx + dx, cy, 0.835),
                        (0.025, 0.64, 0.18), basket))
    for dy in (-0.31, 0.31):
        reg(p14.add_box(f"basket_side_y_{dy}", (cx, cy + dy, 0.835),
                        (0.74, 0.025, 0.18), basket))
    # 遮阳篷：放在车尾（+y），两根细杆 + 薄斜片，不遮脸
    for dx in (-0.32, 0.32):
        reg(p14.add_box(f"hood_rod_{dx}", (cx + dx, cy + 0.28, 1.00),
                        (0.025, 0.025, 0.32), frame))
    hood = reg(p14.add_box("hood", (cx, cy + 0.40, 1.13), (0.70, 0.30, 0.018),
                           mat("hood", 0.86)))
    hood.rotation_euler.x = math.radians(-18)
    # 推车横把（车尾 +y）
    reg(p14.add_box("handle_bar", (cx, cy + 0.36, 1.00), (0.70, 0.035, 0.035), frame))
    for dx in (-0.32, 0.32):
        reg(p14.add_box(f"handle_up_{dx}", (cx + dx, cy + 0.36, 0.83),
                        (0.030, 0.030, 0.35), frame))

    # 躺姿襁褓：身体 + 头 + 五官小点（白模里让「小脸」可辨识）
    reg(p14.add_box("swaddle_body", (cx, cy - 0.02, 0.815), (0.28, 0.42, 0.115), swaddle))
    hx, hy, hz = BABY_HEAD
    reg(add_ball("baby_head", (hx, hy, hz), BABY_HEAD_R, swaddle))
    for ex in (0.085, 0.155):
        reg(add_ball(f"baby_eye_{ex}", (ex, 0.588, 0.945), 0.006, ink))
    reg(add_ball("baby_mouth", (0.120, 0.560, 0.938), 0.006, ink))

    # 婴儿小手：f141-162 抬起抓许宁手指，之后再回落；全程存在，不凭空出现
    baby_hand = reg(add_ball("baby_hand_r", BABY_HAND_HOME, 0.045, swaddle))
    reg(add_ball("baby_hand_l", (0.26, 0.68, 0.845), 0.045, swaddle))

    bpy.context.view_layer.update()
    return parts, wheels, baby_hand


def add_lighting():
    world = bpy.data.worlds.new("previz_world18")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.30, 0.31, 0.33, 1.0)
            n.inputs[1].default_value = 0.90
    bpy.context.scene.world = world
    # 低角度晨光，投出长影（E13_v01 的斜阳）
    bpy.ops.object.light_add(type="SUN", location=(3.4, -1.8, 3.2))
    sun = bpy.context.active_object
    sun.data.energy = 1.9
    sun.data.color = (1.0, 0.90, 0.76)
    sun.rotation_euler = (math.radians(38), math.radians(-26), math.radians(24))
    bpy.ops.object.light_add(type="AREA", location=(-1.8, 1.0, 3.0))
    fill = bpy.context.active_object
    fill.data.energy = 210
    fill.data.size = 3.2
    fill.data.color = (0.90, 0.94, 1.0)
    fill.rotation_euler = (math.radians(28), 0, math.radians(-20))


def act_by_clip(acts, n):
    target = f"animation_{n}"
    for a in acts:
        if a.name.split(".")[0] == target:
            return a
    raise RuntimeError(f"找不到 {target}，现有 {[a.name for a in acts]}")


def head_pose(arm, down, turn, lean):
    p14.rotate_world(arm, "mixamorig:Spine", (1, 0, 0), lean)
    p14.rotate_world(arm, "mixamorig:Spine1", (1, 0, 0), lean * 0.45)
    p14.rotate_world(arm, "mixamorig:Head", (1, 0, 0), down)
    p14.rotate_world(arm, "mixamorig:Neck", (0, 0, 1), turn)
    p14.rotate_world(arm, "mixamorig:Head", (0, 0, 1), turn * 0.55)


def apply_left_arm(arm, ax, ay, fb):
    p14.rotate_ops(arm, "mixamorig:LeftArm", [
        ((0, 1, 0), ay), ((1, 0, 0), ax),
    ])
    p14.rotate_ops(arm, "mixamorig:LeftForeArm", [
        ((0, 1, 0), fb),
    ])


def left_hand_world(arm):
    bpy.context.view_layer.update()
    w = arm.matrix_world @ arm.pose.bones["mixamorig:LeftHand"].matrix.translation
    return (w.x, w.y, w.z)


def arm_anchor_at(f):
    """该帧所在动作段的实测角度，作为求解器的第二起点。

    只靠上一帧 seed 时，f163 起的「抽回身侧」是大跨度跳转，4 轮坐标下降爬不过去
    （v1 测试帧 f176 误差 0.254m）。每段给一个实测 anchor 可让求解器直接落在正确分支。
    """
    if f <= 44:
        return (35.0, 40.0, 60.0)     # HANDLE_V2
    if f <= 96:
        return (-45.0, 40.0, 0.0)    # MOUTH
    if f <= 140:
        return (-40.0, 25.0, 20.0)   # CHEEK
    if f <= 162:
        return (-45.0, 40.0, 0.0)    # MOUTH
    return (0.0, 105.0, -40.0)       # RETREAT


def pose_error(arm, angles, target):
    apply_left_arm(arm, *angles)
    return math.dist(left_hand_world(arm), target)


def solve_left_arm(arm, target, seed, anchor, iters=6, step=22.0):
    """坐标下降：求使左手贴到 target 的 (armX, armY, foreY)。

    弯腰时 Spine/Head 的旋转会传导到手臂，静态探针角度会失准；这里每帧求解。
    起点取「上一帧解」与「本段实测 anchor」中误差更小的一个，兼顾轨迹连续与大跨度跳转。
    不渲帧，只评估依赖图。
    """
    ax, ay, fb = min([seed, anchor], key=lambda c: pose_error(arm, c, target))
    for _ in range(iters):
        cands = [(ax, ay, fb)]
        for d in (-step, step):
            cands.extend([(ax + d, ay, fb), (ax, ay + d, fb), (ax, ay, fb + d)])
        scored = []
        for c in cands:
            apply_left_arm(arm, *c)
            scored.append((math.dist(left_hand_world(arm), target), c))
        _, (ax, ay, fb) = min(scored, key=lambda s: s[0])
        step *= 0.58
    apply_left_arm(arm, ax, ay, fb)
    err = math.dist(left_hand_world(arm), target)
    return (ax, ay, fb), err


def hand_target_at(f):
    for i in range(len(HAND_TRACK) - 1):
        f0, p0 = HAND_TRACK[i]
        f1, p1 = HAND_TRACK[i + 1]
        if f0 <= f <= f1:
            k = p14.ease((f - f0) / (f1 - f0)) if f1 > f0 else 0.0
            return tuple(p0[j] + (p1[j] - p0[j]) * k for j in range(3))
    return HAND_TRACK[-1][1]


def upper_body_at(f):
    """(低头角度, 转身角度, 前倾角度)，段间 ease 渐变。"""
    keys = [
        (1,   (4.0, 0.0, 3.0)),
        (44,  (4.0, 0.0, 3.0)),
        (72,  (18.0, 0.0, 10.0)),
        (100, (26.0, -2.0, 13.0)),
        (124, (26.0, -2.0, 13.0)),
        (140, (-5.0, 2.0, 8.0)),    # 抬头，想起姥姥的手
        (162, (12.0, 0.0, 11.0)),
        (176, (10.0, 0.0, 10.0)),
        (186, (32.0, -2.0, 15.0)),  # 俯身亲额头
        (192, (8.0, 0.0, 5.0)),
    ]
    for i in range(len(keys) - 1):
        f0, p0 = keys[i]
        f1, p1 = keys[i + 1]
        if f0 <= f <= f1:
            k = p14.ease((f - f0) / (f1 - f0)) if f1 > f0 else 0.0
            return tuple(p0[j] + (p1[j] - p0[j]) * k for j in range(3))
    return keys[-1][1]


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    build_room()
    parts, wheels, baby_hand = build_car()
    add_lighting()

    xu, xu_acts, _ = p14.import_glb(os.path.join(MODELS, "C06", "tex_mesh_animated.glb"))
    print("[previs18] xu_acts", len(xu_acts), [a.name for a in xu_acts], flush=True)
    if len(xu_acts) < 5:
        raise RuntimeError("C06 应有 10 个动作 clip")
    idle = act_by_clip(xu_acts, 1)   # Idle_Loop，站姿
    p14.make_loop(idle)
    removed = p14.strip_channels([idle], BONES_MANUAL)
    print("[previs18] stripped", len(removed), "channels", flush=True)
    xu.rotation_mode = "XYZ"
    xu_ad = xu.animation_data
    p14.set_loop(xu_ad, idle, {"key": None}, "idle")
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    dz = -p14.feet_z(xu) + 0.02
    print(f"[previs18] dz={dz:.3f}", flush=True)

    # 白模：自定义场景/道具材质以 s18_ 开头，make_matte 会跳过；角色统一哑光
    matte = p14.make_matte("char_matte18", 0.82)
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        mnames = [m.name for m in o.data.materials] if o.data.materials else []
        if any(n.startswith("s18_") for n in mnames):
            continue
        o.data.materials.clear()
        o.data.materials.append(matte)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = RES_X, RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, N_FRAMES
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    cam_data = bpy.data.cameras.new("previs_cam18")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam18", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    sp, ep = Vector(CAM_START), Vector(CAM_END)

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    if test_mode:
        frames_iter = [1, 24, 44, 60, 84, 96, 112, 132, 148, 160, 176, 186, 192]
    elif os.environ.get("PREVIS_RANGE"):
        a, b = os.environ["PREVIS_RANGE"].split("-")
        frames_iter = range(int(a), int(b) + 1)
    else:
        frames_iter = range(1, N_FRAMES + 1)

    seed = (35.0, 40.0, 60.0)   # HANDLE_V2 实测角度
    max_err, max_err_f = 0.0, 0
    for f in frames_iter:
        t = p14.ease((f - 1) / (N_FRAMES - 1))
        # 推车渐停：车、人、婴儿、目标点同步位移，不做 Walk→Idle 的硬切
        off = PUSH_START * (1.0 - p14.ease((f - 1) / 43.0)) if f <= 44 else 0.0
        for o, by in parts:
            o.location.y = by + off
        roll = (PUSH_START - off) / 0.095
        for w in wheels:
            w.rotation_euler = (roll, math.radians(90), 0)
        xu.location = (XU_XY[0], XU_XY[1] + off, dz)
        xu.rotation_euler = (0, 0, XU_YAW)
        scene.frame_set(f)

        down, turn, lean = upper_body_at(f)
        head_pose(xu, down, turn, lean)

        tgt = hand_target_at(f)
        tgt = (tgt[0], tgt[1] + off, tgt[2])
        # 擦嘴角时的极小幅往复（不脱离目标轨迹）
        if 80 <= f <= 96:
            tgt = (tgt[0], tgt[1] + 0.010 * math.sin(2 * math.pi * (f - 80) / 8.0), tgt[2])
        seed, err = solve_left_arm(xu, tgt, seed, arm_anchor_at(f))
        if err > max_err:
            max_err, max_err_f = err, f

        # 女儿小手：f141-152 抬起抓住她的手指，f153-162 跟着往嘴边带，f163-176 回落
        if f <= 140:
            bh = BABY_HAND_HOME
        elif f <= 152:
            k = p14.ease((f - 141) / 11)
            bh = tuple(BABY_HAND_HOME[j] + (BABY_HAND_GRAB[j] - BABY_HAND_HOME[j]) * k
                       for j in range(3))
        elif f <= 162:
            bh = (BABY_HAND_GRAB[0], BABY_HAND_GRAB[1] - 0.022, BABY_HAND_GRAB[2] - 0.012)
        elif f <= 176:
            k = p14.ease((f - 163) / 13)
            bh = tuple(BABY_HAND_GRAB[j] + (BABY_HAND_HOME[j] - BABY_HAND_GRAB[j]) * k
                       for j in range(3))
        else:
            bh = BABY_HAND_HOME
        baby_hand.location = (bh[0], bh[1] + off, bh[2])

        cam.location = sp.lerp(ep, t)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (AIM - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        if test_mode and f in (1, 44, 72, 96, 112, 132, 148, 160, 176, 186, 192):
            hw = left_hand_world(xu)
            print(f"[previs18] f{f:03d} off={off:.3f} lean={lean:.1f} "
                  f"target=({tgt[0]:.3f},{tgt[1]:.3f},{tgt[2]:.3f}) "
                  f"hand=({hw[0]:.3f},{hw[1]:.3f},{hw[2]:.3f}) err={err:.4f} "
                  f"angles=({seed[0]:.1f},{seed[1]:.1f},{seed[2]:.1f})", flush=True)

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs18] frame {f}/{N_FRAMES}", flush=True)

    print(f"[previs18] max hand solve error = {max_err:.4f} m at f{max_err_f:03d}", flush=True)
    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot18", "title": "楼下晨光·婴儿车",
            "source": "剧本五 L305-311 / 方案 §4 / E13_v01.png",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E13 楼下晨景：左侧收摊早点摊（白布棚/暖壶/盖锅/碗/保温箱/叠凳）、右侧低围墙与后方居民楼形成巷子纵深、低角度晨光长影",
            "camera": [list(CAM_START), list(CAM_END), list(AIM)],
            "stand": {"xu_xy": list(XU_XY), "xu_yaw_deg": 12, "feet_dz": round(dz, 3),
                      "push_start_m": PUSH_START},
            "car": {"center": [CAR_X, CAR_Y], "baby_head": list(BABY_HEAD),
                    "baby_head_radius": BABY_HEAD_R,
                    "note": "C20 为襁褓道具不绑骨；躺姿白模 + 两眼一点嘴，脸面 z≈0.95，与左手目标高度吻合不穿模"},
            "hand_track": [{"frame": a, "target": list(b)} for a, b in HAND_TRACK],
            "arm_solver": {
                "method": "每帧坐标下降求 LeftArm(armX,armY)/LeftForeArm(foreY)，目标为 HAND_TRACK 世界坐标；起点取『上一帧解』与『本段实测 anchor』中误差较小者，6 轮 / 初始步长 22° / 每轮 ×0.58",
                "why": "弯腰时 Spine/Head 旋转会传导到手臂，静态探针角度失准；求解保证手始终贴着完整物理链。v1 只用上一帧 seed，f176 抽回段大跨度跳转收敛不足（误差 0.254m），v2 加分段 anchor 修正",
                "seed_angles": [35, 40, 60],
                "segment_anchors": {"f1-44": [35, 40, 60], "f45-96": [-45, 40, 0],
                                    "f97-140": [-40, 25, 20], "f141-162": [-45, 40, 0],
                                    "f163-192": [0, 105, -40]},
                "probes": ["tmp_qc/probe_xu_arm18.py", "tmp_qc/probe_xu_arm18_fine.py",
                           "tmp_qc/probe_xu_arm18_poses.py", "tmp_qc/shot18_arm_poses.json"],
                "max_error_m": round(max_err, 4),
                "max_error_frame": max_err_f,
            },
            "timeline": {
                "f1-44": "前态：推着婴儿车沿窄巷缓缓停下，车/人/婴儿/轮子同步渐停，双手扶车把",
                "f45-96": "过程A：松开左手弯腰俯身，手渐移向孩子嘴角并轻擦（f80-96 小幅往复）",
                "f97-124": "过程B：指尖在那张柔软的小脸上停住",
                "f125-140": "缓缓抬头，想起许多年前停在头顶的那只手，指不离脸",
                "f141-162": "过程C：女儿小手抬起抓住她的手指、往嘴边带",
                "f163-176": "笑着把手轻轻抽回身侧",
                "f177-192": "后态：俯身亲一下孩子额头，缓缓直起身，镜头微推",
            },
            "three_state": {
                "stroller": "前态缓行（y 偏移 0.22m）→ 过程 ease 渐减速、轮子同步转 → 后态静止，全程不硬切 clip",
                "xu_left_hand": "扶车把 → 抬离并移向嘴角、轻擦 → 指尖停在小脸 → 被带向小嘴 → 笑着抽回身侧 → 直起身时自然回到身侧",
                "xu_upper_body": "微前倾推行 → 弯腰俯身低头 → 抬头望向远处 → 回看孩子 → 更低俯身亲额头 → 缓缓直起",
                "baby_hand": "贴身侧 → 渐抬起抓住母亲手指 → 同向往嘴边带 → 渐回落身侧；全程存在，不凭空出现或消失",
            },
            "characters": {"xu": "C06 ten-clip / clip 1 = Idle_Loop（头颈脊与双臂通道剥出后手 K）",
                           "baby": "C20 襁褓白模道具，按方案 §5 不建模不绑骨"},
            "hard_constraints": "脚贴地；车/人/婴儿同步位移不脱节；左手不漂浮不瞬移不消失且逐帧贴目标轨迹；婴儿小手全程存在；无第四人；段间全 ease 渐变；棚布/围墙不出现正对相机的实心大方板",
        }
        with open(os.path.join(OUT_DIR, "previs18_report.json"), "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS18_DONE", flush=True)


if __name__ == "__main__":
    main()
