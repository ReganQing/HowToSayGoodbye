# -*- coding: utf-8 -*-
"""白模预演：shot20「妈，你晚上吃什么」（剧本六 L321-325，方案 §4）。

场景 E10 出租屋厨房午后版：后墙窗 + 浅窗帘、水槽操作台、灶台与盖锅、
搁板碗碟、小折叠餐桌 + 一把镂空木椅。单人镜头（C06b 许宁·中老年）。

核心动作链（HANDOFF §5.19，必须靠白模给出，prompt 补不出来）：
  前态   挂断电话后独坐，电话在桌面手边；灶上汤锅盖被蒸汽顶得轻颤、蒸汽明显、火大
  过程A  缓缓起身（Sitting_Enter 反放）→ 沿桌子西侧绕到灶前
  过程B  右手贴旋钮把它拧小；旋钮 ease 转 60°、火焰渐矮、锅盖颤动 ease 归零、
         三缕蒸汽 ease 缩短变淡（变化三态，无硬切）
  过程C  回身走回桌边，右手渐伸向电话、抓起话筒沿弧线抬到耳边；
         电话 f129 起由右手骨骼当帧世界坐标驱动，手与话筒零脱节
  后态   站在桌边把话筒贴在耳边轻声问「妈，你晚上吃什么？」，带着很轻的笑；
         锅仍在灶上、只有一丝蒸汽，桌椅窗灶全程同位

道具物理链（§5.19 / §5.21）：
  - 电话：f1–f128 固定桌面 → f129–f152 由右手驱动「离桌 → 抬到耳边」→ f153–f192 贴耳不动；
    全程不消失、不换形、不漂浮。root 原点就是手握点，f129 切换时与桌面位置重合，零跳变。
  - 锅盖全程在锅上、形状恒定，只有颤动振幅 ease 到 0；蒸汽只有高度变化；旋钮只有角度变化。
  - 关键道具前态放在 f001（电话在画面里、在她手边），符合 §5.21。

已知坑（HANDOFF §5）已规避：
  §5.14 按 clip 序号名称取 action、脚高用站姿 Idle 测
  §5.15 add_box 的 dimensions 本质是 scale；蒸汽/火焰按初始 scale 乘倍率；圆柱平躺绕 X 轴
  §5.16 build_room() 末尾补 view_layer.update()
  §5.17 椅背与搁架用镂空细杆，不做正对相机的实心大方板
  §5.19 关键道具必须有完整物理链
  §5.20 手 K 用每帧坐标下降 + 分段 anchor，不用静态角度硬写
  §5.21 关键变化前置、道具首帧画幅与对比度足够

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot20.py
  blender.exe --background --python tools/previs_shot20.py      （192 帧一次性全渲，保证求解器 seed 连续）
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
FRAMES_DIR = os.path.join(OUT_DIR, "frames20")
PROBE_JSON = os.path.join(ROOT, "tmp_qc", "shot20_probe.json")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720
CAM_LENS = 34
CAM_START = (-2.45, -0.95, 1.46)
CAM_END = (-2.05, -0.62, 1.42)
AIM = Vector((0.45, 1.65, 1.02))

WALL_Y = 3.2
WIN_X0, WIN_X1 = -1.9, -0.1
WIN_Z0, WIN_Z1 = 1.15, 2.35
COUNTER_Y = 2.85
COUNTER_TOP_Z = 0.88
TABLE_CENTER = (1.15, 1.45)
CHAIR = (0.55, 0.88)   # v2：椅子左移，镂空椅背不再挡住桌面电话

# 站位与朝向：模型默认朝 -y，rot z=180 时朝 +y（面向窗 / 台面 / 桌子）
SIT_LOC = (0.55, 0.88)
RISE_LOC = (0.55, 0.72)
STOVE_LOC = (0.42, 2.30)
TABLE_LOC = (1.15, 0.90)
YAW_FACE = math.radians(180)

# 绕桌子西侧去灶台、原路回身，避免穿过桌角（shot14 同款走位思路）
PATH_TO_STOVE = ((0.55, 0.72), (0.22, 0.98), (0.14, 1.85), (0.42, 2.30))
PATH_BACK = ((0.42, 2.30), (0.14, 1.85), (0.32, 1.00), (1.15, 0.90))

# 探针实测可达点（tmp_qc/shot20_probe.json）
KNOB = (0.445, 2.548, 0.986)
PHONE_HOME = (1.118, 1.120, 0.893)   # v2：桌面近中、避开椅背；同时是「手握点」
# v2：耳朵目标不再写死世界点（v1 把它放在头顶上方 0.2m，成片会读成「举着电话」），
# 改成每帧读 Head 骨骼世界坐标再加这个小偏移，头微侧时目标跟着动。
EAR_REL = (0.13, -0.02, 0.04)   # v4 再降 0.03m；话筒横放后不再翘到头顶上方
RETREAT_ANG = (-45.0, -132.1, 0.0, 56.6)   # shot19 实测：手臂垂下体侧
# v6：探针里 ear 解的 best_start，作为动态/稳态贴耳求解的额外起点，
# 专门用来绕开 v5 EAR_LOCK 卡住的 ForeArm fb=-90° 局部最优。
EAR_START = (-20.0, 150.0, 0.0, -40.0)

BONES = ("mixamorig:RightArm", "mixamorig:RightForeArm",
         "mixamorig:LeftArm", "mixamorig:LeftForeArm",
         "mixamorig:Head", "mixamorig:Neck",
         "mixamorig:Spine", "mixamorig:Spine1")


def mat(key, shade, emission=None):
    return p14.mat("s20_" + key, shade, emission)


def add_chair(name, px, py, shade=0.55):
    """镂空栏杆椅背（§5.17），不用整块实心板。"""
    c = mat("chair", shade)
    p14.add_box(f"{name}_seat", (px, py, 0.44), (0.45, 0.45, 0.05), c)
    for dx in (-0.17, 0.17):
        p14.add_box(f"{name}_post_{dx}", (px + dx, py - 0.20, 0.75),
                    (0.045, 0.045, 0.60), c)
    for z in (0.62, 0.99):
        p14.add_box(f"{name}_rail_{z}", (px, py - 0.20, z),
                    (0.40, 0.045, 0.05), c)
    for lx in (-0.18, 0.18):
        for ly in (-0.18, 0.18):
            p14.add_box(f"{name}_leg_{lx}_{ly}", (px + lx, py + ly, 0.22),
                        (0.04, 0.04, 0.44), c)


def build_room():
    """E10 厨房午后版：窗 + 水槽台 + 灶台盖锅 + 搁板 + 折叠餐桌 + 一把椅。"""
    wall = mat("wall", 0.62)
    p14.add_box("floor", (0, 0, -0.05), (7.0, 8.0, 0.1), mat("floor", 0.42))
    p14.add_box("ceiling", (0, 0, 2.7), (7.0, 8.0, 0.1), mat("ceil", 0.56))
    p14.add_box("left_wall", (-3.2, 0, 1.35), (0.12, 8.0, 2.7), wall)
    p14.add_box("right_wall", (3.2, 0, 1.35), (0.12, 8.0, 2.7), wall)
    p14.add_box("wall_back_l", ((-3.3 + WIN_X0) / 2, WALL_Y, 1.35),
                (WIN_X0 + 3.3, 0.12, 2.7), wall)
    p14.add_box("wall_back_r", ((WIN_X1 + 3.3) / 2, WALL_Y, 1.35),
                (3.3 - WIN_X1, 0.12, 2.7), wall)
    p14.add_box("wall_back_top", ((WIN_X0 + WIN_X1) / 2, WALL_Y, (WIN_Z1 + 2.7) / 2),
                (WIN_X1 - WIN_X0, 0.12, 2.7 - WIN_Z1), wall)
    p14.add_box("wall_back_bot", ((WIN_X0 + WIN_X1) / 2, WALL_Y, WIN_Z0 / 2),
                (WIN_X1 - WIN_X0, 0.12, WIN_Z0), wall)
    frame = mat("frame", 0.48)
    cx, cz = (WIN_X0 + WIN_X1) / 2, (WIN_Z0 + WIN_Z1) / 2
    p14.add_box("win_f_l", (WIN_X0, WALL_Y - 0.03, cz), (0.07, 0.08, WIN_Z1 - WIN_Z0), frame)
    p14.add_box("win_f_r", (WIN_X1, WALL_Y - 0.03, cz), (0.07, 0.08, WIN_Z1 - WIN_Z0), frame)
    p14.add_box("win_f_h", (cx, WALL_Y - 0.03, WIN_Z1),
                (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    p14.add_box("win_f_b", (cx, WALL_Y - 0.03, WIN_Z0),
                (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    p14.add_box("win_f_m", (cx, WALL_Y - 0.03, cz), (0.05, 0.08, WIN_Z1 - WIN_Z0), frame)
    p14.add_box("daylight", (cx, WALL_Y + 3.0, 1.8), (7.0, 0.1, 3.6),
                mat("daylight", 0.72, emission=(0.60, 0.64, 0.70, 1.0)))
    p14.add_box("windowsill", (cx, WALL_Y - 0.22, WIN_Z0 - 0.03),
                (WIN_X1 - WIN_X0 + 0.24, 0.42, 0.05), mat("sill", 0.68))
    p14.add_box("curtain", (WIN_X0 - 0.12, WALL_Y - 0.12, 1.75),
                (0.34, 0.05, 1.20), mat("curtain", 0.84))

    # 操作台 / 水槽（静态，无水）
    p14.add_box("counter_body", (-1.0, COUNTER_Y, 0.44), (3.0, 0.6, 0.88), mat("cab", 0.58))
    p14.add_box("counter_top", (-1.0, COUNTER_Y, COUNTER_TOP_Z + 0.02),
                (3.06, 0.66, 0.05), mat("top", 0.80))
    p14.add_box("sink_basin", (-1.0, COUNTER_Y - 0.05, COUNTER_TOP_Z + 0.01),
                (0.56, 0.40, 0.04), mat("sink", 0.30))
    p14.add_cyl("faucet_stem", (-1.0, COUNTER_Y + 0.22, 1.03), 0.022, 0.32,
                mat("faucet", 0.55))
    p14.add_cyl("faucet_arm", (-1.0, COUNTER_Y + 0.10, 1.17), 0.020, 0.26,
                mat("faucet", 0.55), rot=(math.radians(90), 0, 0))
    for i in range(3):
        p14.add_cyl(f"bowl_stack_{i}", (-0.42, COUNTER_Y + 0.05, 0.95 + i * 0.055),
                    0.085, 0.05, mat("bowl", 0.78))
    p14.add_cyl("kettle", (0.15, COUNTER_Y, 0.99), 0.075, 0.22, mat("kettle", 0.70))

    # 灶台 + 旋钮 + 汤锅 + 锅盖（锅盖形状恒定，只改颤动振幅）
    p14.add_box("cooker", (0.42, COUNTER_Y, 0.96), (0.30, 0.30, 0.06), mat("cooker", 0.42))
    knob = p14.add_cyl("stove_knob", (0.42, 2.60, 0.96), 0.038, 0.030,
                       mat("knob", 0.16), rot=(math.radians(90), 0, 0))
    p14.add_cyl("pot", (0.42, COUNTER_Y, 1.045), 0.130, 0.110, mat("pot", 0.34))
    lid = p14.add_cyl("pot_lid", (0.42, COUNTER_Y, 1.106), 0.142, 0.018, mat("lid", 0.40))
    p14.add_cyl("lid_handle", (0.42, COUNTER_Y, 1.125), 0.025, 0.022, mat("lid", 0.40))
    flame = p14.add_cyl("flame", (0.42, COUNTER_Y, 0.995), 0.095, 0.060,
                        mat("flame", 0.55, emission=(1.0, 0.62, 0.28, 1.0)))

    # 三缕蒸汽：v8 去掉 emission、改 0.36 中灰并加粗到 r=0.038，
    # 浅背景上才看得出「蒸汽多 → 变淡」的三态渐变（§5.21 道具前态要够清晰）。
    # 初始 scale 全部为 1，按倍率缩放（§5.15）。
    steam = []
    for i, dx in enumerate((-0.060, 0.0, 0.060)):
        s = p14.add_cyl(f"steam_{i}", (0.42 + dx, COUNTER_Y, 1.34 + i * 0.02),
                        0.038, 0.42, mat("steam", 0.36))
        steam.append((s, tuple(s.scale)))

    # 搁板：细杆通透，不做实心板（§5.17）
    shelf = mat("shelf", 0.55)
    p14.add_box("shelf_board", (1.15, WALL_Y - 0.18, 1.62), (1.1, 0.30, 0.04), shelf)
    for name, x in (("shelf_l", 0.65), ("shelf_r", 1.65)):
        p14.add_box(name, (x, WALL_Y - 0.18, 1.76), (0.04, 0.28, 0.32), shelf)
    p14.add_cyl("jar_1", (0.90, WALL_Y - 0.18, 1.76), 0.055, 0.22, mat("jar", 0.62))
    p14.add_cyl("jar_2", (1.10, WALL_Y - 0.18, 1.75), 0.05, 0.20, mat("jar2", 0.58))
    for i in range(2):
        p14.add_cyl(f"shelf_bowl_{i}", (1.38, WALL_Y - 0.18, 1.67 + i * 0.05),
                    0.075, 0.045, mat("bowl", 0.78))

    # 折叠餐桌 + 桌布 + 一把椅
    tx, ty = TABLE_CENTER
    p14.add_box("table_top", (tx, ty, 0.74), (1.15, 0.80, 0.05), mat("table", 0.55))
    p14.add_box("tablecloth", (tx, ty, 0.769), (1.21, 0.86, 0.012), mat("cloth", 0.74))
    for dx in (-0.50, 0.50):
        for dy in (-0.32, 0.32):
            p14.add_box(f"table_leg_{dx}_{dy}", (tx + dx, ty + dy, 0.37),
                        (0.05, 0.05, 0.72), mat("leg", 0.45))
    add_chair("chair_near", *CHAIR)

    # §5.16：强制刷新依赖图，最后创建的几何体 dimensions 才会生效
    bpy.context.view_layer.update()
    return knob, lid, flame, steam


def build_phone():
    """一体式座机话筒：Empty 作 root，原点就是「手握点」。

    子件全挂 root 局部坐标，机身底落在桌面 z≈0.80（root z=0.893）。
    f1–f128 root 固定在 PHONE_HOME；f129 起 root 直接跟右手骨骼世界坐标，
    与桌面位置重合，切换零跳变（shot19 报纸由双手驱动的同一思路）。
    """
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=PHONE_HOME)
    root = bpy.context.active_object
    root.name = "phone_root"
    body = mat("phone_body", 0.08)   # v2 加深到近黑，浅色桌布上高对比
    light = mat("phone_light", 0.74)

    def piece(name, loc, dims, m):
        o = p14.add_box(name, loc, dims, m)
        o.parent = root
        return o

    # 机身（横放桌面）与听筒两端、按键行——v4 再放大一档，f001 首帧就能看见
    piece("phone_shell", (0, 0, -0.040), (0.34, 0.17, 0.085), body)
    piece("phone_ear_l", (-0.145, 0, 0.012), (0.065, 0.140, 0.055), body)
    piece("phone_ear_r", (0.145, 0, 0.012), (0.065, 0.140, 0.055), body)
    for r in range(3):
        for c in range(3):
            piece(f"phone_key_{r}_{c}", (-0.062 + c * 0.062, -0.018 + r * 0.038, 0.006),
                  (0.028, 0.020, 0.008), light)
    bpy.context.view_layer.update()
    return root


def add_lighting():
    world = bpy.data.worlds.new("previz_world20")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.28, 0.29, 0.32, 1.0)
            n.inputs[1].default_value = 0.74
    bpy.context.scene.world = world
    # 窗口冷蓝灰主光
    bpy.ops.object.light_add(type="AREA", location=((WIN_X0 + WIN_X1) / 2, WALL_Y + 1.6, 2.0))
    key = bpy.context.active_object
    key.data.energy = 240
    key.data.size = 3.2
    key.data.color = (0.72, 0.80, 1.0)
    key.rotation_euler = (math.radians(65), 0, math.radians(180))
    # 墙上一块暖光用软点光源，不做几何光斑板片（§5.15）
    bpy.ops.object.light_add(type="POINT", location=(-2.35, 2.45, 1.95))
    warm = bpy.context.active_object
    warm.data.energy = 150
    warm.data.color = (1.0, 0.82, 0.60)
    bpy.ops.object.light_add(type="AREA", location=(1.15, 0.9, 2.2))
    fill = bpy.context.active_object
    fill.data.energy = 115
    fill.data.size = 2.0
    fill.data.color = (1.0, 0.88, 0.74)
    fill.rotation_euler = (math.radians(35), 0, math.radians(15))


def act_by_clip(acts, n):
    target = f"animation_{n}"
    for a in acts:
        if a.name.split(".")[0] == target:
            return a
    raise RuntimeError(f"找不到 {target}，现有 {[a.name for a in acts]}")


def strip_hips_motion(acts):
    """删掉 Walk_Loop 的 Hips 位移/旋转通道。

    C06b 的 animation_2 带 root motion：走路段 Hips 会把上半身整体推走
    0.6–1.3m（v2 测试帧 f080 手在 y=3.009、f128 在 y=2.217，都快插进后墙），
    连带让「每帧实测的体侧基准点」失效、伸手拿电话的求解误差 0.78m。
    腿部通道保留，走路仍然成立；Sitting_Enter 不能剥（起身靠骨盆升降）。
    """
    targets = ('pose.bones["mixamorig:Hips"].location',
               'pose.bones["mixamorig:Hips"].rotation_quaternion')
    removed = []
    for ac in acts:
        for layer in ac.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in list(bag.fcurves):
                        if fc.data_path in targets:
                            bag.fcurves.remove(fc)
                            removed.append(f"{ac.name}:{fc.data_path.split('.')[-1]}")
    return removed


def set_oneshot_reverse(ad, act, f0, speed, state, key):
    """把「站→坐」的 Sitting_Enter 倒放成「坐→站」的起身（Blender 5.2 支持 use_reverse）。"""
    if state.get("key") == key:
        return
    ad.action = None
    for tr in list(ad.nla_tracks):
        ad.nla_tracks.remove(tr)
    tr = ad.nla_tracks.new()
    s0, s1 = act.frame_range
    length = max(float(s1 - s0), 1.0)
    strip = tr.strips.new(act.name, int(f0), act)
    strip.action_frame_start = s0
    strip.action_frame_end = s1
    strip.frame_end = f0 + length / speed
    strip.use_reverse = True
    state["key"] = key


def apply_arm(arm, side, ax, ay, az, fb):
    p14.rotate_ops(arm, f"mixamorig:{side}Arm", [
        ((0, 1, 0), ay), ((1, 0, 0), ax), ((0, 0, 1), az),
    ])
    p14.rotate_ops(arm, f"mixamorig:{side}ForeArm", [((0, 1, 0), fb)])


def hand_world(arm, side):
    bpy.context.view_layer.update()
    w = arm.matrix_world @ arm.pose.bones[f"mixamorig:{side}Hand"].matrix.translation
    return (w.x, w.y, w.z)


def lerp3(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def lerp_ang(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(4))


def solve_right(arm, target, seeds, iters=7, step=22.0):
    """每帧坐标下降贴三维目标；多起点分别收敛，取全局误差最小分支。

    v6：角度空间存在明显局部最优（v4 f140 误差 0.2422m、v5 EAR_LOCK 卡在
    fb=-90° 边界误差 0.1225m）。单起点或跨帧静态角度都不稳，改为每帧从
    「上一帧解 + 分段 anchor + 探针实测解 + 探针 best_start」分别出发，
    且全部在**当前帧骨骼状态**下实测误差（§5.20）。
    """
    best = None
    for start in seeds:
        cur = list(start)
        s = step
        for _ in range(iters):
            cands = [tuple(cur)]
            for j in range(4):
                for d in (-s, s):
                    c = list(cur)
                    c[j] += d
                    cands.append(tuple(c))
            scored = []
            for c in cands:
                apply_arm(arm, "Right", *c)
                scored.append((math.dist(hand_world(arm, "Right"), target), c))
            _, cur = min(scored, key=lambda x: x[0])
            s *= 0.6
        apply_arm(arm, "Right", *cur)
        e = math.dist(hand_world(arm, "Right"), target)
        if best is None or e < best[0]:
            best = (e, tuple(cur))
    apply_arm(arm, "Right", *best[1])
    return best[1], best[0]


def path_point(pts, k):
    k = max(0.0, min(1.0, k))
    segs = len(pts) - 1
    sk = k * segs
    i = min(int(sk), segs - 1)
    return Vector(pts[i]).lerp(Vector(pts[i + 1]), sk - i)


def path_facing(pts, k):
    k = max(0.0, min(1.0, k))
    segs = len(pts) - 1
    sk = k * segs
    i = min(int(sk), segs - 1)
    d = Vector(pts[i + 1]) - Vector(pts[i])
    if d.length < 1e-6:
        return 0.0
    d.normalize()
    return math.degrees(math.atan2(d.x, -d.y))


def blend_rot(start, end, t):
    d = (end - start + 180.0) % 360.0 - 180.0
    return start + d * max(0.0, min(1.0, t))


def head_pose(arm, down, turn):
    p14.rotate_ops(arm, "mixamorig:Head", [
        ((1, 0, 0), down), ((0, 0, 1), turn * 0.55),
    ])
    p14.rotate_world(arm, "mixamorig:Neck", (0, 0, 1), turn * 0.6)


def k_fire(f):
    """关火进度：f81 开始、f104 到底，段内 ease。"""
    if f <= 80:
        return 0.0
    if f <= 104:
        return p14.ease((f - 81) / 23.0)
    return 1.0


def head_world(arm):
    bpy.context.view_layer.update()
    w = arm.matrix_world @ arm.pose.bones["mixamorig:Head"].matrix.translation
    return (w.x, w.y, w.z)


def right_target(f, rest_pt, ear_pt):
    """右手目标轨迹：体侧 → 旋钮 → 体侧 → 电话 → 耳边。

    v2 关键修正：**体侧位置不再写死成世界点**。v1 把 shot19 的绝对手部坐标当成
    「相对偏移」，结果起身/走路/收手段的目标跑到人外一米，求解器误差最高 1.77m、
    手臂被甩出去。现在每帧先摆回体侧角度、实测手的世界坐标 rest_pt，
    目标都在世界空间从 rest_pt 出发做直线插值，站位与朝向怎么变都不会脱节。
    耳朵目标 ear_pt 由 Head 骨骼当帧坐标推导，头微侧时跟着动。
    返回 (目标点或 None, 分段 anchor)；None 表示该段直接锁体侧角度，不求解。
    """
    if f <= 80:      # 坐姿独处 / 起身 / 走向灶台：手臂自然垂在体侧
        return None, ANG["retreat"]
    if f <= 90:      # 渐伸手到旋钮
        return lerp3(rest_pt, KNOB, p14.ease((f - 81) / 9.0)), ANG["knob"]
    if f <= 104:     # 贴住旋钮拧火
        return KNOB, ANG["knob"]
    if f <= 116:     # 收手回体侧
        return lerp3(KNOB, rest_pt, p14.ease((f - 105) / 11.0)), ANG["knob"]
    if f <= 128:     # 回身走位 + 渐伸向桌面电话
        return lerp3(rest_pt, PHONE_HOME, p14.ease((f - 117) / 11.0)), ANG["phone"]
    if f <= 152:
        # v6：把「同时追 xy 与 z」拆成两段 ease。v4 的直线插值让求解器先把
        # y 对齐、z 却过冲 0.14m；现在 xy 先到位（13 帧），z 晚 5 帧起步再抬
        # （18 帧），每帧目标只在单一方向小幅移动，配合多起点可稳定收敛。
        k_xy = p14.ease((f - 129) / 13.0)
        k_z = p14.ease((f - 134) / 18.0)
        tgt = (PHONE_HOME[0] + (ear_pt[0] - PHONE_HOME[0]) * k_xy,
               PHONE_HOME[1] + (ear_pt[1] - PHONE_HOME[1]) * k_xy,
               PHONE_HOME[2] + (ear_pt[2] - PHONE_HOME[2]) * k_z)
        return tgt, ANG["phone"] if f <= 138 else ANG["ear"]
    return ear_pt, ANG["ear"]


def main():
    global ANG
    with open(PROBE_JSON, encoding="utf-8") as fh:
        probe = json.load(fh)
    sol = probe["solutions"]
    ANG = {
        "retreat": RETREAT_ANG,
        "knob": tuple(sol["knob"]["angles"]),
        "phone": tuple(sol["phone_table"]["angles"]),
        "ear": tuple(sol["ear"]["angles"]),
    }
    print("[previs20] anchors", {k: [round(v, 1) for v in a] for k, a in ANG.items()}, flush=True)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    knob, lid, flame, steam = build_room()
    phone_root = build_phone()
    add_lighting()

    xu, acts, _ = p14.import_glb(os.path.join(MODELS, "C06b", "tex_mesh_animated.glb"))
    print("[previs20] acts", len(acts), [a.name for a in acts], flush=True)
    if len(acts) < 4:
        raise RuntimeError("C06b 应有 10 个动作 clip")
    a_idle = act_by_clip(acts, 1)       # Idle_Loop
    a_walk = act_by_clip(acts, 2)       # Walk_Loop
    a_sit_e = act_by_clip(acts, 3)      # Sitting_Enter（反放做起身）
    a_sit_i = act_by_clip(acts, 4)      # Sitting_Idle_Loop
    for a in (a_idle, a_walk, a_sit_i):
        p14.make_loop(a)
    removed = p14.strip_channels([a_idle, a_walk, a_sit_e, a_sit_i], BONES)
    removed_hips = strip_hips_motion([a_walk])
    print("[previs20] stripped", len(removed), "channels; hips motion",
          len(removed_hips), "channels", flush=True)

    ad = xu.animation_data
    scene = bpy.context.scene
    # 脚高校正必须拿站姿 Idle 测（§5.14）
    p14.set_loop(ad, a_idle, {"key": None}, "idle_probe")
    xu.rotation_mode = "XYZ"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    dz = -p14.feet_z(xu) + 0.02
    print(f"[previs20] feet dz = {dz:.4f}", flush=True)

    matte = p14.make_matte("char_matte20", 0.50)   # v2 加深，人物与浅色墙地分开
    for o in [o for o in scene.objects if o.type == "MESH"]:
        mnames = [m.name for m in o.data.materials] if o.data.materials else []
        if any(n.startswith("s20_") for n in mnames):
            continue
        o.data.materials.clear()
        o.data.materials.append(matte)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = RES_X, RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, N_FRAMES
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    cam_data = bpy.data.cameras.new("previs_cam20")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam20", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    sp, ep = Vector(CAM_START), Vector(CAM_END)

    # v6：取消 EAR_LOCK 预计算。v5 证明跨帧复用静态角度必然失准（§5.20）——
    # 预计算在 frame_set(1) 的 Idle 姿态下求解，主循环每帧 Idle 重心与 Spine
    # 传导都不同。贴耳稳态改由「每帧多起点求解 + 误差 >0.03m 自动重求」给出。
    test_mode = os.environ.get("PREVIS_TEST") == "1"
    if test_mode:
        frames_iter = [1, 16, 32, 40, 52, 64, 80, 92, 104, 116, 128, 140, 152, 168, 192]
    elif os.environ.get("PREVIS_RANGE"):
        a, b = os.environ["PREVIS_RANGE"].split("-")
        frames_iter = range(int(a), int(b) + 1)
    else:
        frames_iter = range(1, N_FRAMES + 1)

    st = {"key": None}
    seed = ANG["retreat"]
    max_err, max_err_f = 0.0, 0
    phone_samples = []
    for f in frames_iter:
        t = p14.ease((f - 1) / (N_FRAMES - 1))
        kf = k_fire(f)

        # ---------- 动作段与站位 ----------
        if f <= 32:
            p14.set_loop(ad, a_sit_i, st, "sit")
            loc, yaw = SIT_LOC, 180.0
        elif f <= 52:
            set_oneshot_reverse(ad, a_sit_e, 33, 31.2 / 20.0, st, "rise")
            k = p14.ease((f - 33) / 19.0)
            loc = (SIT_LOC[0] + (RISE_LOC[0] - SIT_LOC[0]) * k,
                   SIT_LOC[1] + (RISE_LOC[1] - SIT_LOC[1]) * k)
            yaw = 180.0
        elif f <= 80:
            p14.set_loop(ad, a_walk, st, "walk1")
            k = p14.ease((f - 53) / 27.0)
            p = path_point(PATH_TO_STOVE, k)
            loc = (p.x, p.y)
            tang = path_facing(PATH_TO_STOVE, k)
            yaw = blend_rot(180.0, tang, k / 0.14) if k < 0.14 else (
                blend_rot(tang, 180.0, (k - 0.80) / 0.20) if k > 0.80 else tang)
        elif f <= 104:
            p14.set_loop(ad, a_idle, st, "stove")
            loc, yaw = STOVE_LOC, 180.0
        elif f <= 128:
            p14.set_loop(ad, a_walk, st, "walk2")
            k = p14.ease((f - 105) / 23.0)
            p = path_point(PATH_BACK, k)
            loc = (p.x, p.y)
            tang = path_facing(PATH_BACK, k)
            yaw = blend_rot(180.0, tang, k / 0.16) if k < 0.16 else (
                blend_rot(tang, 180.0, (k - 0.78) / 0.22) if k > 0.78 else tang)
        else:
            p14.set_loop(ad, a_idle, st, "table")
            loc, yaw = TABLE_LOC, 180.0

        # NLA / action 切换后必须 frame_set 才会在当前帧重新评估骨骼
        scene.frame_set(f)
        xu.location = (loc[0], loc[1], dz)
        xu.rotation_euler = (0, 0, math.radians(yaw))
        bpy.context.view_layer.update()

        # ---------- 头与手 ----------
        down = 5.0 if f <= 32 else 1.5
        turn = 0.0
        if f >= 153:
            turn = 3.0 + 1.2 * math.sin((f - 153) / 9.0)
        head_pose(xu, down, turn)

        # 每帧先摆回体侧角度、实测「手垂在身侧」的当帧世界坐标；
        # 耳朵目标跟 Head 骨骼走，避免 v1 把话筒举到头顶上方 0.2m。
        apply_arm(xu, "Right", *ANG["retreat"])
        rest_pt = hand_world(xu, "Right")
        hd = head_world(xu)
        ear_pt = (hd[0] + EAR_REL[0], hd[1] + EAR_REL[1], hd[2] + EAR_REL[2])
        tgt, anchor = right_target(f, rest_pt, ear_pt)
        if tgt is None:
            solved, err = ANG["retreat"], 0.0
        elif f <= 128:
            solved, err = solve_right(xu, tgt, [seed, anchor], iters=7, step=22.0)
        elif f <= 152:
            # 动态抬升：四起点 + 误差兜底重求。v6 只用一次 10 轮/24° 求解，
            # f140/f152 仍停在坏分支（0.1970/0.1302m）；稳态之所以能收敛，
            # 靠的是 err>0.03 时换大步长重求跳出局部最优。这里补同一套兜底。
            solved, err = solve_right(
                xu, tgt, [seed, anchor, ANG["ear"], EAR_START],
                iters=9, step=20.0)
            if err > 0.035:
                solved, err = solve_right(
                    xu, tgt, [solved, ANG["ear"], EAR_START, ANG["phone"]],
                    iters=14, step=30.0)
            if err > 0.05:
                solved, err = solve_right(
                    xu, tgt, [solved, ANG["ear"], EAR_START],
                    iters=14, step=12.0)
        else:
            # 稳态贴耳：上一帧解微调 + 双锚点兜底；误差超标再高精度重求
            solved, err = solve_right(
                xu, tgt, [seed, ANG["ear"], EAR_START], iters=8, step=18.0)
            if err > 0.03:
                solved, err = solve_right(
                    xu, tgt, [solved, ANG["ear"], EAR_START],
                    iters=12, step=26.0)
        seed = solved
        if err > max_err:
            max_err, max_err_f = err, f

        # 左手：垂在体侧，f137–f148 在机身上做小幅点按（拨号拓扑）
        dial = 0.0
        if 137 <= f <= 148:
            dial = 7.0 * math.sin((f - 137) * math.pi / 3.0)
        apply_arm(xu, "Left", 0.0, 72.0 + dial, 0.0, -8.0)

        # ---------- 电话：f129 起由右手骨骼驱动 ----------
        if f <= 128:
            phone_root.location = PHONE_HOME
            phone_root.rotation_euler = (0, 0, 0)
        else:
            hw = hand_world(xu, "Right")
            phone_root.location = hw
            k_rot = p14.ease((f - 129) / 17.0)
            # v4：55° 会让 0.30m 长的话筒竖起来翘到头顶上方，改成 18° 近横放贴耳
            phone_root.rotation_euler = (0, math.radians(18) * k_rot, 0)
        bpy.context.view_layer.update()
        phone_samples.append((f, [round(v, 3) for v in phone_root.location]))

        # ---------- 灶台三态：旋钮 / 火焰 / 锅盖 / 蒸汽 ----------
        knob.rotation_euler = (math.radians(90), math.radians(60) * kf, 0)
        flame.scale = (1.0, 1.0, 1.0 - 0.66 * kf)
        lid.location.z = 1.106 + (1.0 - kf) * 0.008 * math.sin(f * 0.9)
        for i, (s, s0) in enumerate(steam):
            h = 1.0 - 0.78 * kf
            wob = 1.0 + 0.10 * math.sin(f * 0.35 + i * 1.7)
            s.scale = (s0[0] * wob, s0[1] * wob, s0[2] * h)
            s.location.z = 1.34 + i * 0.02 + 0.02 * math.sin(f * 0.28 + i)

        # ---------- 相机 ----------
        cam.location = sp.lerp(ep, t)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (AIM - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        if test_mode:
            hw = hand_world(xu, "Right")
            tdisp = tgt if tgt is not None else rest_pt
            print(f"[previs20] f{f:03d} kf={kf:.2f} loc=({loc[0]:.2f},{loc[1]:.2f}) "
                  f"yaw={yaw:.0f} hand=({hw[0]:.3f},{hw[1]:.3f},{hw[2]:.3f}) "
                  f"tgt=({tdisp[0]:.3f},{tdisp[1]:.3f},{tdisp[2]:.3f}) err={err:.4f} "
                  f"rest=({rest_pt[0]:.3f},{rest_pt[1]:.3f},{rest_pt[2]:.3f}) "
                  f"ear=({ear_pt[0]:.3f},{ear_pt[1]:.3f},{ear_pt[2]:.3f}) "
                  f"phone=({phone_root.location.x:.3f},{phone_root.location.y:.3f},"
                  f"{phone_root.location.z:.3f})", flush=True)

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs20] frame {f}/{N_FRAMES}", flush=True)

    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot20", "title": "妈，你晚上吃什么",
            "source": "剧本六 L321-325 / 方案 §4 / E10_v01.png",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E10 出租屋厨房午后版：后墙窗+浅窗帘、水槽操作台、灶台与盖锅、搁板碗碟、折叠餐桌+桌布、一把镂空木椅；午后软蓝灰窗光 + 墙面暖光（软点光源，无几何光斑板）",
            "camera": [list(CAM_START), list(CAM_END), list(AIM)],
            "characters": "C06b 许宁·中老年 ten-clip：clip 1 Idle_Loop / clip 2 Walk_Loop / clip 3 Sitting_Enter（反放做起身）/ clip 4 Sitting_Idle_Loop；四个动作的双臂与头颈通道全部剥出，每帧统一手 K",
            "stand": {
                "sit": list(SIT_LOC), "rise_end": list(RISE_LOC),
                "stove": list(STOVE_LOC), "table": list(TABLE_LOC),
                "chair": list(CHAIR), "feet_dz": round(dz, 4),
                "path_to_stove": [list(p) for p in PATH_TO_STOVE],
                "path_back": [list(p) for p in PATH_BACK],
                "yaw_face_deg": 180,
            },
            "phone": {
                "driver": "f1–f128 固定桌面 PHONE_HOME；f129 起 root 直接取右手骨骼当帧世界坐标，f129–f152 手从 PHONE_HOME 沿『先水平 xy 到位（13 帧）、后垂直 z 抬升（18 帧）』两段 ease 到动态耳侧目标；root 旋转 ease 转 18°（近横放贴耳）；f153–f192 贴耳不动",
                "home": list(PHONE_HOME),
                "ear": "动态：Head 骨骼当帧世界坐标 + (0.13,-0.02,0.04)，头微侧时跟着动",
                "why": "HANDOFF §5.19：关键叙事道具必须有完整可辨识的物理链。root 原点就是手握点、初始位置与手抓位置重合，f129 切换零跳变；话筒离桌→抬到耳边本身就是手臂运动的结果",
                "shape_constant": True, "never_disappears": True,
                "first_frame_visible": True,
                "v2_visibility_fix": "v1 电话被椅背挡住、f001 首帧看不见；v2 把椅子从 (0.75,0.88) 左移到 (0.55,0.88)、电话移到桌面近中 (1.118,1.120)，并把机身放大、灰度压到 0.08；v4 放大到 0.30×0.15×0.080；v8 再放大到 0.34×0.17×0.085 并压暗桌布",
                "samples": phone_samples[::24],
            },
            "stove_three_state": {
                "knob": "f1–f80 大火角度 0° → f81–f104 ease 转 60° → f105–f192 保持小火角度",
                "flame": "f1–f80 高 0.055m → f81–f104 ease 缩到 0.019m → 后态保持；发光材质不变",
                "lid": "f1–f80 z 方向 ±0.008m 轻颤 → f81–f104 振幅 ease 归零 → 后态完全静止；锅盖形状与位置恒定、始终在锅上",
                "steam": "f1–f80 三缕高 0.30m、轻微摆动 → f81–f104 ease 缩到 0.066m → 后态只剩淡淡一丝；只改高度与摆动，不改变数量",
                "why": "变化三态原则：前态、后态、渐变过程全部写清，段间用 ease，无硬切",
            },
            "arm_solver": {
                "method": "f1–f80 直接锁体侧角度（不做求解，手随身体走）；f81 起每帧先摆回体侧角度、实测 rest_pt 当基准，再在世界空间把目标从 rest_pt → KNOB → rest_pt → PHONE_HOME → 动态耳侧点做 ease 插值。多起点坐标下降、每轮 ×0.6：f81–f128 双起点（上一帧解 + 分段 anchor，7 轮 / 步长 22°）；f129–f152 四起点（9 轮 / 20°）+ 两道误差兜底（>0.035 → 14 轮 / 30°；>0.05 → 14 轮 / 12°），目标轨迹拆成 xy 先行、z 后抬两段；f153–f192 三起点微调（8 轮 / 18°），误差 >0.03m 自动 12 轮 / 26° 重求兜底。左手固定体侧角度并在 f137–f148 做 7° 小幅点按表示拨号",
                "probes": ["tmp_qc/probe_shot20.py", "tmp_qc/shot20_probe.json"],
                "probe_finding": "首版起点集缺 shot19 实测的 xu_retreat (-45,-132,0,56.6)（手臂垂下体侧），桌面电话被误判不可达（误差 0.534m）；补 7 组历史端点 + 大角度起点、并把 solve 返回前重新 apply 最优解后，旋钮/电话/耳边误差降到 0.063/0.123/0.083m，全部可达",
                "anchors": {k: [round(v, 1) for v in a] for k, a in ANG.items()},
                "max_error_m": round(max_err, 4),
                "max_error_frame": max_err_f,
            },
            "previs_v1_rework": {
                "test_frames": "progress/04_白模预演/shot20_测试帧_v1/",
                "verdict": "rejected（不进入全渲）",
                "issues": [
                    "把 shot19 的绝对手部世界坐标误当成「相对站位偏移」，体侧目标被算到 (loc-0.78, loc+0.78)，距人约 1.1m；起身/走路/收手段求解器误差 0.87–1.77m，手臂被甩到画面外",
                    "f53–f80 走路段目标误写成 KNOB，人还在走手就去够旋钮",
                    "耳朵目标写死 (1.301,0.726,1.483)，比实测 Head 骨骼 z=1.28 高 0.2m，f168 原分辨率里话筒举在头顶上方而不是贴耳",
                    "电话被镂空椅背挡住，f001 首帧看不见；白模整体过亮，人物与墙地对比不足",
                    "蒸汽太细太淡，缩略图里几乎看不出「多 → 淡」的变化",
                ],
                "fixes": [
                    "删除固定 RETREAT_PT；每帧先 apply 体侧角度、实测 rest_pt 作世界空间插值基准，非贴点段直接锁角度不求解",
                    "走路段（f1–f80）锁体侧角度；关火/伸手/拿起三段才求解",
                    "耳朵目标改由 Head 骨骼当帧坐标 + (0.13,-0.02,0.10) 推导",
                    "椅子左移到 (0.55,0.88)、电话移到桌面近中 (1.118,1.120) 并放大加深到 0.08 灰度；人物 matte 0.82→0.68",
                    "蒸汽加粗到 r=0.032 / h=0.42 并调暗；相机拉近到 lens 34",
                ],
            },
            "previs_v2_rework": {
                "test_frames": "progress/04_白模预演/shot20_测试帧_v2/",
                "verdict": "rejected（局部残留，不进入全渲）",
                "issues": [
                    "Walk_Loop（animation_2）带 root motion，Hips 位移把上半身整体推走 0.6–1.3m：f080 体侧手在 y=3.009（站位 2.30）、f128 在 y=2.217（站位 0.90），手几乎插进后墙",
                    "root motion 让 f117–f128 插值起点失效，f128 手距桌面电话 0.7773m，没抓到电话",
                    "贴耳动态段 f140 误差 0.1626m、f152 0.0808m，收敛偏慢",
                ],
                "fixes": [
                    "新增 strip_hips_motion()：只剥 Walk_Loop 的 Hips location/rotation_quaternion 共 7 条通道（腿部保留、Sitting_Enter 不剥，起身仍需骨盆升降）",
                    "EAR_REL z 0.10→0.07；动态段求解 6 轮→7 轮",
                ],
            },
            "previs_v3_rework": {
                "test_frames": "progress/04_白模预演/shot20_测试帧_v3/",
                "verdict": "rejected（话筒位置残留，不进入全渲）",
                "passed": "f128 手准确抓到电话（误差 0.0317m）、f168/f192 贴耳误差 0.0269/0.0085m，走路段不再甩臂",
                "issues": [
                    "f152 原分辨率确认：0.30m 长的话筒被 root 旋转 55° 竖起来，加上求解器 overshoot 0.109m，视觉上明显举在头顶上方而不是贴耳",
                    "f001 深色电话虽在桌面上，但尺寸偏小、被白色环境冲淡，前态不够醒目（§5.21）",
                ],
                "fixes": [
                    "root 旋转 55°→18°（话筒近横放贴耳，不再翘到头顶）",
                    "抬升段 23 帧→17 帧，f147 起目标固定，给求解器 6 帧收敛到稳态",
                    "EAR_REL z 0.07→0.04，手握点更贴近 Head 高度",
                    "电话机身再放大到 0.30×0.15×0.080、听筒两端加粗",
                ],
            },
            "previs_v4_rework": {
                "test_frames": "progress/04_白模预演/shot20_测试帧_v4/",
                "verdict": "rejected（动态抬升 overshoot，不进入全渲）",
                "passed": "话筒 root 旋转 55°→18° 近横放，f192 稳态贴耳误差 0.0024m；f128 抓电话 0.0317m、关火段 0.0036/0.0102m 稳定",
                "issues": [
                    "抬升段 23→17 帧后目标变化更快，逐帧坐标下降跟不上：f140 误差 0.2422m、f152 0.1393m，手 z=1.455 比目标 1.316 高 0.139m",
                    "根因是角度空间局部最优：求解器优先把 xy 对齐，z 收不下来；f168 仍 0.0566m",
                ],
                "fixes": "v5 尝试主循环外预计算 EAR_LOCK 并 ease 渐混锁定（失败，见下条）",
            },
            "previs_v5_rework": {
                "test_frames": "progress/04_白模预演/shot20_测试帧_v5/",
                "verdict": "rejected（EAR_LOCK 自身误差 0.1225m，不进入全渲）",
                "issues": [
                    "主循环外预计算的 EAR_LOCK angles=[0.4,144.4,0,-90.0]、err=0.1225m，ForeArm 卡在 fb=-90° 边界的局部最优",
                    "f145 起把逐帧解渐混到 EAR_LOCK、f153 起完全锁定，等于把 v4 已收敛的解（f192 0.0024m）拉回失准静态角度：f152/f168/f192 手 z 稳定高出目标 0.122m",
                    "根因复核：EAR_LOCK 在 frame_set(1) 静态 Idle 姿态求得，主循环每帧 Idle 重心与 Spine 传导都不同——§5.20 的老坑；shot19 v3『首尾锁回实测角度』只适用于同一帧姿态，不能跨帧复用",
                ],
                "fixes": "v6 取消 EAR_LOCK 整段预计算，回到逐帧求解并做三点加强（见下条）",
            },
            "previs_v6_rework": {
                "verdict": "修复版；测试帧与全渲审查见 progress/04_白模预演/shot20_预演审查/",
                "fixes": [
                    "solve_right 改多起点：动态段四起点（上一帧解 + 分段 anchor + 探针 ear 解 + 探针 best_start (-20,150,0,-40)），全部在当前帧骨骼状态下实测误差，取全局最小分支",
                    "抬升段目标轨迹拆成『xy 先到位 13 帧、z 晚 5 帧起步再抬 18 帧』两段 ease，不再同时被 y/z 拉扯",
                    "稳态 f153–f192 用上一帧解三起点微调，误差 >0.03m 自动 12 轮 / 26° 高精度重求兜底",
                    "保留 v4 已验证的外观修复：root 18° 近横放、机身 0.30×0.15×0.080、EAR_REL z=0.04、椅子左移、蒸汽加粗",
                ],
            },
            "previs_v7_rework": {
                "test_frames": "progress/04_白模预演/shot20_测试帧_v7/",
                "verdict": "动作链数值 pass；画面可读性 rejected（进入 v8 纯场景层优化）",
                "numeric": "f128 0.0317m / f140 0.0611m / f152 0.0286m / f168 0.0013m / f192 0.0011m，全部关键帧 <0.062m；f152/f168/f192 原分辨率确认话筒贴右耳侧、不再浮在头顶上方",
                "issues": [
                    "整体过亮，白墙白地白桌与 0.68 灰度人物几乎黏在一起，深色电话与蒸汽读不清",
                    "f001 桌面电话被浅色桌布与椅背竖杆吃掉，前态不够醒目（§5.21）",
                    "椅背装在 py+0.20（人物朝 +y，等于装在身前），f001 挡躯干、f152/f192 挡桌面与下半身",
                ],
                "fixes": "动态段补误差兜底重求（9 轮/20° → >0.035 时 14 轮/30° → >0.05 时 14 轮/12°），v6 的 0.1970/0.1302m 降到 0.0611/0.0286m",
            },
            "previs_v8_rework": {
                "verdict": "可读性修正版，动画与求解器逐字未改；数值应与 v7 完全一致",
                "fixes": [
                    "椅背 py+0.20 → py-0.20，改到人物背后，不再遮挡躯干与桌面",
                    "人物 matte 0.68→0.50、桌布 0.88→0.74、桌面 0.62→0.55，拉开层次",
                    "fill 光 170→115、world strength 0.86→0.74，整体压暗提对比",
                    "蒸汽去 emission 改 0.36 中灰并加粗 r=0.038，前态三缕清晰可见",
                    "话筒机身 0.30×0.15×0.080 → 0.34×0.17×0.085、两端 0.065×0.140×0.055",
                    "人物全程偏背/侧对相机，下半身被桌椅挡住；不强行改机位以免牵动整条走位，H3 由 ref_image 锁脸",
                ],
            },
            "timeline": {
                "f1-32": "前态：挂断电话后独坐，头微低；电话在桌面手边、灶上盖锅被蒸汽顶得轻颤、三缕蒸汽明显、火大",
                "f33-52": "Sitting_Enter 反放缓缓起身，站位从椅位 ease 前移到 (0.75,0.72)，无硬切",
                "f53-80": "沿桌子西侧绕行到灶前，Walk_Loop + 路径切线朝向，起步/到站用 blend_rot 渐转",
                "f81-104": "核心动作 A：右手贴旋钮拧小，旋钮转 60°、火焰渐矮、锅盖颤动渐停、蒸汽 ease 变淡",
                "f105-116": "右手从旋钮 ease 收回身侧",
                "f117-128": "回身走回桌边，右手渐伸向桌面电话",
                "f129-152": "核心动作 B：话筒由右手骨骼驱动，离桌→沿弧线抬到耳边；f137-148 左手做拨号点按",
                "f153-192": "后态：话筒贴耳，头微侧、很轻的笑，轻声问『妈，你晚上吃什么』；锅仍在灶上只有一丝蒸汽，镜头微推",
            },
            "three_state": {
                "phone": "桌面手边（横放）→ 被右手抓起、ease 抬升并转 18° 近横放 → 贴耳静止；全程同一部电话、不消失不换形不漂浮",
                "fire": "火大、锅盖轻颤、蒸汽明显 → 旋钮渐转、火焰渐矮、颤动渐停、蒸汽渐短 → 火小、锅盖稳、只剩一丝蒸汽",
                "body": "坐姿独处 → 起身 → 绕桌走到灶前 → 站定关火 → 回身走到桌边 → 站定贴耳说话",
            },
            "hard_constraints": "脚贴地；单人镜头；电话 f1–f192 全程存在且形状恒定；锅与锅盖始终在灶上、只改蒸汽与火焰；桌椅窗灶搁板全程同位；段间全 ease 渐变；椅背与搁架用镂空细杆不做实心大方板；192 帧一次性全渲保证逐帧求解器 seed 连续",
            "non_blocking": [
                "起身用 Sitting_Enter 反放（Blender 5.2 NlaStrip.use_reverse=True 已由探针确认），站→坐动作倒放为坐→站，腿部姿态连续",
                "脚高用站姿 Idle 实测 dz=0.7188m；坐姿段小腿被桌子与椅面遮挡，与 shot19 同口径",
                "拨号只用左手小幅点按示意，参考视频重点给出『话筒离桌→贴耳』的位移拓扑，按键细节交给 prompt",
            ],
        }
        with open(os.path.join(OUT_DIR, "previs20_report.json"), "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS20_DONE", flush=True)


if __name__ == "__main__":
    main()
