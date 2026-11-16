# -*- coding: utf-8 -*-
"""白模预演：shot23「地址纸与盒子」（剧本六 L353-359 / 方案 §3 §4，P0）。

场景 E08 朝北小屋书桌。`E08_v01.png` 已目检：北窗带白纱窗帘 / 窗下书桌
（马克杯 + 电热水壶 + 小台灯）/ 桌前木椅 / 左侧单人床与床边书堆 / 墙面斜光斑；
水彩同族、无人物。白模复用 shot12 布局家族。

⚠️ 关键布局决策（见 shot23_探针_v1_布局判退/v1_verdict.json）：
v1 探针证明 C06b 坐姿双手可达 y 下界只有 0.732/0.767，参考图的标准书桌
（桌面 y≈0.50、z≈0.78）整体超出包络 0.33–0.51m。改用 shot22 已过审的
「膝前工作区」：小几顶面 z=0.735、中心 y=0.82，纸/盒子全部落在包络内；
背景另搭 E08 书桌/北窗/床/书堆作空间识别（参考图只锁布局，桌面高度属白模自建）。

双人（tmp_qc/probe_shot23_v2.py 定稿，all_reachable=True）：
  C06b 许宁·中老年  站位 (0.00,0.95)，clip 4 Sitting_Idle_Loop，朝 -y 正对相机
  脚高用站姿 clip 1 Idle 实测 dz_xu=0.7188 / dz_zhou=0.7785（§5.14）；
  坐姿 clip 的 Hips 位移实测 0，无需剥 root motion（shot20 C4 坑）。
  C18 周远·老年     站姿 clip 1 Idle，f001 在门边 (1.15,1.55)，f120–f160 走近

核心叙事（台账 risk_note ②）与动作分工：
  左手  独立完成 抹平 → 折好 → 又展开 → 抬离小几 → 弧线中点 → 盒口
        → 盒内 → 合盖 整条链（v2 探针 9 点误差 0.0020–0.0360m）
  右手  全程轻扶纸左沿 (-0.10,0.82,0.76)，不参与位移，避免两手接力
        被 H3 读成「两个物体 / 交接」（shot22 v2 判退教训）；f048 后 ease 回体侧
  纸 root 由左手位置驱动：摊开 → 折/展开 → 抬离 → 横移到盒口 → 落入盒内 → 被盖遮住
  盒盖 绕后沿铰链从 -105° 敞开 ease 到 0° 合上
  P01 姥姥的褪色旧红发带 从 f001 起就在敞口盒里，纯 Emission 暗红，清晰可见

时间轴（192f / 8s，关键变化全部前置在 f001–f048，§5.21）：
  f001       前态：小几上摊开旧作业本 P10 / 通知书复印件 P11 / 地址纸 P12
             （0.42×0.20 亮暖奶油色，上面三道手写地址细线，最后一处略歪）；
             右侧敞口盒 D09 里躺着 P01 红发带；许宁双手已在纸面
  f001–006   指腹抹平：左手从纸左端滑到右端
  f006–012   折好：右半张绕折线翻到左半张上（fold_k 0→1），双手收拢
  f012–016   又展开：fold_k 1→0，纸恢复摊开
  f016–024   纸抬离小几到弧线中点 (0.24,0.82,0.88)
  f024–032   横移到盒口上方 (0.38,0.83,0.84)
  f032–040   落入盒内 (0.38,0.83,0.762)，与红发带收在一起
  f040–048   合盖（唯一允许纸从视野消失的原因）；f046 起纸/发带被盖遮住
  f049–120   静坐；窗外日光连续渐弱、台灯相对渐亮、world 渐暗（坐到天黑）
  f120–160   周远端着饭碗从门边走近，f148–f160 把碗放到小几左端
  f160–192   许宁左手伸到碗沿 → 碗随左手轻轻端起，慢慢吃几口

物理链六项（方法论 §4.2）：① 首帧可见且够大 ② 有前态 ③ 从桌面到盒内的连续位移
④ 道具由手骨骼驱动 ⑤ 有后态（合盖的盒子） ⑥ 关键变化在 f001–f048 内。

已知坑全部规避：
  §5.14 按 clip 序号名称取 action、脚高用站姿 Idle 实测
  §5.15 圆柱横放绕 X 转 90°；柔光/天黑一律用真实移动渐弱光源，不做几何光斑板
  §5.16 build_room() 末尾补 view_layer.update()
  §5.17 椅背/小几腿/窗框用镂空细杆，不做正对相机的实心大方板
  §5.18/§5.19 纸必须完整连续地「离桌 → 到盒口 → 落盒」，不能只在桌面折短；
        被合上的盒盖遮住是唯一允许消失的物体（shot16 两版判退的根因更正）
  §5.20 手 K 一律在当帧骨骼状态下逐帧坐标下降求解，静态角度只作多起点之一
  §5.21 关键变化前置、首帧道具画幅与对比度足够（纯 Emission 暖纸 + Standard）
  §5.22 多起点 + 误差兜底重求，取消任何跨帧静态锁角
  第 23/24 条 先扫坐姿双手包络再定左右手分工；状态保持型道具避免被读成「拿走」

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot23.py
  blender.exe --background --python tools/previs_shot23.py   （192 帧一次性全渲）
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
FRAMES_DIR = os.path.join(OUT_DIR, "frames23")
PROBE_JSON = os.path.join(ROOT, "tmp_qc", "shot23_probe_v2.json")
REPORT_JSON = os.path.join(OUT_DIR, "previs23_report.json")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720
CAM_LENS = 35
# v2 抬高机位偏右（俯角 10°→15°）；v3 再拉近一档放大人物画幅约 20%
CAM_START = (0.30, -2.25, 1.66)
CAM_END = (0.25, -2.15, 1.64)
AIM = Vector((0.14, 0.92, 0.80))

# ---------------------------------------------------------------- 布局（v2 探针实测）
XU_LOC = (0.00, 0.95)
YAW_DEG = 0.0
CHAIR_TOP_Z = 0.45
TRAY_TOP_Z = 0.735
# v3：彻底改为不落地、不横跨腿前的「膝前浅托盘」，消除 v1 半蹲 / v2 笼子错觉
TRAY_CENTER = (0.22, 0.87, 0.72)

# v2：周远更靠后靠右、侧身站，降低对主道具的注意力
ZHOU_START = (1.45, 1.95)
ZHOU_END = (1.05, 1.45)
ZHOU_YAW_DEG = -20.0
DZ_ZHOU = 0.7785

# v2：纸抬离台面 0.017m，避免与台面 z-fighting；饱和暖橙与灰白台面拉开对比
PAPER_CENTER = (0.10, 0.80, 0.772)
BOX_CENTER = (0.44, 0.83, 0.76)
BOX_IN_Z = 0.775
PAPER_IN_BOX = (0.38, 0.83, BOX_IN_Z)
BOWL_DOCK = (0.02, 0.83, 0.775)

# 左手 anchor（v2 探针真实 solve 误差见 shot23_probe_v2.json）
RIGHT_SUPPORT = (-0.10, 0.82, 0.76)
SMOOTH_START = (0.02, 0.82, 0.77)
SMOOTH_END = (0.20, 0.80, 0.77)
FOLD_MID = (0.11, 0.81, 0.79)
LIFT_MID = (0.24, 0.82, 0.88)
BOX_RIM = (0.38, 0.83, 0.84)
BOX_IN = (0.38, 0.83, 0.76)
LID_CLOSE = (0.36, 0.83, 0.82)
LEFT_REST = (0.30, 0.90, 0.62)
BOWL_EDGE = (0.02, 0.83, 0.79)
BOWL_LIFT = (-0.02, 0.86, 0.88)

# E08 背景（shot12 布局家族）
WALL_Y = 2.35
WIN_X0, WIN_X1 = 0.05, 1.55
WIN_Z0, WIN_Z1 = 1.05, 2.25
DESK_Y = 2.00
DESK_Z = 0.78

BONES = ("mixamorig:RightArm", "mixamorig:RightForeArm",
         "mixamorig:LeftArm", "mixamorig:LeftForeArm",
         "mixamorig:Head", "mixamorig:Neck",
         "mixamorig:Spine", "mixamorig:Spine1")

RETREAT_R = (-45.0, -132.1, 0.0, 56.6)
RETREAT_L = (-45.0, 132.1, 0.0, -56.6)

G = {}   # 逐帧需要访问的对象/材质


def mat(key, shade, emission=None):
    return p14.mat("s23_" + key, shade, emission)


def emission_mat(name, color, strength):
    """纯自发光材质：Standard 色彩管理下保持饱和，不被灯光冲淡（shot21 v3）。"""
    m = bpy.data.materials.new("s23_" + name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def add_torus(name, loc, major, minor, m, rot=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=24, minor_segments=6,
                                     location=loc)
    o = bpy.context.active_object
    o.name = name
    if rot is not None:
        o.rotation_euler = rot
    if m is not None:
        o.data.materials.append(m)
    return o


def build_room():
    """E08 朝北小屋：北窗 + 窗下书桌 + 单人床 + 书堆（背景），膝前小几（前景操作区）。"""
    wall = mat("wall", 0.34)
    p14.add_box("floor", (0, 0, -0.05), (7.0, 8.0, 0.10), mat("floor", 0.25))
    p14.add_box("ceiling", (0, 0, 2.70), (7.0, 8.0, 0.10), mat("ceil", 0.32))
    p14.add_box("side_wall_l", (-2.60, 0.90, 1.35), (0.12, 3.0, 2.70), wall)
    p14.add_box("side_wall_r", (2.60, 0.90, 1.35), (0.12, 3.0, 2.70), wall)

    # 后墙留窗洞（四块拼接，避免实心整板）
    p14.add_box("wall_back_l", ((-2.60 + WIN_X0) / 2, WALL_Y, 1.35),
                (WIN_X0 + 2.60, 0.12, 2.70), wall)
    p14.add_box("wall_back_r", ((WIN_X1 + 2.60) / 2, WALL_Y, 1.35),
                (2.60 - WIN_X1, 0.12, 2.70), wall)
    wx, wz = (WIN_X0 + WIN_X1) / 2, (WIN_Z0 + WIN_Z1) / 2
    p14.add_box("wall_back_top", (wx, WALL_Y, (WIN_Z1 + 2.70) / 2),
                (WIN_X1 - WIN_X0, 0.12, 2.70 - WIN_Z1), wall)
    p14.add_box("wall_back_bot", (wx, WALL_Y, WIN_Z0 / 2),
                (WIN_X1 - WIN_X0, 0.12, WIN_Z0), wall)
    frame = mat("winframe", 0.30)
    for nm, px in (("win_l", WIN_X0), ("win_r", WIN_X1), ("win_m", wx)):
        p14.add_box(nm, (px, WALL_Y - 0.04, wz),
                    (0.05, 0.07, WIN_Z1 - WIN_Z0), frame)
    for nm, pz in (("win_t", WIN_Z1), ("win_b", WIN_Z0)):
        p14.add_box(nm, (wx, WALL_Y - 0.04, pz),
                    (WIN_X1 - WIN_X0 + 0.08, 0.07, 0.05), frame)
    # 白纱窗帘（薄板，只遮窗左三分之一，不挡窗光）
    p14.add_box("curtain", (WIN_X0 + 0.22, WALL_Y - 0.10, wz),
                (0.40, 0.02, WIN_Z1 - WIN_Z0 + 0.06), mat("curtain", 0.46))
    p14.add_cyl("curtain_rod", (wx, WALL_Y - 0.12, WIN_Z1 + 0.09),
                0.014, 1.75, mat("rod", 0.36),
                rot=(0, math.radians(90), 0))

    # 窗外天光板：纯 Emission，逐帧改强度做「天黑」（不是几何光斑板）
    dm = emission_mat("daylight_em", (0.62, 0.72, 0.86), 0.34)
    G["daylight_mat"] = dm
    G["daylight_em"] = [n for n in dm.node_tree.nodes
                        if n.bl_idname == "ShaderNodeEmission"][0]
    p14.add_box("daylight", (wx, WALL_Y + 1.6, 1.75), (5.0, 0.10, 3.2), dm)
    p14.add_box("bld_out", (wx + 1.15, WALL_Y + 0.9, 1.55),
                (1.6, 0.28, 1.5), mat("bld_out", 0.28))

    # 窗下书桌（背景）：薄台面 + 四条细腿 + 合上的抽屉 + 台灯 + 杯 + 水壶
    desk = mat("desk", 0.40)
    p14.add_box("desk_top", (wx, DESK_Y, DESK_Z), (1.70, 0.65, 0.055), desk)
    for dx in (-0.76, 0.76):
        for dy in (-0.26, 0.26):
            p14.add_box(f"desk_leg_{dx}_{dy}",
                        (wx + dx, DESK_Y + dy, DESK_Z / 2),
                        (0.045, 0.045, DESK_Z), desk)
    # 抽屉合上基准：缩进桌板下（§5.15 D5）
    p14.add_box("desk_drawer", (wx, DESK_Y - 0.02, DESK_Z - 0.16),
                (1.40, 0.40, 0.24), mat("drawer", 0.34))
    p14.add_box("drawer_pull", (wx, DESK_Y - 0.23, DESK_Z - 0.16),
                (0.10, 0.025, 0.025), mat("pull", 0.56))
    p14.add_box("lamp_base", (wx + 0.58, DESK_Y, DESK_Z + 0.03),
                (0.13, 0.13, 0.035), mat("lampmetal", 0.44))
    p14.add_cyl("lamp_arm", (wx + 0.58, DESK_Y, DESK_Z + 0.20),
                0.014, 0.34, mat("lampmetal", 0.44))
    p14.add_cyl("lamp_head", (wx + 0.52, DESK_Y - 0.04, DESK_Z + 0.38),
                0.075, 0.10, mat("lampshade", 0.52),
                rot=(math.radians(28), 0, 0))
    p14.add_cyl("mug", (wx - 0.50, DESK_Y, DESK_Z + 0.07),
                0.045, 0.11, mat("mug", 0.58))
    p14.add_cyl("kettle", (wx - 0.68, DESK_Y, DESK_Z + 0.13),
                0.075, 0.24, mat("kettle", 0.30))

    # 左侧单人床 + 床边书堆（v2：整体左移出画面主体 + 压暗，避免抢主道具）
    bedx = -2.35
    p14.add_box("bed_frame", (bedx, 0.85, 0.32),
                (1.15, 2.05, 0.22), mat("bedframe", 0.26))
    p14.add_box("bed_mattress", (bedx, 0.85, 0.50),
                (1.10, 2.00, 0.16), mat("mattress", 0.40))
    p14.add_box("bed_quilt", (bedx, 0.58, 0.62),
                (1.08, 1.45, 0.10), mat("quilt", 0.34))
    p14.add_box("bed_pillow", (bedx, 1.62, 0.62),
                (0.68, 0.38, 0.10), mat("pillow", 0.44))
    for k, c in enumerate((0.24, 0.30, 0.27, 0.34, 0.26, 0.32)):
        p14.add_box(f"bookstack_{k}", (-1.55, 1.18, 0.03 + 0.035 * k),
                    (0.30, 0.22, 0.030), mat(f"book{k}", c))

    # v3：不落地、不横跨腿前的「膝前浅托盘」。v1 的落地桌把人拦腰截断、
    # v2 的桌裙栅栏把下半身框成笼子，v3 直接取消一切桌腿/栅栏，
    # 只在后沿留一根短横杆暗示托盘搁在膝上；人物腿部自然垂落。
    tray = mat("tray", 0.40)
    p14.add_box("tray_top", TRAY_CENTER, (0.92, 0.20, 0.030), tray)
    p14.add_cyl("tray_back_support",
                (TRAY_CENTER[0], TRAY_CENTER[1] + 0.095, 0.655),
                0.016, 0.86, mat("traysupport", 0.30),
                rot=(0, math.radians(90), 0))

    # 人物坐的椅子：椅面 + 镂空椅背（放在人物背后 +y，D4 坑）
    chair = mat("chair", 0.32)
    p14.add_box("chair_seat", (XU_LOC[0], XU_LOC[1], CHAIR_TOP_Z),
                (0.46, 0.42, 0.045), chair)
    for dx in (-0.19, 0.19):
        for dy in (-0.16, 0.16):
            p14.add_box(f"chair_leg_{dx}_{dy}",
                        (XU_LOC[0] + dx, XU_LOC[1] + dy, CHAIR_TOP_Z / 2),
                        (0.032, 0.032, CHAIR_TOP_Z), chair)
    for dx in (-0.19, 0.19):
        p14.add_cyl(f"chair_back_post_{dx}",
                    (XU_LOC[0] + dx, XU_LOC[1] + 0.20, 0.70),
                    0.020, 0.52, chair)
    for z in (0.62, 0.92):
        p14.add_cyl(f"chair_back_rail_{z}",
                    (XU_LOC[0], XU_LOC[1] + 0.20, z),
                    0.016, 0.38, chair, rot=(0, math.radians(90), 0))

    # §5.16：强制刷新依赖图，最后创建的几何体 dimensions 才会生效
    bpy.context.view_layer.update()


def build_props():
    """P10 作业本 / P11 通知书复印件 / P12 地址纸（两半可折）/ D09 盒与盖 / P01 红发带 / 饭碗。"""
    # --- P10 / P11：桌面上摊开的另外两件遗物（不参与位移，恒存） ---
    p14.add_box("exercise_book", (-0.20, 0.86, TRAY_TOP_Z + 0.014),
                (0.26, 0.18, 0.022), mat("book", 0.50))
    p14.add_box("book_cover_line", (-0.20, 0.86, TRAY_TOP_Z + 0.027),
                (0.22, 0.008, 0.003), mat("bookline", 0.26))
    p14.add_box("letter_copy", (0.02, 0.90, TRAY_TOP_Z + 0.010),
                (0.28, 0.17, 0.008), mat("letter", 0.58))
    for k in range(3):
        p14.add_box(f"letter_line_{k}", (0.02, 0.86 + 0.035 * k, TRAY_TOP_Z + 0.016),
                    (0.20, 0.006, 0.002), mat("letterink", 0.24))

    # --- P12 地址纸：Empty root + 左右半张 + 折痕 + 三道手写地址细线 ---
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=PAPER_CENTER)
    root = bpy.context.active_object
    root.name = "paper_root"
    G["paper_root"] = root
    # v2：饱和暖橙 + 放大，让「一张纸」在灰白台面上有明确轮廓（v1 只剩几道线）
    paper_m = emission_mat("paper_em", (0.98, 0.74, 0.36), 1.00)
    ink_m = mat("paper_ink", 0.16)
    parts = []

    def piece(name, loc, dims, m):
        o = p14.add_box(name, loc, dims, m)
        o.parent = root
        parts.append(o)
        return o

    left_half = piece("paper_left_half", (-0.115, 0, 0), (0.23, 0.22, 0.006), paper_m)
    right_half = piece("paper_right_half", (0.115, 0, 0), (0.23, 0.22, 0.006), paper_m)
    G["paper_left_half"] = left_half
    G["paper_right_half"] = right_half
    piece("paper_crease", (0, 0, 0.004), (0.005, 0.22, 0.002), ink_m)
    # 改过两次的地址：三道细线，旧地址未划掉、新地址写在旁边、最后一处略歪
    for k, (yy, w, ang) in enumerate(((0.055, 0.24, 0), (0.005, 0.28, 0), (-0.050, 0.22, 7))):
        o = piece(f"address_line_{k}", (-0.02, yy, 0.005), (w, 0.009, 0.002), ink_m)
        o.rotation_euler.z = math.radians(ang)
    piece("address_new_0", (0.13, 0.055, 0.005), (0.10, 0.007, 0.002), ink_m)
    piece("address_new_1", (0.14, 0.005, 0.005), (0.09, 0.007, 0.002), ink_m)
    G["paper_parts"] = parts

    # --- D09 遗物盒：Empty root + 四片薄壁 + 底板 + 铰链盖 ---
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=BOX_CENTER)
    box = bpy.context.active_object
    box.name = "box_root"
    G["box_root"] = box
    # v2：盒壁压暗、盒口提亮、盒壁略降低，让敞口与盒内红发带在联系表上可读
    boxm = mat("boxwall", 0.24)
    boxrim = mat("boxrim", 0.56)
    bw, bd, bh = 0.30, 0.22, 0.090

    def bpiece(name, loc, dims, m, parent=None):
        o = p14.add_box(name, loc, dims, m)
        o.parent = parent if parent is not None else box
        return o

    bpiece("box_front", (0, -bd / 2, 0), (bw, 0.012, bh), boxm)
    bpiece("box_back", (0, bd / 2, 0), (bw, 0.012, bh), boxm)
    bpiece("box_left", (-bw / 2, 0, 0), (0.012, bd, bh), boxm)
    bpiece("box_right", (bw / 2, 0, 0), (0.012, bd, bh), boxm)
    bpiece("box_bottom", (0, 0, -bh / 2), (bw, bd, 0.012), boxm)
    for dy in (-bd / 2, bd / 2):
        bpiece(f"box_rim_y{dy}", (0, dy, bh / 2), (bw + 0.02, 0.016, 0.012), boxrim)

    # 铰链 Empty 在盒后沿；盖板绕它翻合
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    hinge = bpy.context.active_object
    hinge.name = "lid_hinge"
    hinge.parent = box
    hinge.location = (0, bd / 2, bh / 2)
    G["lid_hinge"] = hinge
    lid = p14.add_box("box_lid", (0, -bd / 2, 0), (bw + 0.02, bd, 0.014),
                      mat("boxlid", 0.56))
    lid.parent = hinge
    # 盖面一道浅色包边，让「合盖」动作在联系表上可读
    edge = p14.add_box("box_lid_edge", (0, -bd + 0.012, 0.010),
                       (bw + 0.02, 0.012, 0.004), boxrim)
    edge.parent = hinge

    # --- P01 姥姥的褪色旧红发带：盒内两小段弯带，纯 Emission 暗红 ---
    # v2：抬到盒口附近、加粗提亮，避免被盒前壁挡住（v1 发带位于盒底完全看不见）
    ribbon_m = emission_mat("ribbon_em", (0.80, 0.10, 0.08), 1.20)
    rparts = []
    for k, (dx, dy, ang) in enumerate(((0.045, -0.035, 24), (-0.045, 0.030, -32))):
        o = p14.add_cyl(f"red_ribbon_{k}", (0, 0, 0), 0.018, 0.16, ribbon_m,
                        rot=(math.radians(90), 0, math.radians(ang)))
        o.parent = box
        o.location = (dx, dy, bh / 2 - 0.016)
        rparts.append(o)
    G["ribbon_parts"] = rparts

    # --- 饭碗：周远端进来，后段放到小几左端 ---
    bowl = p14.add_cyl("rice_bowl", BOWL_DOCK, 0.075, 0.075,
                       mat("bowl", 0.60))
    add_torus("rice_bowl_rim", BOWL_DOCK, 0.075, 0.008,
              mat("bowlrim", 0.70))
    G["bowl"] = bowl
    G["bowl_rim"] = bpy.data.objects["rice_bowl_rim"]

    bpy.context.view_layer.update()


def add_lighting():
    """坐到天黑：真实 AREA 主光渐弱+缓移 + 台灯 POINT 渐亮 + fill/world 渐暗。

    光影移动全靠真实光源，不做几何光斑板（§5.15 D5）。
    """
    world = bpy.data.worlds.new("previz_world23")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.20, 0.22, 0.26, 1.0)
            n.inputs[1].default_value = 0.30
    bpy.context.scene.world = world
    G["world_bg"] = [n for n in world.node_tree.nodes
                     if n.bl_idname == "ShaderNodeBackground"][0]

    bpy.ops.object.light_add(type="AREA", location=(-1.30, 0.80, 2.30))
    sun = bpy.context.active_object
    sun.name = "dusk_key"
    sun.data.energy = 120
    sun.data.size = 1.45
    sun.data.color = (1.00, 0.90, 0.74)
    sun.rotation_euler = (math.radians(52), math.radians(-16), 0)
    G["sun"] = sun

    bpy.ops.object.light_add(type="POINT", location=(0.60, 1.85, 1.18))
    lamp = bpy.context.active_object
    lamp.name = "desk_lamp"
    lamp.data.energy = 12
    lamp.data.shadow_soft_size = 0.55
    lamp.data.color = (1.00, 0.84, 0.58)
    G["lamp"] = lamp

    bpy.ops.object.light_add(type="AREA", location=(0.90, -1.20, 2.30))
    fill = bpy.context.active_object
    fill.name = "cool_fill"
    fill.data.energy = 40
    fill.data.size = 2.60
    fill.data.color = (0.72, 0.80, 1.00)
    fill.rotation_euler = (math.radians(28), 0, 0)
    G["fill"] = fill


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
    """左手：抹平 → 折/展开 → 抬离 → 横移 → 盒口 → 盒内 → 合盖 → 收回 → 接碗。

    所有段间端点一致，全程 ease，零跳变。
    """
    if f <= 6:
        return lerp3(SMOOTH_START, SMOOTH_END, p14.ease((f - 1) / 5.0))
    if f <= 12:
        return lerp3(SMOOTH_END, FOLD_MID, p14.ease((f - 6) / 6.0))
    if f <= 16:
        return FOLD_MID
    if f <= 24:
        return lerp3(FOLD_MID, LIFT_MID, p14.ease((f - 16) / 8.0))
    if f <= 32:
        return lerp3(LIFT_MID, BOX_RIM, p14.ease((f - 24) / 8.0))
    if f <= 40:
        return lerp3(BOX_RIM, BOX_IN, p14.ease((f - 32) / 8.0))
    if f <= 48:
        return lerp3(BOX_IN, LID_CLOSE, p14.ease((f - 40) / 8.0))
    if f <= 120:
        return lerp3(LID_CLOSE, LEFT_REST, p14.ease((f - 48) / 72.0))
    if f <= 160:
        return lerp3(LEFT_REST, BOWL_EDGE, p14.ease((f - 120) / 40.0))
    if f <= 176:
        return BOWL_EDGE
    return lerp3(BOWL_EDGE, BOWL_LIFT, p14.ease((f - 176) / 16.0))


def paper_pos(f):
    """地址纸 root：桌面摊开 → 抬离 → 弧线中点 → 盒口 → 盒内。"""
    if f <= 16:
        return PAPER_CENTER
    if f <= 24:
        return lerp3(PAPER_CENTER, LIFT_MID, p14.ease((f - 16) / 8.0))
    if f <= 32:
        return lerp3(LIFT_MID, BOX_RIM, p14.ease((f - 24) / 8.0))
    if f <= 40:
        return lerp3(BOX_RIM, PAPER_IN_BOX, p14.ease((f - 32) / 8.0))
    return PAPER_IN_BOX


def fold_k(f):
    """折好又展开（0 摊开 / 1 对折）。"""
    if f <= 6:
        return 0.0
    if f <= 12:
        return p14.ease((f - 6) / 6.0)
    if f <= 16:
        return 1.0 - p14.ease((f - 12) / 4.0)
    return 0.0


def lid_angle_deg(f):
    """盒盖：-75° 敞开（v2 让盖板始终留在画面里）→ 0° 合上。"""
    if f <= 40:
        return -75.0
    if f <= 48:
        return -75.0 + 75.0 * p14.ease((f - 40) / 8.0)
    return 0.0


def xu_head(f):
    """低头看纸 → 静坐 → 末段侧头看周远（连续 ease）。"""
    if f <= 48:
        return 14.0 - 4.0 * p14.ease((f - 1) / 47.0), 0.0
    if f <= 140:
        return 10.0, 2.0 * p14.ease((f - 49) / 91.0)
    return (10.0 - 6.0 * p14.ease((f - 141) / 51.0),
            2.0 - 8.0 * p14.ease((f - 141) / 51.0))


def zhou_loc(f):
    if f <= 120:
        return ZHOU_START
    if f <= 160:
        return (ZHOU_START[0] + (ZHOU_END[0] - ZHOU_START[0]) * p14.ease((f - 120) / 40.0),
                ZHOU_START[1] + (ZHOU_END[1] - ZHOU_START[1]) * p14.ease((f - 120) / 40.0))
    return ZHOU_END


def main():
    with open(PROBE_JSON, encoding="utf-8") as fh:
        probe = json.load(fh)
    assert probe.get("all_reachable") and probe.get("probe_version") == "v2_final", \
        "定稿探针未全绿，先修布局再跑预演"
    sol = probe["solutions"]
    ANG = {k: tuple(v["angles"]) for k, v in sol.items()}
    print("[previs23] anchors", {k: [round(v, 1) for v in a] for k, a in ANG.items()},
          flush=True)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    build_room()
    build_props()
    add_lighting()

    xu, x_acts, _ = p14.import_glb(os.path.join(MODELS, "C06b", "tex_mesh_animated.glb"))
    zhou, z_acts, _ = p14.import_glb(os.path.join(MODELS, "C18", "tex_mesh_animated.glb"))
    print("[previs23] xu_acts", len(x_acts), "zhou_acts", len(z_acts), flush=True)
    if len(x_acts) < 5 or len(z_acts) < 5:
        raise RuntimeError("C06b / C18 都应有 10 个动作 clip")

    x_idle = act_by_clip(x_acts, 1)
    x_sit = act_by_clip(x_acts, 4)
    z_idle = act_by_clip(z_acts, 1)
    for a in (x_idle, x_sit, z_idle):
        p14.make_loop(a)
    removed = p14.strip_channels([x_idle, x_sit, z_idle], BONES)
    print("[previs23] sit clip", x_sit.name, "| zhou idle", z_idle.name,
          "| stripped", len(removed), "channels", flush=True)

    scene = bpy.context.scene
    p14.set_loop(xu.animation_data, x_idle, {"key": None}, "idle_probe")
    p14.set_loop(zhou.animation_data, z_idle, {"key": None}, "idle_zhou")
    xu.rotation_mode = "XYZ"
    zhou.rotation_mode = "XYZ"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    dz_x = -p14.feet_z(xu) + 0.02
    dz_z = -p14.feet_z(zhou) + 0.02
    print(f"[previs23] feet dz xu={dz_x:.4f} zhou={dz_z:.4f}", flush=True)
    assert abs(dz_x - probe["dz"]) < 0.01 and abs(dz_z - DZ_ZHOU) < 0.01
    p14.set_loop(xu.animation_data, x_sit, {"key": None}, "sit")

    # 角色统一哑光，场景/道具保留 s23_ 前缀材质
    char_matte = p14.make_matte("char_matte23", 0.34)
    for o in [o for o in scene.objects if o.type == "MESH"]:
        names = [m.name for m in o.data.materials] if o.data.materials else []
        if any(n.startswith("s23_") for n in names):
            continue
        o.data.materials.clear()
        o.data.materials.append(char_matte)

    scene.render.engine = "BLENDER_EEVEE"
    # 纯 Emission 暖纸/暗红发带在 AgX 下会被压淡，切 Standard 保持饱和（shot21 v3）
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = RES_X, RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, N_FRAMES
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    cam_data = bpy.data.cameras.new("previs_cam23")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam23", cam_data)
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

    seed_l = ANG["smooth_start"]
    seed_r = ANG["right_support"]
    max_err, max_err_f = 0.0, 0
    paper_samples, light_samples = [], []

    for f in frames_iter:
        t = (f - 1) / (N_FRAMES - 1)
        tc = p14.ease(t)
        xu.location = (*XU_LOC, dz_x)
        xu.rotation_euler = (0, 0, math.radians(YAW_DEG))
        zl = zhou_loc(f)
        zhou.location = (zl[0], zl[1], dz_z)
        zhou.rotation_euler = (0, 0, math.radians(ZHOU_YAW_DEG))
        scene.frame_set(f)
        bpy.context.view_layer.update()

        # ---------- 头：许宁低头看纸 → 静坐 → 侧头看周远 ----------
        xd, xt = xu_head(f)
        head_pose(xu, xd, xt)
        head_pose(zhou, 4.0, -6.0)

        # ---------- 体侧基准：每帧先摆回体侧角，实测当帧 rest_pt（§5.20 / C3） ----------
        apply_arm(xu, "Left", *RETREAT_L)
        rest_xl = hand_world(xu, "Left")
        apply_arm(xu, "Right", *RETREAT_R)
        rest_xr = hand_world(xu, "Right")
        # v3：周远 f001–120 双手体侧（剧本「过了一会儿，把饭端了进来」），
        # f120–148 ease 到右前伸托碗；不做逐帧求解，避免增加第三条手 K 链
        ck = p14.ease(min(1.0, max(0.0, (f - 120) / 28.0)))
        carry = (62.0, -85.0, 0.0, 42.0)
        zang = tuple(RETREAT_R[i] + (carry[i] - RETREAT_R[i]) * ck
                      for i in range(4))
        apply_arm(zhou, "Right", *zang)

        # ---------- 许宁左手：地址纸整条物理链 ----------
        tgt_l = xu_left_target(f)
        sl, el = solve_with_fallback(xu, "Left", tgt_l,
                                      [seed_l, ANG["smooth_start"], ANG["fold_mid"],
                                       ANG["lift_mid"], ANG["box_rim"], ANG["box_in"],
                                       ANG["lid_close"], RETREAT_L])
        seed_l = sl

        # ---------- 许宁右手：f001–048 轻扶纸左沿，之后 ease 回体侧 ----------
        if f <= 48:
            tgt_r = RIGHT_SUPPORT
        else:
            tgt_r = lerp3(RIGHT_SUPPORT, rest_xr, p14.ease((f - 49) / 24.0))
        sr, er = solve_with_fallback(xu, "Right", tgt_r,
                                     [seed_r, ANG["right_support"], RETREAT_R])
        seed_r = sr
        err = max(el, er)
        if err > max_err:
            max_err, max_err_f = err, f

        # ---------- 地址纸：由左手驱动，折/展开 + 完整连续位移 ----------
        hl = hand_world(xu, "Left")
        # f001–016 纸摊在小几上；f016–040 由当帧左手骨骼驱动（3 帧 ease 过渡，
        # 手与纸零脱节，§1.2）；f040 后固定在盒内，手单独去合盖。
        if f <= 16:
            pp = PAPER_CENTER
        elif f <= 40:
            hand_pt = (hl[0], hl[1] - 0.010, hl[2] - 0.020)
            kd = p14.ease(min(1.0, (f - 16) / 3.0))
            pp = lerp3(paper_pos(f), hand_pt, kd)
            pp = (pp[0], pp[1],
                  pp[2] + 0.012 * math.sin(math.pi * min(1.0, (f - 16) / 24.0)))
        else:
            pp = PAPER_IN_BOX
        G["paper_root"].location = pp
        k = fold_k(f)
        G["paper_right_half"].location = (0.115 - 0.23 * k, 0, 0.010 * k)
        G["paper_right_half"].rotation_euler.y = math.radians(180.0 * k)
        hidden = f >= 46          # 被合上的盒盖遮住：唯一允许消失的物体
        for o in G["paper_parts"]:
            o.hide_render = hidden
        paper_samples.append((f, [round(v, 3) for v in pp], round(k, 3), hidden))

        # ---------- 盒盖：f040–048 从敞开 ease 到合上 ----------
        G["lid_hinge"].rotation_euler.x = math.radians(lid_angle_deg(f))
        for o in G["ribbon_parts"]:
            o.hide_render = hidden

        # ---------- 饭碗：周远手 → 小几左端 → 许宁左手 ----------
        zh = hand_world(zhou, "Right")
        zh_hold = (zh[0], zh[1] - 0.02, zh[2] + 0.06)
        if f <= 148:
            bp = zh_hold
        elif f <= 160:
            bp = lerp3(zh_hold, BOWL_DOCK, p14.ease((f - 148) / 12.0))
        elif f <= 176:
            bp = BOWL_DOCK
        else:
            bp = lerp3(BOWL_DOCK, (hl[0], hl[1] - 0.01, hl[2] + 0.05),
                       p14.ease((f - 176) / 16.0))
        # v3：碗 f001–120 隐藏、f120–132 缩放置 0→1 渐显，避免首帧「举杯」观感
        bs = max(0.001, p14.ease(min(1.0, max(0.0, (f - 120) / 12.0))))
        for o in (G["bowl"], G["bowl_rim"]):
            o.scale = (bs, bs, bs)
            o.hide_render = f <= 120
        G["bowl"].location = bp
        G["bowl_rim"].location = (bp[0], bp[1], bp[2] + 0.037 * bs)

        # ---------- 坐到天黑：真实光源渐弱/缓移 + 台灯渐亮 + world 渐暗 ----------
        G["sun"].data.energy = 120.0 - 110.0 * t
        G["sun"].location.x = -1.30 + 1.90 * t
        G["sun"].data.color = (1.00 - 0.45 * t, 0.90 - 0.24 * t, 0.74 + 0.14 * t)
        G["lamp"].data.energy = 12.0 + 113.0 * t
        G["fill"].data.energy = 40.0 - 30.0 * t
        G["world_bg"].inputs[1].default_value = 0.30 - 0.20 * t
        G["daylight_em"].inputs["Strength"].default_value = 0.34 - 0.30 * t
        light_samples.append((f, round(G["sun"].data.energy, 1),
                              round(G["lamp"].data.energy, 1),
                              round(G["sun"].location.x, 3)))

        # ---------- 相机：缓慢推镜 + 极轻手持微晃 ----------
        cam.location = sp.lerp(ep, tc)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (AIM - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        if test_mode:
            print(f"[previs23] f{f:03d} L=({hl[0]:.3f},{hl[1]:.3f},{hl[2]:.3f}) "
                  f"err={err:.4f} paper={paper_samples[-1][1]} fold={k:.2f} "
                  f"lid={lid_angle_deg(f):.0f} sun={G['sun'].data.energy:.0f} "
                  f"lamp={G['lamp'].data.energy:.0f}", flush=True)

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs23] frame {f}/{N_FRAMES}", flush=True)

    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot23", "title": "地址纸与盒子", "priority": "P0",
            "source": "剧本六 L353-359 / 方案 §3 §4 / E08_v01.png（目检：水彩朝北小屋书桌，无人物）",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E08 朝北小屋：北窗带白纱窗帘、窗下书桌（抽屉/台灯/杯/水壶）、左侧单人床与书堆；前景膝前浅托盘（不落地、不横跨腿前）承载遗物操作区；桌前镂空木椅。天黑由真实渐弱主光 + 渐亮台灯 + 渐暗 world/窗外天光给出，无几何光斑板",
            "camera": [list(CAM_START), list(CAM_END), list(AIM)],
            "characters": {
                "xu": "C06b 许宁·中老年 ten-clip / clip 4 Sitting_Idle_Loop",
                "zhou": "C18 周远·老年 ten-clip / clip 1 Idle（站姿，f120–160 走近）",
                "feet_dz": {"xu": round(dz_x, 4), "zhou": round(dz_z, 4)},
                "feet_note": "脚高用站姿 clip 1 Idle 实测（§5.14）；坐姿 clip 的 Hips 位移探针实测 0，无需剥 root motion",
            },
            "probe": {
                "file": "tmp_qc/shot23_probe_v2.json", "version": "v2_final",
                "all_reachable": True,
                "errors_m": {k: v["error_m"] for k, v in sol.items()},
                "rejected_layouts": [
                    "tmp_qc/shot23_probe.json（按参考图标准书桌 y≈0.50 / z≈0.78 定点，8 个理想点全部超出坐姿包络 0.283–0.510m）→ progress/04_白模预演/shot23_探针_v1_布局判退/",
                ],
                "left_right_split": "v1 扫坐姿双手包络（右手 x∈[-0.613,0.217]、左手 x∈[-0.208,0.624]、y 下界 0.767/0.732）；v2 定为左手独立完成抹平→折→展开→抬离→横移→入盒→合盖整条链，右手只轻扶纸左沿不参与位移",
            },
            "layout_decision": {
                "reason": "参考图的 0.78m 标准书桌超出 C06b 坐姿双手可达范围（手臂前伸仅约 0.18–0.22m）",
                "solution": "前景膝前浅托盘顶面 z=0.735、中心 y=0.87（v3 取消落地桌腿与桌裙，消除半蹲/笼子错觉）承载 P10/P11/P12/D09；背景保留 E08 书桌/北窗/床/书堆作空间识别（参考图只锁布局，§5.8）",
                "tray": {"center": list(TRAY_CENTER), "top_z": TRAY_TOP_Z},
            },
            "paper": {
                "driver": "f001–016 摊在托盘；f016–040 由当帧左手骨骼世界坐标驱动（3 帧 ease 过渡，手与纸零脱节，§1.2）；f040 起固定在盒内 PAPER_IN_BOX，手单独去合盖；f046 起被合上的盒盖遮住（全片唯一允许消失的物体）",
                "dims": [0.46, 0.22, 0.006],
                "material": "纯 Emission 饱和暖橙 (0.98,0.74,0.36) 强度 1.00 + Standard 色彩管理（v2 起，与灰白台面拉开对比）",
                "address_lines": "三道手写地址细线（旧地址未划掉、新地址写在旁边、最后一处略歪 7°）",
                "fold": "右半张 loc.x 0.115→-0.115、z 抬 0.010、绕 Y 转 180°，fold_k f006–012 0→1（折好）、f012–016 1→0（又展开）",
                "first_frame_visible_and_large": True,
                "never_teleports": True,
                "disappears_only_by_closed_lid": True,
                "samples": paper_samples[::16],
            },
            "box_and_ribbon": {
                "box": "Empty root + 四片薄壁 + 底板 + 两道口沿（敞口，不做实心块）",
                "lid": "lid_hinge 在盒后沿，绕 X 从 -75° 敞开 ease 到 0° 合上（f040–048；v2 改 -105°→-75° 让盖板始终留在画面里）",
                "p01_red_ribbon": "两段纯 Emission 暗红 (0.80,0.10,0.08) 强度 1.20、半径 0.018、抬到盒口附近，f001 起就在敞口盒内；与 shot16 P02、shot27 P03 区分",
                "red_ribbon_visible_in_first_frame": True,
            },
            "other_props": {
                "p10_exercise_book": "小几左后方薄本，恒存不动",
                "p11_letter_copy": "小几后方浅灰薄纸 + 三道细线，恒存不动",
                "rice_bowl": "f001–120 隐藏、周远双手体侧；f120–132 缩放置 0→1 渐显、f120–148 右手 ease 到托碗角；f148–160 ease 到托盘左端；f160–176 静置；f176–192 随许宁左手轻轻端起",
            },
            "sunlight": {
                "method": "dusk_key AREA energy 120→10 且 x -1.30→+0.60、色温暖白→冷蓝；desk_lamp POINT 12→125；cool_fill 40→10；world 0.30→0.10；窗外天光 Emission 0.34→0.04。全部线性，无阶跃、无几何光斑板",
                "continuous": True, "samples": light_samples[::24],
            },
            "arm_solver": {
                "method": "两只工作手（许宁左手/右手）每帧先摆回体侧角实测 rest_pt，再在当前帧骨骼状态下做多起点坐标下降；起点=上一帧解 + 六段探针 anchor + 体侧角；6 轮 / 初始步长 20° / 每轮 ×0.6；误差 >0.045m 换 12 轮 30° 大步长，>0.06m 再换 12 轮 12° 细修（§5.22）",
                "retreat": {"right": list(RETREAT_R), "left": list(RETREAT_L)},
                "max_error_m": round(max_err, 4), "max_error_frame": max_err_f,
            },
            "timeline": {
                "f001": "前态：小几上摊开 P10 作业本 / P11 通知书复印件 / P12 地址纸（亮暖奶油、地址细线清晰）；右侧敞口盒里 P01 红发带；双手已在纸面",
                "f001-006": "指腹抹平：左手从纸左端滑到右端",
                "f006-012": "折好：右半张翻折到左半张上，双手收拢",
                "f012-016": "又展开：纸恢复摊开",
                "f016-024": "纸抬离小几到弧线中点 (0.24,0.82,0.88)",
                "f024-032": "横移到盒口上方 (0.38,0.83,0.84)",
                "f032-040": "落入盒内 (0.38,0.83,0.762)，与红发带收在一起",
                "f040-048": "合盖；f046 起纸与发带被盖遮住（唯一允许消失）",
                "f049-120": "静坐；天黑光影连续渐变",
                "f120-160": "周远端碗走近，f148–160 把碗放到小几左端",
                "f160-192": "许宁左手伸到碗沿、碗随左手轻抬（慢慢吃几口）",
            },
            "three_state": {
                "address_sheet": "小几上摊开（f001）→ 抹平/折/展开 → 抬离 → 横移 → 落入盒内 → 被合上的盒盖遮住（f192 不见）",
                "box_lid": "敞开 -75°（f001）→ f040–048 ease 合上 → 合盖静置（f192）",
                "daylight": "明亮暖白窗光 → 连续渐弱渐冷 → 蓝灰暮色 + 台灯暖光",
            },
            "hard_constraints": "许宁全程坐在椅上、脚贴地；只有 C06b 与 C18 两人、无第三人；地址纸必须从桌面完整连续地移动到盒内，不得凭空消失/漂浮/变形；P10/P11/盒子/红发带/台灯/杯全程恒存不消失；北窗/窗帘/书桌/床/书堆/小几全程同位；段间全 ease 渐变无硬切；192 帧一次性全渲保证逐帧求解器 seed 连续",
            "previs_v1_rework": {
                "test_frames": "progress/04_白模预演/shot23_测试帧_v1/",
                "verdict": "rejected（不进入全渲），判定书 v1_verdict.json",
                "issues": [
                    "落地小几把坐姿人物拦腰截断、桌下露出蜷腿，读作半蹲/跪在桌下",
                    "地址纸纯 Emission 暖奶油在灰白台面上无轮廓，只剩三道深色细线",
                    "盒内红发带位于盒底被前壁挡住；盒盖 -105° 掀到背后看不见",
                    "床占左下约 25%，窗外天光板过曝；整体偏灰白、人物与背景黏连",
                ],
                "fixes": ["机位抬高偏右", "纸改饱和暖橙并放大", "盒壁压暗/发带抬到盒口/盖改 -75°",
                           "床左移压暗", "灯光总量下调、昼夜差拉大", "周远侧身后移"],
                "scope": "仅场景/灯光/道具/机位；逐帧求解误差与 v2/v3 逐字一致",
            },
            "previs_v2_rework": {
                "test_frames": "progress/04_白模预演/shot23_测试帧_v2/",
                "verdict": "rejected（画面可读性残留），判定书 v2_verdict.json",
                "passed": "亮橙纸与红发带清晰、天黑渐变拉开、床不再抢戏、整体对比改善",
                "root_cause": "用『加遮挡物』解决半蹲错觉方向错，桌裙栅栏把下半身框成笼子",
                "fixes": ["彻底取消落地桌腿与桌裙，改不落地不横跨腿前的膝前浅托盘",
                           "相机 y -2.75→-2.25 拉近一档", "周远的碗改后段渐显", "台灯终点 110→125"],
            },
            "non_blocking": [
                "膝前浅托盘无落地腿，原分辨率略有悬浮感；参考图只锁布局，H3 会重绘为书桌（§5.8）",
                "周远 f001 右手在胸前呈白色团块（站姿模型手部 + 体侧角），白模只供运动",
                "人物画幅约占画高 1/3，主体与道具在联系表上仍可辨",
                "f192 整体偏暗，窗台台灯暖光仍保留脸/手/合盖盒子/碗的轮廓",
            ],
            "physical_chain_checklist": {
                "first_frame_visible_and_large": True,
                "has_before_state": True,
                "continuous_displacement": True,
                "driven_by_hand_bones": True,
                "has_after_state": True,
                "key_change_before_f048": True,
            },
            "max_error_m": round(max_err, 4),
            "max_error_frame": max_err_f,
        }
        with open(REPORT_JSON, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("[previs23] max_error", round(max_err, 4), "@ f", max_err_f, flush=True)
        print("[previs23] WROTE", REPORT_JSON, flush=True)
    print("PREVIS23_DONE", flush=True)


if __name__ == "__main__":
    main()
