# -*- coding: utf-8 -*-
"""白模预演：shot22「阳台择豆角」（剧本六 L339-351，方案 §3 §4，P0）。

场景 E11 阳台。E11_v01.png 已目检：窄阳台 / 左侧防盗格栅与邻楼绿树 /
头顶横跨竹竿 / 右侧窗台（绿植 + 白布 + 搪瓷盆）/ 两把并排小木凳 /
左前地面一篮绿豆角 / 墙面与地面春日斜光斑；画风水彩同族、无人物。
白模补出参考图里没有的「两人并排坐姿 + 膝前工作区 + 连续移动的阳光」。

双人坐姿（tmp_qc/probe_shot22_v3.py 定稿，all_reachable=True）：
  C11 妈妈·老年   站位 (-0.38,0.65)，clip 4 Sitting_Idle_Loop，朝 -y 正对相机
  C06b 许宁·中老年 站位 ( 0.38,0.65)，clip 4 Sitting_Idle_Loop，朝 -y 正对相机
  脚高用站姿 clip 1 Idle 实测 dz_xu=0.7188 / dz_mom=0.7132（§5.14）；
  坐姿 clip 的 Hips 位移实测 0，无需 strip_hips_motion（shot20 C4 坑）。

核心叙事（台账 risk_note ②）与动作分工：
  妈妈右手   全程静止捏着「一截没掐断的豆角」(-0.46,0.48,0.66)，
             那截豆角逐帧挂在 RightHand 骨骼上、位置不动、不掉落；
             头 f001 已微垂 10°，f001–f024 ease 到 28° 睡着，f163–f192 ease 抬起醒来
  许宁左手   独立完成 6 根豆角的「篮口 → 抬高短弧线 → 小盆」整条物理链，
             v2 探针证伪了让右手放盆（误差 0.0766m），故左手包办
  许宁右手   全程膝前轻扶 (0.34,0.60,0.56)，极小周期起伏
  妈妈左手   每帧 apply RETREAT_L 后实测当帧 rest_pt（§5.20），不设绝对坐标
  两人工作区相隔 0.924m，许宁的手全程不进入妈妈手部区域（避免被读成「拿走」）

时间轴（192f / 8s，关键变化前置 §5.21）：
  f001       前态：两人并排坐好；妈妈手里那截亮绿豆角够大够清晰（唯一高饱和彩色）；
             篮里 6 根亮绿豆角冒尖；许宁左手已在篮口；阳光在画面左侧
  f001–f024  妈妈头慢慢垂下睡着（唯一关键状态变化，前置到前 1 秒）；
             第 1 根豆角 f009–f024 完成 篮→手→盆
  f030–f134  其余 5 根逐根沿短弧线从篮到盆，盆里逐渐堆起
  f135–f162  篮空、盆满；许宁左手 ease 收回体侧，两人安静坐着；阳光持续右移
  f163–f192  妈妈慢慢抬头醒来，许宁侧头看她并把空篮轻轻挪开一点；
             那截豆角仍在妈妈手里，门/格栅/竹竿/窗台全程同位

物理链六项（方法论 §4.2）：① 首帧可见且够大 ② 有前态 ③ 从篮到盆的连续位移
④ 道具由手骨骼驱动 ⑤ 有后态（篮空盆满） ⑥ 关键变化在 f001–f024 内。

已知坑全部规避：
  §5.14 按 clip 序号名称取 action、脚高用站姿 Idle 实测
  §5.15 圆柱横放绕 X 转 90°；柔光一律用移动光源，不做几何光斑板
  §5.16 build_room() 末尾补 view_layer.update()
  §5.17 凳子/格栅用镂空细杆，不做正对相机的实心大方板
  §5.19 核心道具完整物理链；豆角挂左手骨骼、妈妈那截挂右手骨骼
  §5.20 手 K 一律在当帧骨骼状态下逐帧坐标下降求解，静态角度只作多起点之一
  §5.21 关键变化前置、道具首帧画幅与对比度足够（纯 Emission 亮绿 + Standard）
  §5.22 多起点 + 误差兜底重求，取消任何跨帧静态锁角
  第 23 条 双人镜头先扫可达包络再定左右手分工（v2 判退稿已归档）

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot22.py
  blender.exe --background --python tools/previs_shot22.py   （192 帧一次性全渲）
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
FRAMES_DIR = os.path.join(OUT_DIR, "frames22")
PROBE_JSON = os.path.join(ROOT, "tmp_qc", "shot22_probe_v3.json")
REPORT_JSON = os.path.join(OUT_DIR, "previs22_report.json")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720
CAM_LENS = 35                       # v2 拉近一档，放大人物画幅
CAM_START = (0.00, -2.62, 1.40)
CAM_END = (-0.05, -2.50, 1.38)
AIM = Vector((0.00, 0.62, 0.84))

# ---------------------------------------------------------------- 布局（v3 探针实测）
MOM_LOC = (-0.38, 0.65)
XU_LOC = (0.38, 0.65)
YAW_DEG = 0.0
STOOL_TOP_Z = 0.45

BASKET_CENTER = (0.72, 0.50, 0.56)     # 篮口中心（Empty 原点）
BOWL_CENTER = (0.46, 0.52, 0.56)       # 盆口中心（Empty 原点）
BASKET_DOCK = (0.90, 0.42, 0.56)       # f163+ 许宁把空篮轻轻挪开

BASKET_PICK = (0.72, 0.50, 0.58)       # 许宁左手取豆点（v3 err 0.0446）
ARC_MID = (0.59, 0.51, 0.68)           # 弧线中点（v3 err 0.0178）
BOWL_DROP = (0.46, 0.52, 0.58)         # 许宁左手放盆点（v3 err 0.0245）
XU_RIGHT_REST = (0.34, 0.60, 0.56)     # 许宁右手膝前轻扶（v3 err 0.0165）
XU_LEFT_REST = (0.74, 0.58, 0.54)      # 许宁左手末段收回（v3 err 0.0195）
MOM_BEAN = (-0.46, 0.48, 0.66)         # 妈妈右手静止持豆角（v3 err 0.0029）

# 6 根豆角的「篮→手→盆」窗口；第 1 根落在 f009–f024 内（关键变化前置）
BEAN_WINDOWS = [(9, 24), (30, 46), (52, 68), (74, 90), (96, 112), (118, 134)]

# 阳台空间（参考图布局家族）
WALL_Y = 2.20
GRILLE_X = -1.35
WIN_X0, WIN_X1 = 0.35, 1.55
WIN_Z0, WIN_Z1 = 1.15, 2.30

BONES = ("mixamorig:RightArm", "mixamorig:RightForeArm",
         "mixamorig:LeftArm", "mixamorig:LeftForeArm",
         "mixamorig:Head", "mixamorig:Neck",
         "mixamorig:Spine", "mixamorig:Spine1")

RETREAT_R = (-45.0, -132.1, 0.0, 56.6)
RETREAT_L = (-45.0, 132.1, 0.0, -56.6)

# 篮内 / 盆内豆角的局部堆叠（相对各自 Empty 原点）
# v3：z 分三层 + xy 散开更开，让篮里/盆里的 6 根豆角成为「有层次的一小堆」，
# 不再全部平行横在同一高度糊成一块绿色板（v2 判定书）
LOCAL_IN_BASKET = [
    (-0.078, -0.048, 0.012), (0.072, -0.042, 0.012),
    (-0.068, 0.052, 0.026), (0.076, 0.046, 0.026),
    (-0.018, -0.012, 0.055), (0.022, 0.016, 0.070),
]
LOCAL_IN_BOWL = [
    (-0.060, -0.030, 0.012), (0.058, -0.028, 0.012),
    (-0.055, 0.032, 0.026), (0.060, 0.030, 0.026),
    (-0.010, 0.000, 0.058), (0.015, 0.005, 0.072),
]


def mat(key, shade, emission=None):
    return p14.mat("s22_" + key, shade, emission)


def emission_mat(name, color, strength):
    """纯自发光材质：Standard 色彩管理下保持高饱和，不被灯光冲淡（shot21 v3）。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def add_torus(name, loc, major, minor, m):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=24, minor_segments=6,
                                     location=loc)
    o = bpy.context.active_object
    o.name = name
    if m is not None:
        o.data.materials.append(m)
    return o


def add_stool(name, px, py):
    """小木凳：凳面 + 四条细腿 + 一根横撑，镂空不做实心板（§5.17）。"""
    w = mat("stool", 0.38)
    p14.add_box(f"{name}_seat", (px, py, STOOL_TOP_Z), (0.42, 0.38, 0.045), w)
    for dx in (-0.16, 0.16):
        for dy in (-0.13, 0.13):
            p14.add_box(f"{name}_leg_{dx}_{dy}",
                        (px + dx, py + dy, STOOL_TOP_Z / 2),
                        (0.035, 0.035, STOOL_TOP_Z), w)
    p14.add_box(f"{name}_rail", (px, py - 0.13, 0.16), (0.34, 0.025, 0.025),
                mat("stoolrail", 0.30))


def build_room():
    """E11 阳台：窄地面 / 后墙与窗 / 右侧窗台 / 左侧防盗格栅 / 头顶竹竿 / 两凳。"""
    # v2 整体压暗一档：v1 中段移动主光移到画面中央时背景过曝成纯白，
    # 右侧人物被白光吃掉（shot21 v2 / shot20 v8 同类问题）
    wall = mat("wall", 0.36)
    p14.add_box("floor", (0, 0, -0.05), (7.0, 8.0, 0.10), mat("floor", 0.26))
    p14.add_box("ceiling", (0, 0, 2.70), (7.0, 8.0, 0.10), mat("ceil", 0.34))
    # 两侧深灰墙（参考图画面左右的边框），只做到 y=0.2，不挡人物
    p14.add_box("side_wall_l", (-1.75, 1.10, 1.35), (0.12, 2.2, 2.70), wall)
    p14.add_box("side_wall_r", (1.75, 1.10, 1.35), (0.12, 2.2, 2.70), wall)
    # 后墙留窗
    p14.add_box("wall_back_l", ((-1.75 + WIN_X0) / 2, WALL_Y, 1.35),
                (WIN_X0 + 1.75, 0.12, 2.70), wall)
    p14.add_box("wall_back_r", ((WIN_X1 + 1.75) / 2, WALL_Y, 1.35),
                (1.75 - WIN_X1, 0.12, 2.70), wall)
    p14.add_box("wall_back_top", ((WIN_X0 + WIN_X1) / 2, WALL_Y, (WIN_Z1 + 2.70) / 2),
                (WIN_X1 - WIN_X0, 0.12, 2.70 - WIN_Z1), wall)
    p14.add_box("wall_back_bot", ((WIN_X0 + WIN_X1) / 2, WALL_Y, WIN_Z0 / 2),
                (WIN_X1 - WIN_X0, 0.12, WIN_Z0), wall)
    frame = mat("winframe", 0.32)
    wx, wz = (WIN_X0 + WIN_X1) / 2, (WIN_Z0 + WIN_Z1) / 2
    for nm, px in (("win_l", WIN_X0), ("win_r", WIN_X1), ("win_m", wx)):
        p14.add_box(nm, (px, WALL_Y - 0.04, wz),
                    (0.05, 0.07, WIN_Z1 - WIN_Z0), frame)
    for nm, pz in (("win_t", WIN_Z1), ("win_b", WIN_Z0)):
        p14.add_box(nm, (wx, WALL_Y - 0.04, pz),
                    (WIN_X1 - WIN_X0 + 0.08, 0.07, 0.05), frame)
    # v2：窗外自发光板是 v1 过曝主因之一，大幅压暗到冷灰蓝
    p14.add_box("daylight", (wx, WALL_Y + 2.5, 1.75), (6.0, 0.10, 3.4),
                mat("daylight", 0.32, emission=(0.26, 0.30, 0.36, 1.0)))

    # 右侧窗台与台上小物（绿植 / 白布 / 搪瓷盆），压在窗下不挡人
    sill = mat("sill", 0.44)
    p14.add_box("sill", (wx, WALL_Y - 0.22, 1.03), (1.40, 0.32, 0.055), sill)
    p14.add_cyl("sill_pot", (WIN_X0 + 0.24, WALL_Y - 0.22, 1.13),
                0.085, 0.16, mat("pot", 0.36))
    for k in range(5):
        a = 2 * math.pi * k / 5
        p14.add_cyl(f"pot_leaf_{k}",
                    (WIN_X0 + 0.24 + 0.06 * math.cos(a),
                     WALL_Y - 0.22 + 0.06 * math.sin(a), 1.28),
                    0.018, 0.16, mat("leaf", 0.40),
                    rot=(math.radians(26), 0, math.radians(30 * k)))
    p14.add_box("sill_cloth", (wx + 0.08, WALL_Y - 0.24, 1.065),
                (0.30, 0.16, 0.018), mat("cloth", 0.60))
    p14.add_cyl("sill_basin", (WIN_X1 - 0.22, WALL_Y - 0.22, 1.09),
                0.10, 0.075, mat("basin", 0.56))

    # 左侧防盗格栅：竖细杆 + 上下横杆，镂空不挡人（§5.17）
    gr = mat("grille", 0.28)
    for k in range(7):
        p14.add_cyl(f"grille_bar_{k}",
                    (GRILLE_X, 0.30 + 0.30 * k, 0.85),
                    0.014, 1.60, gr)
    for z in (0.06, 1.62):
        p14.add_cyl(f"grille_rail_{z}", (GRILLE_X, 1.20, z),
                    0.016, 1.90, gr, rot=(math.radians(90), 0, 0))
    p14.add_box("grille_sill", (GRILLE_X, 1.20, 0.04),
                (0.14, 1.90, 0.08), mat("grillebase", 0.34))

    # 头顶横跨竹竿 + 两只小夹子
    p14.add_cyl("bamboo_pole", (0.00, 1.35, 2.18), 0.028, 2.70,
                mat("bamboo", 0.50), rot=(0, math.radians(90), 0))
    for px in (-0.62, 0.58):
        p14.add_box(f"pole_peg_{px}", (px, 1.35, 2.18),
                    (0.035, 0.035, 0.10), mat("peg", 0.30))

    add_stool("stool_mom", *MOM_LOC)
    add_stool("stool_xu", *XU_LOC)

    # §5.16：强制刷新依赖图，最后创建的几何体 dimensions 才会生效
    bpy.context.view_layer.update()


def build_basket():
    """竹篮：Empty 原点=篮口中心；12 根镂空竖杆 + 底盘 + 口沿圆环。"""
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=BASKET_CENTER)
    root = bpy.context.active_object
    root.name = "basket_root"
    rib = mat("basket", 0.24)
    edge = mat("basketrim", 0.16)

    def piece(name, loc, dims, m):
        o = p14.add_box(name, loc, dims, m)
        o.parent = root
        return o

    for k in range(12):
        a = 2 * math.pi * k / 12
        o = p14.add_cyl(f"basket_rib_{k}",
                        (0.125 * math.cos(a), 0.125 * math.sin(a), -0.085),
                        0.008, 0.17, rib)
        o.parent = root
    p14.add_cyl("basket_bottom", (0, 0, -0.175), 0.125, 0.015, rib).parent = root
    add_torus("basket_rim", (0, 0, 0.0), 0.125, 0.010, edge).parent = root
    add_torus("basket_mid", (0, 0, -0.095), 0.124, 0.007, rib).parent = root
    piece("basket_handle_l", (-0.125, 0, 0.045), (0.020, 0.020, 0.10), edge)
    piece("basket_handle_r", (0.125, 0, 0.045), (0.020, 0.020, 0.10), edge)
    bpy.context.view_layer.update()
    return root


def build_bowl():
    """膝前小搪瓷盆：Empty 原点=盆口中心；浅盆身 + 亮口沿。"""
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=BOWL_CENTER)
    root = bpy.context.active_object
    root.name = "bowl_root"
    body = mat("bowl", 0.48)
    rim = mat("bowlrim", 0.62)
    p14.add_cyl("bowl_body", (0, 0, -0.055), 0.105, 0.10, body).parent = root
    p14.add_cyl("bowl_inside", (0, 0, -0.006), 0.095, 0.012,
                mat("bowlinner", 0.34)).parent = root
    add_torus("bowl_rim", (0, 0, 0.0), 0.105, 0.009, rim).parent = root
    bpy.context.view_layer.update()
    return root


def build_beans():
    """6 根亮绿豆角 + 妈妈手里那截（更大更亮，全程不掉落）。"""
    # v2：v1 的 1.25/1.55 强 Emission 把饱和绿冲成荧光黄白 → 降饱和降强度。
    # v3：6 根绕 X 68+9*i / 绕 Z 12+11*i，朝向各异且带 z 分量、投影缩短，
    #     不再平行横放跨越盆沿与篮沿；手里那截斜向上 38° 保持不变。
    gm = emission_mat("s22_bean_em", (0.24, 0.70, 0.16), 0.80)
    hm = emission_mat("s22_held_bean_em", (0.30, 0.85, 0.10), 0.95)
    beans = []
    for i in range(6):
        o = p14.add_cyl(f"bean_{i}", (0, 0, 0), 0.017, 0.20, gm,
                        rot=(math.radians(68 + 9 * i), 0,
                             math.radians(12 + 11 * i)))
        beans.append(o)
    held = p14.add_cyl("mom_held_bean", (0, 0, 0), 0.026, 0.34, hm,
                       rot=(math.radians(62), 0, math.radians(38)))
    return beans, held


def add_lighting():
    """春日斜光：一盏缓慢右移的暖 AREA 主光 + 一盏膝前 POINT 光 + 冷色常亮 fill。

    光影移动全靠真实光源，不做几何光斑板（§5.15 D5 会把板片读成「一块板子长出来」）。
    """
    world = bpy.data.worlds.new("previz_world22")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.20, 0.22, 0.26, 1.0)
            n.inputs[1].default_value = 0.38
    bpy.context.scene.world = world

    bpy.ops.object.light_add(type="AREA", location=(-1.55, 0.80, 2.20))
    sun = bpy.context.active_object
    sun.name = "moving_sun_key"
    sun.data.energy = 150
    sun.data.size = 1.20
    sun.data.color = (1.00, 0.87, 0.66)
    sun.rotation_euler = (math.radians(52), math.radians(-18), 0)

    bpy.ops.object.light_add(type="POINT", location=(-0.95, 0.10, 0.90))
    knee = bpy.context.active_object
    knee.name = "moving_knee_light"
    knee.data.energy = 18
    knee.data.shadow_soft_size = 0.45
    knee.data.color = (1.00, 0.90, 0.70)

    bpy.ops.object.light_add(type="AREA", location=(0.90, -1.20, 2.30))
    fill = bpy.context.active_object
    fill.name = "cool_fill"
    fill.data.energy = 60
    fill.data.size = 2.60
    fill.data.color = (0.72, 0.80, 1.00)
    fill.rotation_euler = (math.radians(28), 0, 0)
    return sun, knee


def act_by_clip(acts, n):
    target = f"animation_{n}"
    for a in acts:
        if a.name.split(".")[0] == target:
            return a
    raise RuntimeError(f"找不到 {target}，现有 {[a.name for a in acts]}")


def apply_arm(arm, side, ax, ay, az, fb):
    p14.rotate_ops(arm, f"mixamorig:{side}Arm", [
        ((0, 1, 0), ay), ((1, 0, 0), ax), ((0, 0, 1), az),
    ])
    p14.rotate_ops(arm, f"mixamorig:{side}ForeArm", [((0, 1, 0), fb)])


def hand_world(arm, side):
    bpy.context.view_layer.update()
    w = arm.matrix_world @ arm.pose.bones[f"mixamorig:{side}Hand"].matrix.translation
    return (w.x, w.y, w.z)


def head_pose(arm, down, turn):
    """只动 Head/Neck，不动 Spine，避免上身旋转传导到手臂（§5.20）。"""
    p14.rotate_ops(arm, "mixamorig:Head", [
        ((1, 0, 0), down), ((0, 0, 1), turn * 0.55),
    ])
    p14.rotate_world(arm, "mixamorig:Neck", (0, 0, 1), turn * 0.6)


def lerp3(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def solve_arm(arm, side, target, seeds, iters=6, step=20.0):
    """每帧、当帧骨骼状态下的多起点坐标下降（§5.20 / §5.22）。"""
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
                apply_arm(arm, side, *c)
                scored.append((math.dist(hand_world(arm, side), target), c))
            _, cur = min(scored, key=lambda x: x[0])
            s *= 0.6
        apply_arm(arm, side, *cur)
        e = math.dist(hand_world(arm, side), target)
        if best is None or e < best[0]:
            best = (e, tuple(cur))
    apply_arm(arm, side, *best[1])
    return best[1], best[0]


def solve_with_fallback(arm, side, target, seeds):
    """误差兜底重求：超阈换大步长跳出局部最优，仍超阈再细修（shot20 v7）。"""
    solved, err = solve_arm(arm, side, target, seeds, iters=6, step=20.0)
    if err > 0.045:
        solved, err = solve_arm(arm, side, target,
                                [solved] + seeds[:2], iters=12, step=30.0)
    if err > 0.06:
        solved, err = solve_arm(arm, side, target,
                                [solved] + seeds[:2], iters=12, step=12.0)
    return solved, err


def xu_left_target(f):
    """许宁左手：每根窗口内 篮口 → 抬高短弧线 → 盆口；窗口间 ease 回篮口。

    窗口内 z 额外加 0.10*sin(pi*k)，让豆角走一条高于篮沿/盆沿的弧线，
    中途不被膝盖与凳面遮住（shot21 v3 同类修复）。
    """
    if f < BEAN_WINDOWS[0][0]:
        return BASKET_PICK
    for i, (s, e) in enumerate(BEAN_WINDOWS):
        if s <= f <= e:
            k = p14.ease((f - s) / (e - s))
            p = lerp3(BASKET_PICK, BOWL_DROP, k)
            return (p[0], p[1], p[2] + 0.10 * math.sin(math.pi * k))
        if f > e:
            nxt = BEAN_WINDOWS[i + 1][0] if i + 1 < len(BEAN_WINDOWS) else None
            if nxt is None:
                k = p14.ease((f - e) / 18.0)
                return lerp3(BOWL_DROP, XU_LEFT_REST, k)
            if f < nxt:
                return lerp3(BOWL_DROP, BASKET_PICK, p14.ease((f - e) / (nxt - e)))
    return BASKET_PICK


def bean_pos(i, f, hand_l, basket_w, bowl_w):
    """豆角 i 的世界坐标：篮里 → 挂左手 → 盆里；段间 3 帧 ease，零跳变。"""
    s, e = BEAN_WINDOWS[i]
    start = tuple(basket_w @ Vector(LOCAL_IN_BASKET[i]))
    end = tuple(bowl_w @ Vector(LOCAL_IN_BOWL[i]))
    hp = (hand_l[0], hand_l[1] - 0.005, hand_l[2] + 0.012)
    if f < s:
        return start
    if f < s + 3:
        return lerp3(start, hp, p14.ease((f - s) / 3.0))
    if f <= e - 3:
        return hp
    if f <= e:
        return lerp3(hp, end, p14.ease((f - (e - 3)) / 3.0))
    return end


def mom_head_down(f):
    if f <= 24:
        return 10.0 + 18.0 * p14.ease((f - 1) / 23.0)
    if f <= 162:
        return 28.0
    # v2：抬头幅度加大到 2°，让 f192 的「醒来」在联系表上也读得出
    return 28.0 - 26.0 * p14.ease((f - 163) / 29.0)


def xu_head(f):
    if f <= 12:
        return 3.0, -9.0
    if f <= 162:
        return 10.0, 2.0
    return 4.0, -8.0


def main():
    with open(PROBE_JSON, encoding="utf-8") as fh:
        probe = json.load(fh)
    assert probe.get("all_reachable") and probe.get("probe_version") == "v3_final", \
        "定稿探针未全绿，先修布局再跑预演"
    sol = probe["solutions"]
    ANG = {k: tuple(v["angles"]) for k, v in sol.items()}
    REC = probe["recommended"]
    print("[previs22] anchors", {k: [round(v, 1) for v in a] for k, a in ANG.items()},
          flush=True)
    print("[previs22] separation", probe["workspace_separation_m"], flush=True)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    build_room()
    basket_root = build_basket()
    bowl_root = build_bowl()
    beans, held_bean = build_beans()
    sun, knee = add_lighting()

    xu, x_acts, _ = p14.import_glb(os.path.join(MODELS, "C06b", "tex_mesh_animated.glb"))
    mom, m_acts, _ = p14.import_glb(os.path.join(MODELS, "C11", "tex_mesh_animated.glb"))
    print("[previs22] xu_acts", len(x_acts), "mom_acts", len(m_acts), flush=True)
    if len(x_acts) < 5 or len(m_acts) < 5:
        raise RuntimeError("C06b / C11 都应有 10 个动作 clip")

    x_idle, m_idle = act_by_clip(x_acts, 1), act_by_clip(m_acts, 1)
    x_sit, m_sit = act_by_clip(x_acts, 4), act_by_clip(m_acts, 4)
    for a in (x_idle, m_idle, x_sit, m_sit):
        p14.make_loop(a)
    # 坐姿 clip 的手臂/头/脊柱旋转通道必须剥掉，否则 depsgraph 重评估覆盖手 K
    removed = p14.strip_channels([x_sit, m_sit], BONES)
    print("[previs22] sit clips", x_sit.name, m_sit.name,
          "| stripped", len(removed), "channels", flush=True)

    scene = bpy.context.scene
    p14.set_loop(xu.animation_data, x_idle, {"key": None}, "idle_probe")
    p14.set_loop(mom.animation_data, m_idle, {"key": None}, "idle_probe")
    xu.rotation_mode = "XYZ"
    mom.rotation_mode = "XYZ"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    dz_x = -p14.feet_z(xu) + 0.02
    dz_m = -p14.feet_z(mom) + 0.02
    print(f"[previs22] feet dz xu={dz_x:.4f} mom={dz_m:.4f}", flush=True)
    assert abs(dz_x - probe["dz"]["xu"]) < 0.01 and abs(dz_m - probe["dz"]["mom"]) < 0.01

    p14.set_loop(xu.animation_data, x_sit, {"key": None}, "sit")
    p14.set_loop(mom.animation_data, m_sit, {"key": None}, "sit")

    # 角色统一哑光，场景/道具保留 s22_ 前缀材质
    char_matte = p14.make_matte("char_matte22", 0.34)
    for o in [o for o in scene.objects if o.type == "MESH"]:
        names = [m.name for m in o.data.materials] if o.data.materials else []
        if any(n.startswith("s22_") for n in names):
            continue
        o.data.materials.clear()
        o.data.materials.append(char_matte)

    scene.render.engine = "BLENDER_EEVEE"
    # 纯 Emission 亮绿在 AgX 下会被压成淡黄绿，切 Standard 保持饱和（shot21 v3）
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = RES_X, RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, N_FRAMES
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    cam_data = bpy.data.cameras.new("previs_cam22")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam22", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    sp, ep = Vector(CAM_START), Vector(CAM_END)

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    if test_mode:
        frames_iter = [1, 8, 16, 24, 32, 44, 56, 72, 88, 104, 120,
                       140, 160, 176, 192]
    elif os.environ.get("PREVIS_RANGE"):
        a, b = os.environ["PREVIS_RANGE"].split("-")
        frames_iter = range(int(a), int(b) + 1)
    else:
        frames_iter = range(1, N_FRAMES + 1)

    seed_xl = ANG["xu_left_basket"]
    seed_xr = ANG["xu_right_rest"]
    seed_mr = ANG["mom_right_bean"]
    max_err, max_err_f = 0.0, 0
    held_samples, sun_samples = [], []

    for f in frames_iter:
        t = (f - 1) / (N_FRAMES - 1)                 # 光照用线性，均匀移动
        tc = p14.ease(t)                              # 相机推镜用 ease
        xu.location = (*XU_LOC, dz_x)
        xu.rotation_euler = (0, 0, math.radians(YAW_DEG))
        mom.location = (*MOM_LOC, dz_m)
        mom.rotation_euler = (0, 0, math.radians(YAW_DEG))
        scene.frame_set(f)
        bpy.context.view_layer.update()

        # ---------- 头：妈妈睡着 → 醒来；许宁侧头看她 → 低头择豆 → 再看她 ----------
        head_pose(mom, mom_head_down(f), -2.0)
        xu_down, xu_turn = xu_head(f)
        head_pose(xu, xu_down, xu_turn)

        # ---------- 体侧基准：每帧先摆回体侧角，实测当帧 rest_pt（§5.20 / C3） ----------
        apply_arm(xu, "Left", *RETREAT_L)
        rest_xl = hand_world(xu, "Left")
        apply_arm(xu, "Right", *RETREAT_R)
        rest_xr = hand_world(xu, "Right")
        apply_arm(mom, "Left", *RETREAT_L)
        rest_ml = hand_world(mom, "Left")
        apply_arm(mom, "Right", *RETREAT_R)
        rest_mr = hand_world(mom, "Right")

        # ---------- 许宁左手：6 根豆角的完整物理链 ----------
        tgt_xl = xu_left_target(f)
        sl, el = solve_with_fallback(xu, "Left", tgt_xl,
                                     [seed_xl, ANG["xu_left_basket"],
                                      ANG["xu_left_mid"], ANG["xu_left_bowl"],
                                      RETREAT_L])
        seed_xl = sl

        # ---------- 许宁右手：膝前轻扶，极小周期起伏 ----------
        wobble = 0.012 * math.sin(2.0 * math.pi * f / 46.0)
        tgt_xr = (XU_RIGHT_REST[0], XU_RIGHT_REST[1],
                  XU_RIGHT_REST[2] + wobble)
        sr, er = solve_with_fallback(xu, "Right", tgt_xr,
                                     [seed_xr, ANG["xu_right_rest"], RETREAT_R])
        seed_xr = sr

        # ---------- 妈妈双手：右手静止持豆角；左手停在当帧体侧实测点 ----------
        mr, emr = solve_with_fallback(mom, "Right", MOM_BEAN,
                                      [seed_mr, ANG["mom_right_bean"], RETREAT_R])
        seed_mr = mr
        apply_arm(mom, "Left", *RETREAT_L)   # 目标即当帧 rest_ml，误差 0
        eml = 0.0
        err = max(el, er, emr, eml)
        if err > max_err:
            max_err, max_err_f = err, f

        # ---------- 妈妈手里那截豆角：逐帧挂 RightHand 骨骼，位置恒定 ----------
        mh = hand_world(mom, "Right")
        held_bean.location = (mh[0] - 0.010, mh[1] - 0.008, mh[2] + 0.020)
        held_samples.append((f, [round(v, 3) for v in held_bean.location]))

        # ---------- 篮子：f163+ 轻轻挪开一点（剧本「许宁把篮子挪开」） ----------
        if f <= 162:
            basket_root.location = BASKET_CENTER
        else:
            basket_root.location = lerp3(BASKET_CENTER, BASKET_DOCK,
                                         p14.ease((f - 163) / 24.0))
        bowl_root.location = BOWL_CENTER
        bpy.context.view_layer.update()
        bw, ow = basket_root.matrix_world, bowl_root.matrix_world

        # ---------- 6 根豆角：篮里 → 挂左手 → 盆里 ----------
        hl = hand_world(xu, "Left")
        bean_world = []
        for i, o in enumerate(beans):
            p = bean_pos(i, f, hl, bw, ow)
            o.location = p
            bean_world.append([round(v, 3) for v in p])
        bpy.context.view_layer.update()

        # ---------- 阳光：两盏光源匀速右移，扫过两人膝盖（无几何光斑板） ----------
        sun.location.x = -1.55 + 3.10 * t
        knee.location.x = -0.95 + 1.90 * t
        knee.location.z = 0.90 + 0.10 * t
        sun_samples.append((f, round(sun.location.x, 3), round(knee.location.x, 3)))

        # ---------- 相机：缓慢推镜 + 极轻手持微晃 ----------
        cam.location = sp.lerp(ep, tc)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (AIM - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        if test_mode:
            print(f"[previs22] f{f:03d} "
                  f"xuL=({hl[0]:.3f},{hl[1]:.3f},{hl[2]:.3f}) "
                  f"momR=({mh[0]:.3f},{mh[1]:.3f},{mh[2]:.3f}) "
                  f"err={err:.4f} b0={bean_world[0]} b5={bean_world[5]} "
                  f"held={[round(v, 3) for v in held_bean.location]} "
                  f"sun_x={sun.location.x:.2f}", flush=True)

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs22] frame {f}/{N_FRAMES}", flush=True)

    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot22", "title": "阳台择豆角", "priority": "P0",
            "source": "剧本六 L339-351 / 方案 §3 §4 / E11_v01.png（目检：水彩阳台，无人物）",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E11 阳台：左侧防盗格栅与邻楼绿树、头顶横跨竹竿、右侧窗台（绿植/白布/搪瓷盆）、两把并排小木凳、右前竹篮与膝前小搪瓷盆；春日斜光由两盏匀速右移的暖光源给出，无几何光斑板",
            "camera": [list(CAM_START), list(CAM_END), list(AIM)],
            "characters": {
                "mom": "C11 妈妈·老年 ten-clip（横版 T-pose 重建版）/ clip 4 Sitting_Idle_Loop",
                "xu": "C06b 许宁·中老年 ten-clip / clip 4 Sitting_Idle_Loop",
                "feet_dz": {"xu": round(dz_x, 4), "mom": round(dz_m, 4)},
                "feet_note": "脚高用站姿 clip 1 Idle 实测（§5.14）；坐姿 clip 的 Hips 位移探针实测 0，无需剥 root motion",
            },
            "probe": {
                "file": "tmp_qc/shot22_probe_v3.json", "version": "v3_final",
                "all_reachable": True,
                "workspace_separation_m": probe["workspace_separation_m"],
                "errors_m": {k: v["error_m"] for k, v in sol.items()},
                "rejected_layouts": [
                    "tmp_qc/shot22_probe_v2.json（右手放盆误差 0.0766m）→ progress/04_白模预演/shot22_探针_v2_判退/",
                    "shot22_probe_v3.json 首版（硬写绝对体侧点 0.1725m）→ progress/04_白模预演/shot22_探针_v3a_判退/",
                ],
                "left_right_split": "v1 扫四手坐姿可达包络；v2 证伪右手放盆；v3 定为许宁左手独立完成篮→盆整条链、右手膝前轻扶、妈妈右手静止持豆角、妈妈左手用当帧 RETREAT 实测体侧点",
            },
            "held_bean": {
                "driver": "逐帧取 mom RightHand 世界坐标 + (-0.010,-0.008,+0.020)",
                "target": list(MOM_BEAN), "radius": 0.026, "length": 0.34,
                "material": "纯 Emission 绿 (0.30,0.85,0.10) 强度 0.95 + Standard 色彩管理；斜向上 38° 读作一截细长豆角",
                "never_falls": True, "never_taken": True, "never_disappears": True,
                "position_constant": True,
                "first_frame_visible_and_large": True,
                "samples": held_samples[::24],
            },
            "beans": {
                "count": 6, "schedule": [list(x) for x in BEAN_WINDOWS],
                "path": "f<s 在篮内局部点；f∈[s,s+3] ease 到左手；f∈[s+3,e-3] 挂左手（手走篮口→抬高 0.10m 弧线→盆口）；f∈[e-3,e] ease 到盆内局部点；f>e 静置盆内",
                "first_window_before_f024": True,
                "basket_empties_by": 134,
                "never_disappear": True,
            },
            "basket": {
                "driver": "f<=162 静止在 BASKET_CENTER；f163–192 ease 挪到 BASKET_DOCK（剧本『许宁把篮子挪开』）",
                "shape": "12 根镂空竖杆 + 底盘 + 两道圆环 + 两只提耳，敞口，不做实心桶",
            },
            "sunlight": {
                "method": "moving_sun_key AREA (x -1.55→+1.55) + moving_knee_light POINT (x -0.95→+0.95) 匀速线性右移 + 冷色常亮 fill；不用几何光斑板",
                "continuous": True, "samples": sun_samples[::24],
            },
            "arm_solver": {
                "method": "三只工作手（许宁左手/许宁右手/妈妈右手）每帧先摆回体侧角实测 rest_pt，再在当前帧骨骼状态下做多起点坐标下降；起点=上一帧解 + 三段探针 anchor + 体侧角；6 轮 / 初始步长 20° / 每轮 ×0.6；误差 >0.045m 换 12 轮 30° 大步长，>0.06m 再换 12 轮 12° 细修（§5.22）。妈妈左手直接用当帧 RETREAT_L 实测体侧点，误差 0",
                "retreat": {"right": list(RETREAT_R), "left": list(RETREAT_L)},
                "max_error_m": round(max_err, 4), "max_error_frame": max_err_f,
            },
            "timeline": {
                "f001": "前态：两人并排坐好；妈妈右手捏着一截亮绿豆角（够大够清晰）；篮里 6 根冒尖；许宁左手已在篮口；阳光在画面左侧",
                "f001-024": "关键变化：妈妈头从 10° ease 垂到 28° 睡着，手与那截豆角完全不动；第 1 根豆角 f009–f024 完成 篮→手→盆（§5.21）",
                "f030-134": "其余 5 根逐根沿抬高 0.10m 短弧线从篮到盆，盆里逐渐堆起",
                "f135-162": "篮空盆满；许宁左手 ease 收回体侧；两人安静坐着；阳光持续右移",
                "f163-192": "后态：妈妈慢慢抬头醒来、许宁侧头看她并把空篮轻轻挪开；那截豆角仍在妈妈手里",
            },
            "three_state": {
                "held_bean": "妈妈手里（f001）→ 全程不动 → 仍在妈妈手里（f192）",
                "basket_beans": "6 根在篮里 → 逐根沿弧线经左手到盆 → 篮空、盆里 6 根",
                "mom_head": "微垂 10° → ease 垂到 28° 睡着 → ease 抬回 5° 醒来",
                "sunlight": "画面左侧 → 匀速右移扫过两人膝盖 → 画面右侧",
            },
            "hard_constraints": "两人始终并排坐在各自小木凳上、脚贴地；双人镜头无第三人；妈妈那截豆角 f001–f192 全程存在、位置恒定、不被任何手触碰；6 根豆角与竹篮、小盆不凭空出现消失；格栅/竹竿/窗台/两凳全程同位；段间全 ease 渐变无硬切；192 帧一次性全渲保证逐帧求解器 seed 连续",
            "physical_chain_checklist": {
                "first_frame_visible_and_large": True,
                "has_before_state": True,
                "continuous_displacement": True,
                "driven_by_hand_bones": True,
                "has_after_state": True,
                "key_change_before_f024": True,
            },
            "previs_v1_rework": {
                "test_frames": "progress/04_白模预演/shot22_测试帧_v1/",
                "verdict": "rejected（不进入全渲），判定书 v1_verdict.json",
                "issues": [
                    "f088–f140 中段过曝：移动主光 + 膝前点光 + fill + world + 窗外自发光板叠加，背景纯白、右侧人物被吃掉",
                    "妈妈手里那截豆角被强 Emission 冲成黄色短块，读不出细长豆角（§5.21）",
                    "6 根豆角过饱和糊成荧光绿横板条，逐根物理链读不出",
                    "人物画幅偏小（约占画高 48%），四周空白过多",
                ],
                "ruled_out": "联系表上疑似「手臂举过头顶/T-pose」经 frame_0120/0192 原分辨率复核排除（G1/G2 缩略图误判），不作返修项",
                "fixes": [
                    "world 0.55→0.38、主光 270→150 且 size 1.70→1.20、膝前点光 42→18、fill 95→60、窗外 daylight emission 压暗",
                    "墙 0.44→0.36 / 地 0.30→0.26 / 顶 0.40→0.34，窗台浅色物件同步压暗",
                    "那截豆角 (0.30,0.85,0.10)/0.95/长 0.34/半径 0.026/斜 38°；6 根 (0.28,0.78,0.16)/0.90/长 0.24/方向分散；篮内盆内散开幅度加大",
                    "相机 y -3.05→-2.62、lens 32→35；妈妈醒来抬头 28°→2°",
                ],
                "scope": "全部集中在场景/灯光/道具材质/机位/头部幅度；豆角时间窗、逐帧求解器、四手分工与探针 anchor 逐字未改（§2.2 分层返修）",
            },
            "previs_v2_rework": {
                "test_frames": "progress/04_白模预演/shot22_测试帧_v2/",
                "verdict": "rejected（画面可读性残留），判定书 v2_verdict.json",
                "passed": "中段过曝消除、人物画幅放大、妈妈那截豆角清晰、睡着→醒来三态可读、竹篮挪开；15 帧误差与 v1 逐字一致，单变量验证成立",
                "issues": [
                    "frame_0192.png 原分辨率：盆里 6 根豆角平行横放、z 高度几乎相同，糊成一块约 120×40px 绿色板，数不出『一根根择完』",
                    "纯 Emission + 长 0.24m + 绕 Z 25*i 使部分豆角轴几乎沿 x，投影过长并跨越盆沿与篮沿",
                ],
                "fixes": [
                    "6 根长度 0.24→0.20、绕 X 68+9*i / 绕 Z 12+11*i 让朝向各异且带 z 分量",
                    "颜色 (0.28,0.78,0.16)→(0.24,0.70,0.16)、强度 0.90→0.80",
                    "篮内/盆内局部落点 z 分三层（0.012 / 0.026 / 0.055–0.072）并加大 xy 散开",
                ],
                "scope": "仅道具层；场景/灯光/机位/动画时间窗/逐帧求解器/妈妈手里那截豆角逐字未改",
            },
            "max_error_m": round(max_err, 4),
            "max_error_frame": max_err_f,
        }
        with open(REPORT_JSON, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("[previs22] max_error", round(max_err, 4), "@ f", max_err_f, flush=True)
        print("[previs22] WROTE", REPORT_JSON, flush=True)
    print("PREVIS22_DONE", flush=True)


if __name__ == "__main__":
    main()
