# -*- coding: utf-8 -*-
"""白模预演：shot21「一袋橘子」（剧本六 L327-337，方案 §4）。

场景 E10 出租屋门口清晨版。E10_v01.png 目检确认画面里**完全没有门、门框、玄关**，
只有厨房角（窗、水槽、台面、搁板、吊灯、折叠餐桌 + 两把椅）。因此本白模明确搭出
『打开的入户门 + 门框 + 门内玄关窄桌 + 门后能瞥见厨房一角』，让参考视频直接给出
门口空间拓扑，不指望 prompt 凭空补门（台账 shot21.preparation.risk_note ①）。

双人镜头：C06b 许宁·中老年（门洞里）、C11 妈妈·老年（门内侧）。
两人相距 0.53m 斜对面（yaw ±70°），因为 tmp_qc/probe_shot21.py 实测这两个绑骨模型
手臂前伸只有 0.24–0.30m，间距 1.10m 时中间会出现谁都够不到的空档（v1/v2 判退）。

核心动作链（HANDOFF §5.19，必须靠白模给出，prompt 补不出位移）：
  前态   f001 许宁站在门口右手提一袋橘子，袋子大且亮橙、首帧就够醒目（§5.21）
  交接   f009–f024 袋子从许宁右手平滑转到妈妈双手（关键变化前置到前 1 秒）
  移步   f025–f044 许宁收手；妈妈带袋缓行到玄关桌前并侧身转向桌子
  摆橘   f046–f160 妈妈右手持袋、左手从袋口逐个取橘子摆到桌面；
                    6 个橘子走「袋口 → 桌面」短弧线，最后一个单独放远（最软的那个）
  后态   f150–f168 空袋从妈妈手里 ease 放到桌面；f169–f192 许宁轻点头侧身朝门，
                    门始终开着、桌上橘子一排、两人安静对视

物理链六项（方法论 §4.2）：① 首帧可见且够大 ② 有前态 ③ 有从 A 到 B 的连续位移
④ 道具由手骨骼驱动 ⑤ 有后态 ⑥ 关键变化在 f001–f024 内 —— 全部打勾才提交 H3。

已知坑（HANDOFF §5）已规避：
  §5.14 按 clip 序号名称取 action、脚高用站姿 Idle 实测
  §5.16 build_room() 末尾补 view_layer.update()
  §5.17 门扇斜开 78° 且做框式结构，椅背/搁架用镂空细杆，不做正对相机的实心大方板
  §5.19 关键道具完整物理链；袋子 root 由当帧手部世界坐标驱动
  §5.20 手 K 一律在当帧骨骼状态下逐帧坐标下降求解，静态角度只作多起点之一
  §5.21 关键变化前置、道具首帧画幅与对比度足够（亮橙 emission 是白模里唯一彩色）
  §5.22 多起点 + 误差兜底重求，取消任何跨帧静态锁角

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot21.py
  blender.exe --background --python tools/previs_shot21.py   （192 帧一次性全渲）
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
FRAMES_DIR = os.path.join(OUT_DIR, "frames21")
PROBE_JSON = os.path.join(ROOT, "tmp_qc", "shot21_probe.json")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720
CAM_LENS = 32                       # v2 拉近一档，放大人物画幅（v1 只占画高 1/3）
CAM_START = (-0.85, -2.95, 1.48)
CAM_END = (-0.72, -2.80, 1.44)
AIM = Vector((-0.80, 0.95, 1.05))

# ---------------------------------------------------------------- 布局（探针实测）
XU_LOC = (-1.15, 0.95)
XU_YAW_DEG = 70.0
MOM_A = (-0.62, 0.95)
MOM_B = (0.02, 0.72)
MOM_YAW_A_DEG = -70.0
MOM_YAW_B_DEG = 40.0

BAG_HOME_XU = (-0.98, 0.80, 0.90)
HAND_OFF = (-0.90, 0.88, 0.95)
HAND_OFF_L = (-0.96, 0.88, 0.95)
HAND_OFF_R = (-0.84, 0.88, 0.95)
BAG_HOLD_MOM_A = (-0.76, 0.85, 0.92)
# v2：左右手袋口目标分离。v1 共用一个 MOUTH_STATIC 让 f044 左手差 0.087m，
# f160/f176/f192 末位点 0.54 也超出左臂可达包络，分别下修。
MOUTH_R = (0.10, 0.72, 0.92)            # 右手扶袋（探针实测可达）
MOUTH_L = (0.10, 0.72, 0.86)            # 左手取橘子（略低，收进可达包络）
BAG_DOCK = (-0.04, 1.06, 0.92)          # 后态空袋放在桌左端

# v3：整体右移避开妈妈躯干与前臂（v2 前几颗被挡，末帧程序化只数出 2 团）；
# 最末 0.56 仍在左臂可达包络 x≤0.61 内，并继续与前面 5 颗拉开距离。
TABLE_PTS = [(0.14 + 0.06 * i, 0.94, 0.86) for i in range(5)] + [(0.56, 0.94, 0.86)]
# 橘子 i：回袋段 [s-6, s)，离袋到桌面段 [s, e]
ORANGE_MOVE = [(46 + 20 * i, 60 + 20 * i) for i in range(6)]

# 门框 / 玄关 / 厨房角
DOOR_HINGE = (-2.40, 0.0)
DOOR_LEFT, DOOR_RIGHT = -2.40, -0.75
DOOR_H = 2.10
DOOR_OPEN_DEG = 78.0
CONSOLE_CENTER = (0.30, 1.05)
CONSOLE_TOP_Z = 0.80
WALL_Y = 3.20
WIN_X0, WIN_X1 = -1.90, -0.10
WIN_Z0, WIN_Z1 = 1.15, 2.35

BONES = ("mixamorig:RightArm", "mixamorig:RightForeArm",
         "mixamorig:LeftArm", "mixamorig:LeftForeArm",
         "mixamorig:Head", "mixamorig:Neck",
         "mixamorig:Spine", "mixamorig:Spine1")

# v2 修正：p14.arms_down 的左右规则是 ay/fb 反号、ax 同号。v1 把 ax 也取反，
# 导致妈妈左手在 f001 平伸向右前方。两个模型共用同一对体侧角。
RETREAT_R = (-45.0, -132.1, 0.0, 56.6)    # 右手垂在体侧（shot19/20 实测）
RETREAT_L = (-45.0, 132.1, 0.0, -56.6)    # 左手垂在体侧
RETREAT_XU = RETREAT_R                     # 兼容：许宁右手
RETREAT_MOM = RETREAT_L                    # 兼容：妈妈左手


def mat(key, shade, emission=None):
    return p14.mat("s21_" + key, shade, emission)


def add_sphere(name, radius, loc, m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=12,
                                         ring_count=8, location=loc)
    o = bpy.context.active_object
    o.name = name
    if m is not None:
        o.data.materials.append(m)
    return o


def add_chair(name, px, py, shade=0.52):
    """厨房角的镂空栏杆椅（§5.17），不做整块实心板。"""
    c = mat("chair", shade)
    p14.add_box(f"{name}_seat", (px, py, 0.44), (0.42, 0.42, 0.05), c)
    for dx in (-0.16, 0.16):
        p14.add_box(f"{name}_post_{dx}", (px + dx, py + 0.19, 0.75),
                    (0.04, 0.04, 0.58), c)
    for z in (0.62, 0.98):
        p14.add_box(f"{name}_rail_{z}", (px, py + 0.19, z), (0.38, 0.04, 0.045), c)
    for lx in (-0.17, 0.17):
        for ly in (-0.17, 0.17):
            p14.add_box(f"{name}_leg_{lx}_{ly}", (px + lx, py + ly, 0.22),
                        (0.035, 0.035, 0.44), c)


def build_room():
    """E10 出租屋门口：前墙门洞 + 打开的门 + 玄关窄桌 + 门后厨房一角。"""
    # v2 整体压暗一档：v1 白墙白地白人黏成灰白一片（shot20 v8 同类问题）
    wall = mat("wall", 0.46)
    p14.add_box("floor", (0, 0, -0.05), (7.0, 8.0, 0.10), mat("floor", 0.32))
    p14.add_box("ceiling", (0, 0, 2.70), (7.0, 8.0, 0.10), mat("ceil", 0.42))
    p14.add_box("left_wall", (-3.20, 0, 1.35), (0.12, 8.0, 2.70), wall)
    p14.add_box("right_wall", (3.20, 0, 1.35), (0.12, 8.0, 2.70), wall)

    # 前墙：只做门洞左段；x > DOOR_RIGHT 是敞开的玄关，右侧窄桌与厨房都可见
    p14.add_box("front_wall_left", ((-3.30 + DOOR_LEFT) / 2, 0, 1.35),
                (DOOR_LEFT + 3.30, 0.12, 2.70), wall)
    # v3：删除门框右柱实体。v1 的 0.10×0.16 粗柱、v2 的 0.045×0.10 细柱都
    # 是一条从画面顶贯到地的竖线，正好压在 f024 的交接动作上并把两人割裂。
    # 改为开放式门洞：左柱 + 上梁 + 门槛，右侧完全敞开，交接动作无遮挡。
    frame = mat("doorframe", 0.26)
    p14.add_box("door_jamb_l", (DOOR_LEFT, 0, DOOR_H / 2),
                (0.045, 0.10, DOOR_H), frame)
    p14.add_box("door_lintel", ((DOOR_LEFT + DOOR_RIGHT - 0.10) / 2, 0, DOOR_H),
                (DOOR_RIGHT - 0.10 - DOOR_LEFT + 0.20, 0.10, 0.08), frame)
    p14.add_box("door_threshold", ((DOOR_LEFT + DOOR_RIGHT) / 2, 0, 0.012),
                (DOOR_RIGHT - DOOR_LEFT, 0.22, 0.024), mat("threshold", 0.34))

    # 打开的门扇：框式结构（上下横 + 左右竖 + 两块嵌板 + 把手），斜开 78°。
    # 斜开后板面投影只有约 0.34m 宽，不会被读成「一块板子长出来」（§5.17）。
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(DOOR_HINGE[0], DOOR_HINGE[1], 0))
    door = bpy.context.active_object
    door.name = "door_root"
    door.rotation_euler = (0, 0, math.radians(DOOR_OPEN_DEG))
    L = DOOR_RIGHT - DOOR_LEFT
    dm = mat("doorpanel", 0.40)
    hedge = mat("dooredge", 0.20)   # v2 加深边框，让「打开的框式门」一眼可辨

    def dpart(name, loc, dims, m):
        o = p14.add_box(name, loc, dims, m)
        o.parent = door
        return o

    dpart("door_frame_l", (0.045, 0, DOOR_H / 2), (0.07, 0.055, DOOR_H), hedge)
    dpart("door_frame_r", (L - 0.045, 0, DOOR_H / 2), (0.07, 0.055, DOOR_H), hedge)
    dpart("door_frame_t", (L / 2, 0, DOOR_H - 0.045), (L, 0.055, 0.08), hedge)
    dpart("door_frame_b", (L / 2, 0, 0.045), (L, 0.055, 0.08), hedge)
    dpart("door_mid_rail", (L / 2, 0, 1.02), (L, 0.055, 0.06), hedge)
    dpart("door_panel_upper", (L / 2, 0, 1.56), (L - 0.16, 0.030, 0.94), dm)
    dpart("door_panel_lower", (L / 2, 0, 0.50), (L - 0.16, 0.030, 0.82), dm)
    dpart("door_handle", (L - 0.16, -0.055, 1.00), (0.045, 0.055, 0.14),
          mat("handle", 0.18))

    # 玄关窄桌：桌面 + 桌布 + 四条细腿（橘子就摆在这张桌面上）
    cx, cy = CONSOLE_CENTER
    p14.add_box("console_top", (cx, cy, CONSOLE_TOP_Z), (0.80, 0.40, 0.045),
                mat("console", 0.42))
    p14.add_box("console_cloth", (cx, cy, CONSOLE_TOP_Z + 0.027),
                (0.84, 0.44, 0.012), mat("cloth", 0.44))
    for dx in (-0.34, 0.34):
        for dy in (-0.16, 0.16):
            p14.add_box(f"console_leg_{dx}_{dy}", (cx + dx, cy + dy, 0.39),
                        (0.035, 0.035, 0.76), mat("consoleleg", 0.32))
    p14.add_box("console_rail", (cx, cy + 0.17, 0.22), (0.70, 0.025, 0.025),
                mat("consoleleg", 0.32))

    # 门后厨房一角（压暗，只负责「能瞥见」）：后墙窗 + 窗帘 + 水槽台 + 搁板碗 + 吊灯
    bw = mat("backwall", 0.42)
    p14.add_box("wall_back_l", ((-3.3 + WIN_X0) / 2, WALL_Y, 1.35),
                (WIN_X0 + 3.3, 0.12, 2.70), bw)
    p14.add_box("wall_back_r", ((WIN_X1 + 3.3) / 2, WALL_Y, 1.35),
                (3.3 - WIN_X1, 0.12, 2.70), bw)
    p14.add_box("wall_back_top", ((WIN_X0 + WIN_X1) / 2, WALL_Y, (WIN_Z1 + 2.7) / 2),
                (WIN_X1 - WIN_X0, 0.12, 2.7 - WIN_Z1), bw)
    p14.add_box("wall_back_bot", ((WIN_X0 + WIN_X1) / 2, WALL_Y, WIN_Z0 / 2),
                (WIN_X1 - WIN_X0, 0.12, WIN_Z0), bw)
    wx, wz = (WIN_X0 + WIN_X1) / 2, (WIN_Z0 + WIN_Z1) / 2
    for nm, px in (("win_l", WIN_X0), ("win_r", WIN_X1)):
        p14.add_box(nm, (px, WALL_Y - 0.03, wz), (0.06, 0.08, WIN_Z1 - WIN_Z0),
                    mat("winframe", 0.40))
    for nm, pz in (("win_t", WIN_Z1), ("win_b", WIN_Z0)):
        p14.add_box(nm, (wx, WALL_Y - 0.03, pz),
                    (WIN_X1 - WIN_X0 + 0.10, 0.08, 0.06), mat("winframe", 0.40))
    p14.add_box("win_mid", (wx, WALL_Y - 0.03, wz),
                (0.045, 0.08, WIN_Z1 - WIN_Z0), mat("winframe", 0.40))
    p14.add_box("daylight", (wx, WALL_Y + 2.8, 1.80), (7.0, 0.10, 3.6),
                mat("daylight", 0.70, emission=(0.62, 0.68, 0.78, 1.0)))
    p14.add_box("curtain", (WIN_X0 - 0.10, WALL_Y - 0.12, 1.75),
                (0.30, 0.05, 1.18), mat("curtain", 0.64))
    p14.add_box("counter_body", (-1.0, 2.85, 0.44), (3.0, 0.60, 0.88),
                mat("cab", 0.46))
    p14.add_box("counter_top", (-1.0, 2.85, 0.90), (3.06, 0.66, 0.05),
                mat("coptop", 0.62))
    p14.add_box("sink", (-1.0, 2.80, 0.91), (0.54, 0.38, 0.035),
                mat("sink", 0.30))
    p14.add_cyl("faucet_stem", (-1.0, 3.07, 1.05), 0.022, 0.30,
                mat("faucet", 0.50))
    for i in range(2):
        p14.add_cyl(f"bowl_{i}", (-0.40, 2.88, 0.96 + i * 0.05), 0.080, 0.045,
                    mat("bowl", 0.78))
    shelf_m = mat("shelf", 0.40)
    p14.add_box("shelf_board", (1.15, WALL_Y - 0.18, 1.62), (1.05, 0.30, 0.04),
                shelf_m)
    for nm, sx in (("shelf_l", 0.68), ("shelf_r", 1.62)):
        p14.add_box(nm, (sx, WALL_Y - 0.18, 1.76), (0.035, 0.28, 0.30), shelf_m)
    p14.add_cyl("jar", (0.95, WALL_Y - 0.18, 1.76), 0.052, 0.20,
                mat("jar", 0.50))
    # 吊灯（细线 + 小灯罩，不用几何光斑板）
    p14.add_cyl("lamp_wire", (-2.60, 1.90, 2.28), 0.008, 0.60,
                mat("lampwire", 0.34))
    p14.add_cyl("lamp_shade", (-2.60, 1.90, 1.96), 0.085, 0.07,
                mat("lampshade", 0.66))
    add_chair("kitchen_chair", 1.35, 2.05, shade=0.42)

    # §5.16：强制刷新依赖图，最后创建的几何体 dimensions 才会生效
    bpy.context.view_layer.update()


def build_bag():
    """橘子袋：Empty 作 root，原点就是「手提点 / 袋口中心」。

    纸袋中灰 + 深色轮廓 + 敞开的袋口；袋内 6 颗亮橙橘子从袋口露出，
    是整幅白模里唯一的彩色，保证 f001 首帧够大够清晰（§5.21）。
    """
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=BAG_HOME_XU)
    root = bpy.context.active_object
    root.name = "bag_root"
    bag = mat("bag", 0.26)   # v3 加深袋身，避免首帧读成一个浅色托盘
    edge = mat("bagedge", 0.10)
    handle = mat("baghandle", 0.16)

    def piece(name, loc, dims, m):
        o = p14.add_box(name, loc, dims, m)
        o.parent = root
        return o

    # v2 致命修复：v1 用实心盒当袋身，6 颗橘子被完全包在里面，f001 只看到一个
    # 中空方框。这里改成 4 片薄板 + 底板，袋口彻底敞开；口沿也用 4 根细框条，
    # 不封住开口。橘子堆在袋口上方冒尖，亮橙色从首帧起直接可见。
    piece("bag_front", (0, -0.11, -0.17), (0.30, 0.014, 0.34), bag)
    piece("bag_back", (0, 0.11, -0.17), (0.30, 0.014, 0.34), bag)
    piece("bag_left", (-0.15, 0, -0.17), (0.014, 0.22, 0.34), bag)
    piece("bag_right", (0.15, 0, -0.17), (0.014, 0.22, 0.34), bag)
    piece("bag_bottom", (0, 0, -0.335), (0.30, 0.22, 0.014), edge)
    for sy in (-0.12, 0.12):
        piece(f"bag_rim_y_{sy}", (0, sy, 0.0), (0.32, 0.018, 0.022), edge)
    for sx in (-0.16, 0.16):
        piece(f"bag_rim_x_{sx}", (sx, 0, 0.0), (0.018, 0.24, 0.022), edge)
    for sx in (-0.10, 0.10):
        piece(f"bag_handle_{sx}", (sx, 0, 0.052), (0.020, 0.020, 0.105), handle)
    bpy.context.view_layer.update()
    return root


def build_oranges():
    """6 颗橘子：独立对象，逐帧显式定位（在袋里时挂 bag_root 变换）。

    v3 改用纯 Emission 节点：v2 的 Principled + AgX 把饱和橙压成淡桃色
    (213,172,132)，程序化统计在 f056 甚至数出 0 个橙色像素。纯自发光不受
    灯光与色彩管理冲淡，配合 view_transform=Standard，橘子在整条
    「袋口 → 桌面」弧线上都保持高对比。
    """
    om = bpy.data.materials.new("s21_orange_v3")
    om.use_nodes = True
    nt = om.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.34, 0.03, 1.0)
    em.inputs["Strength"].default_value = 1.25
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    objs = []
    for i in range(6):
        o = add_sphere(f"orange_{i}", 0.055, (0, 0, 0), om)
        objs.append(o)
    return objs


def add_lighting():
    world = bpy.data.worlds.new("previz_world21")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.27, 0.29, 0.33, 1.0)
            n.inputs[1].default_value = 0.58
    bpy.context.scene.world = world
    # 后窗冷蓝灰主光（清晨）
    bpy.ops.object.light_add(type="AREA", location=((WIN_X0 + WIN_X1) / 2, WALL_Y + 1.5, 2.0))
    key = bpy.context.active_object
    key.data.energy = 190
    key.data.size = 3.2
    key.data.color = (0.74, 0.82, 1.0)
    key.rotation_euler = (math.radians(65), 0, math.radians(180))
    # 门口一片暖光用软点光源，不做几何光斑板（§5.15）
    bpy.ops.object.light_add(type="POINT", location=(-1.60, -1.40, 2.05))
    warm = bpy.context.active_object
    warm.data.energy = 110
    warm.data.color = (1.0, 0.84, 0.64)
    bpy.ops.object.light_add(type="AREA", location=(0.20, 0.40, 2.25))
    fill = bpy.context.active_object
    fill.data.energy = 80
    fill.data.size = 2.0
    fill.data.color = (1.0, 0.90, 0.78)
    fill.rotation_euler = (math.radians(30), 0, 0)


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
    """只动 Head/Neck，不动 Spine（§5.20 避免上身旋转传导到手臂）。"""
    p14.rotate_ops(arm, "mixamorig:Head", [
        ((1, 0, 0), down), ((0, 0, 1), turn * 0.55),
    ])
    p14.rotate_world(arm, "mixamorig:Neck", (0, 0, 1), turn * 0.6)


def lerp3(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def solve_arm(arm, side, target, seeds, iters=6, step=20.0):
    """每帧、当帧骨骼状态下的多起点坐标下降（§5.20 / §5.22）。

    静态探针角度只作为多起点之一，绝不跨帧锁定复用。
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


def mom_left_target(f):
    """妈妈左手：接袋 → 反复「回袋口 → 送橘子到桌面」→ 停在最末点。"""
    if f <= 40:
        return MOUTH_L
    for i, (s, e) in enumerate(ORANGE_MOVE):
        r = s - 6
        if r <= f < s:
            prev = TABLE_PTS[i - 1] if i > 0 else MOUTH_L
            return lerp3(prev, MOUTH_L, p14.ease((f - r) / 6.0))
        if s <= f <= e:
            return lerp3(MOUTH_L, TABLE_PTS[i], p14.ease((f - s) / (e - s)))
    return TABLE_PTS[-1]


def orange_pos(i, f, mouth):
    """橘子 i 的世界坐标：在袋里返回 None；离袋后走「袋口 → 桌面」短弧线。"""
    s, e = ORANGE_MOVE[i]
    if f < s:
        return None
    k = p14.ease((f - s) / (e - s)) if f <= e else 1.0
    p = lerp3(mouth, TABLE_PTS[i], k)
    if f <= e:
        # v3 抬高 0.16m，让离袋途中的橘子高于妈妈的手与桌面，不被遮挡
        p = (p[0], p[1], p[2] + 0.16 * math.sin(math.pi * k))
    return p


def main():
    with open(PROBE_JSON, encoding="utf-8") as fh:
        probe = json.load(fh)
    assert probe.get("all_reachable"), "探针未全绿，先修布局再跑预演"
    sol = probe["solutions"]
    ANG = {
        "xu_bag": tuple(sol["xu_bag_home"]["angles"]),
        "xu_off": tuple(sol["xu_hand_off"]["angles"]),
        "mom_l": tuple(sol["mom_take_l"]["angles"]),
        "mom_r": tuple(sol["mom_take_r"]["angles"]),
        "mom_hold": tuple(sol["mom_hold_a_r"]["angles"]),
    }
    print("[previs21] anchors", {k: [round(v, 1) for v in a] for k, a in ANG.items()},
          flush=True)
    print("[previs21] table_pts", probe["recommended_table_points"], flush=True)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    build_room()
    bag_root = build_bag()
    oranges = build_oranges()
    add_lighting()

    xu, x_acts, _ = p14.import_glb(os.path.join(MODELS, "C06b", "tex_mesh_animated.glb"))
    mom, m_acts, _ = p14.import_glb(os.path.join(MODELS, "C11", "tex_mesh_animated.glb"))
    print("[previs21] xu_acts", len(x_acts), "mom_acts", len(m_acts), flush=True)
    if len(x_acts) < 4 or len(m_acts) < 4:
        raise RuntimeError("C06b / C11 都应有 10 个动作 clip")
    x_idle = act_by_clip(x_acts, 1)
    m_idle = act_by_clip(m_acts, 1)
    for a in (x_idle, m_idle):
        p14.make_loop(a)
    removed = p14.strip_channels([x_idle, m_idle], BONES)
    print("[previs21] stripped", len(removed), "channels", flush=True)

    scene = bpy.context.scene
    p14.set_loop(xu.animation_data, x_idle, {"key": None}, "idle")
    p14.set_loop(mom.animation_data, m_idle, {"key": None}, "idle")
    xu.rotation_mode = "XYZ"
    mom.rotation_mode = "XYZ"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    dz_x = -p14.feet_z(xu) + 0.02
    dz_m = -p14.feet_z(mom) + 0.02
    print(f"[previs21] feet dz xu={dz_x:.4f} mom={dz_m:.4f}", flush=True)

    # v2 人物压到 0.34：v1 的 0.50 与白墙白地几乎同亮度，人形黏在背景里
    matte = p14.make_matte("char_matte21", 0.34)
    for o in [o for o in scene.objects if o.type == "MESH"]:
        names = [m.name for m in o.data.materials] if o.data.materials else []
        if any(n.startswith("s21_") for n in names):
            continue
        o.data.materials.clear()
        o.data.materials.append(matte)

    scene.render.engine = "BLENDER_EEVEE"
    # v3：AgX 会把高饱和橙压成淡桃色，切 Standard 让橘子的纯 Emission 保持饱和
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = RES_X, RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, N_FRAMES
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    cam_data = bpy.data.cameras.new("previs_cam21")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam21", cam_data)
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

    # 袋内橘子的局部堆叠（袋口敞开，亮橙色从顶部露出）
    # v2：橘子堆在敞开的袋口上方冒尖，不在袋身内部
    LOCAL_IN_BAG = [(-0.070, -0.045, 0.010), (0.070, -0.045, 0.010),
                    (-0.070, 0.045, 0.010), (0.070, 0.045, 0.010),
                    (-0.045, 0.000, 0.062), (0.045, 0.000, 0.062)]

    seed_x = ANG["xu_bag"]
    seed_ml = ANG["mom_l"]
    seed_mr = ANG["mom_r"]
    max_err, max_err_f = 0.0, 0
    bag_samples = []
    for f in frames_iter:
        t = p14.ease((f - 1) / (N_FRAMES - 1))

        # ---------- 站位与朝向（妈妈 f25–f44 缓行到桌前并侧身，不切 clip） ----------
        k_move = p14.ease((f - 25) / 19.0) if 25 <= f <= 44 else (1.0 if f > 44 else 0.0)
        mom_xy = (MOM_A[0] + (MOM_B[0] - MOM_A[0]) * k_move,
                  MOM_A[1] + (MOM_B[1] - MOM_A[1]) * k_move)
        mom_yaw = MOM_YAW_A_DEG + (MOM_YAW_B_DEG - MOM_YAW_A_DEG) * k_move
        xu.location = (*XU_LOC, dz_x)
        xu.rotation_euler = (0, 0, math.radians(XU_YAW_DEG))
        mom.location = (*mom_xy, dz_m)
        mom.rotation_euler = (0, 0, math.radians(mom_yaw))
        scene.frame_set(f)
        bpy.context.view_layer.update()

        # ---------- 头：许宁低头递袋后抬头、结尾轻点头；妈妈看袋子再转看她 ----------
        xu_down = 5.0 - 3.0 * p14.ease((f - 25) / 30.0)
        if 169 <= f <= 192:
            xu_down += 1.8 * math.sin((f - 169) / 5.0)
        head_pose(xu, xu_down, 2.0 if f <= 44 else 5.0)
        head_pose(mom, 4.0 if f <= 100 else 1.0, -3.0 + 5.0 * p14.ease((f - 141) / 40.0))

        # ---------- 体侧基准：每帧先摆回体侧角度，实测当帧 rest_pt（§5.20 / C3） ----------
        apply_arm(xu, "Right", *RETREAT_R)
        rest_x = hand_world(xu, "Right")
        apply_arm(mom, "Left", *RETREAT_L)
        rest_ml = hand_world(mom, "Left")
        apply_arm(mom, "Right", *RETREAT_R)
        rest_mr = hand_world(mom, "Right")

        # ---------- 许宁右手：持袋 → 递到交接点 → 收回体侧 ----------
        if f <= 8:
            tgt_x = BAG_HOME_XU
        elif f <= 24:
            tgt_x = lerp3(BAG_HOME_XU, HAND_OFF, p14.ease((f - 9) / 15.0))
        elif f <= 40:
            tgt_x = lerp3(HAND_OFF, rest_x, p14.ease((f - 25) / 15.0))
        else:
            tgt_x = rest_x
        sx, ex = solve_with_fallback(xu, "Right", tgt_x,
                                     [seed_x, ANG["xu_bag"], ANG["xu_off"], RETREAT_XU])
        seed_x = sx
        apply_arm(xu, "Left", *RETREAT_L)

        # ---------- 妈妈双手：接袋 → 右手持袋、左手逐个摆橘子 ----------
        if f <= 8:
            tgt_ml, tgt_mr = rest_ml, rest_mr
        elif f <= 24:
            tgt_ml = lerp3(rest_ml, HAND_OFF_L, p14.ease((f - 9) / 15.0))
            tgt_mr = lerp3(rest_mr, HAND_OFF_R, p14.ease((f - 9) / 15.0))
        elif f <= 44:
            # 带袋走向桌前：双手一起收到身前持袋点（左右手高度分离）
            k = p14.ease((f - 25) / 19.0)
            tgt_ml = lerp3(HAND_OFF_L, MOUTH_L, k)
            tgt_mr = lerp3(HAND_OFF_R, MOUTH_R, k)
        else:
            tgt_mr = MOUTH_R                      # 右手始终扶着袋子
            tgt_ml = mom_left_target(f)           # 左手反复从袋口取橘子摆到桌面
        if f > 162:
            # v3：摆完后左手 ease 收回体侧，不再横压在桌面上挡住那排橘子
            tgt_ml = lerp3(TABLE_PTS[-1], rest_ml, p14.ease((f - 163) / 20.0))
        sl, el = solve_with_fallback(mom, "Left", tgt_ml,
                                     [seed_ml, ANG["mom_l"], RETREAT_MOM])
        sr, er = solve_with_fallback(mom, "Right", tgt_mr,
                                     [seed_mr, ANG["mom_r"], ANG["mom_hold"]])
        seed_ml, seed_mr = sl, sr
        err = max(ex, el, er)
        if err > max_err:
            max_err, max_err_f = err, f

        # ---------- 袋子：由当帧手部世界坐标驱动，平滑完成「一双手 → 另一双手」 ----------
        hx = hand_world(xu, "Right")
        hl = hand_world(mom, "Left")
        hr = hand_world(mom, "Right")
        mom_mid = tuple((hl[i] + hr[i]) / 2 for i in range(3))
        if f <= 9:
            bag_pt = hx
        elif f <= 24:
            bag_pt = lerp3(hx, mom_mid, p14.ease((f - 9) / 15.0))
        elif f <= 150:
            bag_pt = mom_mid
        elif f <= 168:
            bag_pt = lerp3(mom_mid, BAG_DOCK, p14.ease((f - 151) / 17.0))
        else:
            bag_pt = BAG_DOCK
        bag_root.location = bag_pt
        bag_root.rotation_euler = (0, 0, 0.025 * math.sin(f / 21.0))
        bpy.context.view_layer.update()

        # ---------- 橘子：在袋里时跟袋走，离袋后走短弧线到桌面点 ----------
        # v2：起点抬到袋口橘子堆中心，避免橘子离袋瞬间发生 0.03–0.08m 的 z 跳变
        mouth = tuple(bag_root.matrix_world @ Vector((0.0, 0.0, 0.035)))
        orange_world = []
        for i, o in enumerate(oranges):
            p = orange_pos(i, f, mouth)
            if p is None:
                w = bag_root.matrix_world @ Vector(LOCAL_IN_BAG[i])
                p = (w.x, w.y, w.z)
            o.location = p
            orange_world.append([round(v, 3) for v in p])
        bpy.context.view_layer.update()
        bag_samples.append((f, [round(v, 3) for v in bag_pt]))

        # ---------- 相机 ----------
        cam.location = sp.lerp(ep, t)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (AIM - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        if test_mode:
            print(f"[previs21] f{f:03d} move={k_move:.2f} "
                  f"bag=({bag_pt[0]:.3f},{bag_pt[1]:.3f},{bag_pt[2]:.3f}) "
                  f"xuR=({hx[0]:.3f},{hx[1]:.3f},{hx[2]:.3f}) "
                  f"momL=({hl[0]:.3f},{hl[1]:.3f},{hl[2]:.3f}) "
                  f"momR=({hr[0]:.3f},{hr[1]:.3f},{hr[2]:.3f}) "
                  f"err={err:.4f} o0={orange_world[0]} o5={orange_world[5]}",
                  flush=True)

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs21] frame {f}/{N_FRAMES}", flush=True)

    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot21", "title": "一袋橘子",
            "source": "剧本六 L327-337 / 方案 §4 / E10_v01.png（目检：原图无门无玄关）",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E10 出租屋门口清晨版：前墙门洞 + 门框 + 斜开 78° 的框式门扇 + 门内玄关窄桌 + 门后厨房一角（窗/水槽台/搁板/吊灯/镂空椅）；冷蓝灰窗光 + 门口暖光软点光源",
            "why_door_in_previs": "E10_v01 只有厨房角，完全没有门/门框/玄关。按台账 risk_note ①，白模必须直接给出门口空间拓扑，不能指望 prompt 补门",
            "camera": [list(CAM_START), list(CAM_END), list(AIM)],
            "characters": {
                "xu": "C06b 许宁·中老年 ten-clip / clip 1 Idle_Loop，全程站定不换 clip",
                "mom": "C11 妈妈·老年 ten-clip（横版 T-pose 重建版）/ clip 1 Idle_Loop；f25–f44 缓行平移 + ease 转身，不走 Walk clip 以免 root motion 与硬切",
            },
            "stand": {
                "xu": list(XU_LOC), "xu_yaw_deg": XU_YAW_DEG,
                "mom_a": list(MOM_A), "mom_b": list(MOM_B),
                "mom_yaw_a_deg": MOM_YAW_A_DEG, "mom_yaw_b_deg": MOM_YAW_B_DEG,
                "feet_dz": {"xu": round(dz_x, 4), "mom": round(dz_m, 4)},
                "distance_m": round(math.dist(XU_LOC, MOM_A), 3),
                "why_close": "tmp_qc/probe_shot21.py v1/v2 实测：模型手臂前伸仅 0.24–0.30m，1.10m 间距下中间出现谁都够不到的空档；收近到 0.53m 后交接 5 项误差 0.0033–0.0419m 全部可达",
            },
            "probe": {
                "file": "tmp_qc/shot21_probe.json",
                "all_reachable": True,
                "handoff_errors_m": {
                    k: sol[k]["error_m"] for k in
                    ("xu_bag_home", "xu_hand_off", "mom_take_l", "mom_take_r", "mom_hold_a_r")
                },
                "left_right_split": "包络扫描显示妈妈右臂可达 x≤0.256、左臂可达 x≤0.61；因此右手持袋、左手摆橘子，6 个桌面落点全部落在左手可达包络内",
                "table_points": [list(p) for p in TABLE_PTS],
            },
            "bag": {
                "driver": "Empty root 原点=手提点/袋口中心；f1–9 取许宁右手当帧世界坐标 → f10–24 ease 插值到妈妈双手中点 → f25–150 取妈妈双手中点 → f151–168 ease 放到桌面 BAG_DOCK → f169–192 静置桌面",
                "handoff_zero_jump": "交接点两侧手都在 HAND_OFF 附近，插值驱动使袋子位置连续，手与袋子零脱节（§5.19）",
                "shape_constant": True, "never_disappears": True,
                "first_frame_visible": True,
                "high_contrast": "纸袋 0.26 中灰 + 0.10 深色轮廓，4 片薄板敞口；6 颗橘子用纯 Emission 亮橙材质 + Standard 色彩管理，是白模里唯一彩色，在整条袋口→桌面弧线上都保持高对比（§5.21）",
                "samples": bag_samples[::24],
            },
            "oranges": {
                "count": 6,
                "schedule": [list(x) for x in ORANGE_MOVE],
                "path": "f<s 挂在 bag_root 局部坐标（跟着袋子走）；f∈[s,e] 从当帧袋口沿 ease 短弧线（中段抬高 0.10m）到 TABLE_PTS[i]；f>e 静置桌面",
                "last_one_apart": "第 6 颗单独放在 x=0.56，与前面 5 颗拉开，对应剧本『挑了一个最软的放在桌上』",
                "never_disappear": True,
                "all_end_on_table": True,
            },
            "arm_solver": {
                "method": "3 只手（许宁右手 / 妈妈左手 / 妈妈右手）每帧先摆回体侧角度实测 rest_pt，再在当前帧骨骼状态下做多起点坐标下降；起点集=上一帧解 + 该段探针实测 anchor + 体侧角，6 轮 / 初始步长 20° / 每轮 ×0.6；误差 >0.045m 换 12 轮 30° 大步长跳出局部最优，>0.06m 再换 12 轮 12° 细修（§5.22）。静态探针角度只作起点，绝不跨帧锁定",
                "retreat": {"right": list(RETREAT_R), "left": list(RETREAT_L),
                            "v1_fix": "左右规则为 ay/fb 反号、ax 同号；v1 把 ax 也取反，妈妈左手在 f001 平伸向右前方"},
                "mouth_targets": {"right": list(MOUTH_R), "left": list(MOUTH_L)},
                "anchors": {k: [round(v, 1) for v in a] for k, a in ANG.items()},
                "max_error_m": round(max_err, 4),
                "max_error_frame": max_err_f,
            },
            "timeline": {
                "f1-8": "前态：许宁站在门洞里右手提一袋亮橙橘子，妈妈在门内面对她；门开着、玄关窄桌空着",
                "f9-24": "核心交接：许宁把袋子递出，妈妈双手迎上，袋子从一双手平滑转到另一双手（关键变化前置 §5.21）",
                "f25-44": "许宁右手收回身侧；妈妈带袋缓行平移到玄关桌前并由 -70° ease 侧转到 40°",
                "f40-60": "妈妈左手回袋口，第 1 颗橘子沿短弧线离袋到桌面；右手始终扶袋",
                "f60-160": "其余 5 颗橘子逐个『回袋 → 离袋 → 落桌』，排成一行，最后一颗单独放远",
                "f150-168": "空袋从妈妈手里 ease 放到桌面左端",
                "f169-192": "后态：许宁轻点头侧身朝门、妈妈站在桌旁；门始终开着、桌上 6 颗橘子一排、空袋在桌左端、两人安静对视",
            },
            "three_state": {
                "bag": "许宁手里（袋口露出亮橙橘子）→ ease 位移到妈妈双手 → 随妈妈移到桌前 → ease 落到桌面；全程同一只袋子、不消失不换形",
                "oranges": "全部在袋里 → 逐个沿弧线从袋口到桌面 → 6 颗排成一行（末颗单独放远）",
                "mom_body": "门口面对许宁 → 缓行平移 + 侧身 → 站定在桌前摆橘子",
                "xu_right_hand": "提袋 → 递到交接点 → ease 收回身侧",
            },
            "hard_constraints": "脚贴地；双人镜头、无第三人；袋子与 6 颗橘子 f1–f192 全程存在且形状恒定；门始终打开在同一位置；前墙/门框/玄关桌/厨房角全程同位；段间全 ease 渐变、无硬切；门扇斜开且框式结构、搁架与椅背用镂空细杆不做实心大方板；192 帧一次性全渲保证逐帧求解器 seed 连续",
            "physical_chain_checklist": {
                "first_frame_visible_and_large": True,
                "has_before_state": True,
                "continuous_displacement": True,
                "driven_by_hand_bones": True,
                "has_after_state": True,
                "key_change_before_f024": True,
            },
            "previs_v1_rework": {
                "test_frames": "progress/04_白模预演/shot21_测试帧_v1/",
                "verdict": "rejected（不进入全渲），判定书 v1_verdict.json",
                "issues": [
                    "实心盒当袋身把 6 颗橘子完全包住，f001 只见一个中空方框，核心道具首帧不可见（§5.21）",
                    "门框右柱 0.10×0.16 孤立立在画面正中，把两人割裂；门口空间读成『柱子 + 白板』",
                    "整体过亮、人物与背景黏成灰白一片；人物只占画高约 1/3",
                    "妈妈左手在 f001 平伸向右前方（RETREAT 角度 ax 误取反）",
                    "f044 误差 0.0869m、f160 0.0567m（左手目标超出可达包络）",
                ],
                "fixes": [
                    "袋身改 4 片薄板 + 底板 + 4 根口沿细框，橘子堆到袋口上方冒尖，Base Color 也设亮橙",
                    "门框柱变细到 0.045×0.10 并加深到 0.26，门扇边框加深，上梁变薄",
                    "人物 matte 0.34 / 墙 0.46 / 地 0.32 / 后墙 0.42；world 0.58、key 190、fill 80、warm 110",
                    "相机 y -3.60→-2.95、lens 30→32，放大人物画幅",
                    "体侧角改共用 RETREAT_L/R（ax 同号）；左右手袋口目标分离；末位橘子点 0.54→0.48",
                ],
                "scope": "全部改动集中在场景层 / 道具层 / 灯光机位 / 姿态基准；动作时间线与逐帧求解器逐字未改（方法论 §2.2 分层返修）",
            },
            "previs_v2_rework": {
                "test_frames": "progress/04_白模预演/shot21_测试帧_v2/",
                "verdict": "rejected（画面可读性残留），判定书 v2_verdict.json",
                "passed": "敞口袋修复后 f001 橘子清楚可见；交接链橙色团从 x≈585px 右移到 x≈942px；最大误差 0.0430m 全部 <0.05m",
                "issues": [
                    "门框右柱细到 0.045×0.10 仍是从画面顶贯到地的竖线，正好压住 f024 的交接动作",
                    "橙色像素程序化统计：f056=0px、f072=14px、f088–f140 仅 1 团、f160/f192 仅 2 团，『橘子逐个从袋到桌』中段读不出来",
                    "AgX 把饱和橙压成淡桃色 (213,172,132)；球半径 0.042 太小、弧线抬高仅 0.10m",
                    "妈妈左手在 f160 后仍横压桌面末位橘子点，遮住整排橘子",
                ],
                "fixes": [
                    "删除 door_jamb_r 实体，改开放式门洞（左柱 + 上梁 + 门槛），交接动作无遮挡",
                    "橘子改纯 Emission 节点材质 + view_transform=Standard；半径 0.042→0.055；弧线抬高 0.10→0.16m",
                    "桌面落点右移到 [0.14..0.38] + [0.56]，避开妈妈躯干与前臂",
                    "f>162 左手 ease 收回体侧，后态桌面 6 颗橘子完整可见",
                    "袋身 0.34→0.26、桌布 0.52→0.44",
                ],
                "orange_audit": "v2 判定书内 orange_pixel_audit 字段（PIL+numpy 程序化，非肉眼臆断）",
            },
        }
        with open(os.path.join(OUT_DIR, "previs21_report.json"), "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS21_DONE", flush=True)


if __name__ == "__main__":
    main()
