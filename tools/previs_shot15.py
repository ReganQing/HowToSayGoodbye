# -*- coding: utf-8 -*-
"""白模预演：shot15「再攒两年」（剧本五 L269-275）。

场景：E09 朝北出租屋的折叠餐桌，与 shot13「两只碗」同一张桌子、同一组坐标。
夜晚；后墙一扇窗，窗台一盏小灯。许宁坐左椅 (-0.75,0.90)、周远坐右椅 (1.55,0.90)，
沿桌子左右隔桌对坐；相机在桌子正前方（y 负），两张四分之三侧脸与背景的窗都能入镜。

时间轴（192f / 8s），变化三态全部写成渐变，无硬切：
- f1-64   两人低头算账（before）：纸摊在桌面、笔在许宁手里小幅点算，
          周远手指在纸上点；两人上身略前倾、头低
- f65-92  许宁停笔（过程）：笔从斜立渐平放到纸面，点算幅度归零，
          上身回正、抬头看向周远；周远仍在算
- f93-124 许宁说「再攒两年吧」（after 的第一层）：嘴/头轻微动作；
          周远在 f105-124 停笔抬头，两人对视
- f125-160 收纸进抽屉（前态：抽屉合、纸在桌面 → 过程：抽屉拉出、纸收拢抬起
          → 后态：纸入柜、抽屉合上）
- f161-192 窗台小灯渐亮（前态：灭 → 过程：暖光渐起、墙上落一圈淡光
          → 后态：稳定），两人静坐，镜头微推

硬约束：两人始终坐在椅面上、脚贴地；纸/笔/抽屉不漂浮不瞬移；
小灯只在结尾亮；无第三人；对面椅子不空（shot15 是两人对坐，与 shot24 相反）。

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot15.py
  set PREVIS_RANGE=1-64 && blender.exe --background --python tools/previs_shot15.py
  blender.exe --background --python tools/previs_shot15.py
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
FRAMES_DIR = os.path.join(OUT_DIR, "frames15")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720

TABLE_CENTER = (0.4, 0.9)
CHAIR_LEFT = (-0.75, 0.90)     # 许宁，面向 +x
CHAIR_RIGHT = (1.55, 0.90)     # 周远，面向 -x
WIN_X0, WIN_X1 = -2.7, -1.3
WIN_Z0, WIN_Z1 = 1.15, 2.35
WALL_Y = 3.2
# 相机在桌子正前方（y 负）：两人左右对坐各呈四分之三侧脸，
# 后墙的窗与窗台小灯落在背景里，结尾灯光变化才进得了预演
CAM_START = (0.10, -2.95, 1.52)
CAM_END = (0.22, -2.62, 1.48)
CAM_LENS = 34
LAMP_POS = (-1.60, 2.92, 1.28)   # 窗台上的小灯

MANUAL_BONES = ("mixamorig:Head", "mixamorig:Neck",
                "mixamorig:Spine", "mixamorig:Spine1")


def mat(key, shade, emission=None):
    return p14.mat("s15_" + key, shade, emission)


def build_room():
    """朝北出租屋：折叠餐桌 + 两把椅 + 后墙窗 + 窗台小灯 + 桌侧矮柜抽屉。"""
    wall = mat("wall", 0.60)
    p14.add_box("floor", (0, 0, -0.05), (7.0, 8.0, 0.1), mat("floor", 0.40))
    p14.add_box("ceiling", (0, 0, 2.7), (7.0, 8.0, 0.1), mat("ceil", 0.54))
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
    p14.add_box("win_f_h", (cx, WALL_Y - 0.03, WIN_Z1), (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    p14.add_box("win_f_b", (cx, WALL_Y - 0.03, WIN_Z0), (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    p14.add_box("win_f_m", (cx, WALL_Y - 0.03, cz), (0.05, 0.08, WIN_Z1 - WIN_Z0), frame)
    p14.add_box("night", (cx, WALL_Y + 3.0, 1.8), (7.0, 0.1, 3.6),
                mat("night", 0.13, emission=(0.10, 0.13, 0.21, 1.0)))
    # 窗台 + 小灯
    p14.add_box("windowsill", (cx, WALL_Y - 0.22, WIN_Z0 - 0.03),
                (WIN_X1 - WIN_X0 + 0.24, 0.42, 0.05), mat("sill", 0.66))
    p14.add_cyl("lamp_base", (LAMP_POS[0], LAMP_POS[1], LAMP_POS[2]),
                0.085, 0.05, mat("lamp_base", 0.52))
    p14.add_cyl("lamp_shade", (LAMP_POS[0], LAMP_POS[1], LAMP_POS[2] + 0.16),
                0.11, 0.16, mat("lamp_shade", 0.72))
    bulb_mat = p14.make_matte("s15_bulb", 0.85, emission=(1.0, 0.80, 0.52, 1.0))
    p14.add_cyl("lamp_bulb", (LAMP_POS[0], LAMP_POS[1], LAMP_POS[2] + 0.11),
                0.045, 0.07, bulb_mat)
    # 墙上不做几何光斑：方片会被读成「一块板子长出来」，
    # 交给结尾的软点光源在墙面自然晕出一圈淡光（见 add_lighting）

    # 折叠方桌（与 shot13 同坐标同尺寸）
    tx, ty = TABLE_CENTER
    p14.add_box("table_top", (tx, ty, 0.74), (1.55, 1.0, 0.05), mat("table", 0.62))
    for dx in (-0.65, 0.65):
        p14.add_box(f"table_leg_{dx}", (tx + dx, ty, 0.37), (0.05, 0.85, 0.72),
                    mat("leg", 0.45))
    chair = mat("chair", 0.55)
    for name, (px, py), bx in (("chair_left", CHAIR_LEFT, CHAIR_LEFT[0] - 0.22),
                               ("chair_right", CHAIR_RIGHT, CHAIR_RIGHT[0] + 0.22)):
        p14.add_box(f"{name}_seat", (px, py, 0.44), (0.45, 0.45, 0.05), chair)
        p14.add_box(f"{name}_back", (bx, py, 0.75), (0.05, 0.45, 0.6), chair)
        for lx in (-0.18, 0.18):
            for ly in (-0.18, 0.18):
                p14.add_box(f"{name}_leg_{lx}_{ly}", (px + lx, py + ly, 0.22),
                            (0.04, 0.04, 0.44), chair)

    # 桌上道具：写满数字的纸、笔、暖壶
    paper = p14.add_box("paper", (tx - 0.05, ty + 0.02, 0.775),
                        (0.46, 0.34, 0.006), mat("paper", 0.90))
    pen = p14.add_cyl("pen", (tx - 0.16, ty - 0.04, 0.80), 0.009, 0.20,
                      mat("pen", 0.32))
    p14.add_cyl("thermos", (tx + 0.52, ty - 0.26, 0.90), 0.055, 0.32,
                mat("thermos", 0.50))

    # 桌子自带抽屉（桌板下方近侧，许宁坐着伸手够得到，拉出方向 -y）
    dx0 = tx - 0.30   # 偏左，靠近许宁那一侧，坐着伸手够得到
    p14.add_box("drawer_frame", (dx0, ty - 0.02, 0.66), (0.56, 0.92, 0.02),
                mat("cab", 0.52))
    # 合上时缩进桌板下被遮挡，拉出 0.22m 才露出来，「合→拉→合」读得出来
    drawer = p14.add_box("drawer_front", (dx0, ty - 0.28, 0.62),
                         (0.52, 0.035, 0.15), mat("drawer", 0.74))
    drawer_body = p14.add_box("drawer_body", (dx0, ty - 0.10, 0.62),
                              (0.46, 0.32, 0.12), mat("drawer_in", 0.68))
    # 墙角防潮垫（剧本 L275 周远新换的，作静态道具）
    p14.add_box("damp_mat", (-2.85, WALL_Y - 0.55, 0.06), (0.55, 0.34, 0.12),
                mat("damp", 0.48))

    # add_box 用 dimensions 实现尺寸，本质是 scale；后续驱动必须基于这个基准，
    # 直接写 (1,1,1) 会把薄片还原成 1 米立方体挡住画面
    print(f"[previs15] base scale paper={tuple(round(v,4) for v in paper.scale)}", flush=True)
    return paper, pen, drawer, drawer_body, bulb_mat


def act_by_clip(acts, n):
    """按 glb 内的 clip 序号取 action。

    bpy.data.actions 按名称字典序排列，animation_10 会排在 animation_2 前，
    且第二次导入的同名 action 会带 .001 后缀，按列表下标取必然错位。
    """
    target = f"animation_{n}"
    for a in acts:
        if a.name.split(".")[0] == target:
            return a
    raise RuntimeError(f"找不到 {target}，现有 {[a.name for a in acts]}")


def add_lighting():
    world = bpy.data.worlds.new("previz_world15")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.20, 0.21, 0.26, 1.0)
            n.inputs[1].default_value = 0.80
    bpy.context.scene.world = world
    # 窗外冷光
    bpy.ops.object.light_add(type="AREA", location=((WIN_X0 + WIN_X1) / 2, WALL_Y + 1.6, 2.0))
    key = bpy.context.active_object
    key.data.energy = 240
    key.data.size = 3.2
    key.data.color = (0.52, 0.62, 0.84)
    key.rotation_euler = (math.radians(65), 0, math.radians(180))
    # 桌面顶部暖光（基础照明，全程恒定）
    bpy.ops.object.light_add(type="AREA", location=(0.4, 0.7, 2.25))
    fill = bpy.context.active_object
    fill.data.energy = 190
    fill.data.size = 2.0
    fill.data.color = (1.0, 0.86, 0.70)
    fill.rotation_euler = (math.radians(25), 0, 0)
    # 小灯点光（结尾渐亮）
    bpy.ops.object.light_add(type="POINT", location=LAMP_POS)
    lamp = bpy.context.active_object
    lamp.data.energy = 0
    lamp.data.color = (1.0, 0.78, 0.50)
    lamp.data.shadow_soft_size = 1.1   # 软一点，墙上是渐晕而不是硬圆
    return lamp


def head_pose(arm, down, turn, lean):
    """低头/转头/前倾，四个通道已从动作里剥离，逐帧可覆盖。"""
    p14.rotate_world(arm, "mixamorig:Spine", (1, 0, 0), lean)
    p14.rotate_world(arm, "mixamorig:Spine1", (1, 0, 0), lean * 0.45)
    p14.rotate_world(arm, "mixamorig:Head", (1, 0, 0), down)
    p14.rotate_world(arm, "mixamorig:Neck", (0, 0, 1), turn)
    p14.rotate_world(arm, "mixamorig:Head", (0, 0, 1), turn * 0.55)


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    paper, pen, drawer, drawer_body, bulb_mat = build_room()
    lamp = add_lighting()

    xu, xu_acts, _ = p14.import_glb(os.path.join(MODELS, "C06", "tex_mesh_animated.glb"))
    zhou, zhou_acts, _ = p14.import_glb(os.path.join(MODELS, "C15", "tex_mesh_animated.glb"))
    print("[previs15] xu_acts", len(xu_acts), [a.name for a in xu_acts], flush=True)
    print("[previs15] zhou_acts", len(zhou_acts), [a.name for a in zhou_acts], flush=True)
    if len(xu_acts) < 5 or len(zhou_acts) < 4:
        raise RuntimeError("动作 clip 数量不符：C06 需 10 个，C15 需 4 个")

    # 提交顺序：C06 = Idle/Walk/Sitting_Enter/Sitting_Idle/Sitting_Talking/...
    #           C15 = Idle_Loop/Walk_Loop/Sitting_Enter/Sitting_Idle_Loop
    # 两者第 4 个 clip 都是 Sitting_Idle_Loop，按 clip 序号取而非列表下标
    ACT_XU_SIT = act_by_clip(xu_acts, 4)
    ACT_ZHOU_SIT = act_by_clip(zhou_acts, 4)
    print(f"[previs15] sit clips: xu={ACT_XU_SIT.name} zhou={ACT_ZHOU_SIT.name}", flush=True)
    for a in (ACT_XU_SIT, ACT_ZHOU_SIT):
        p14.make_loop(a)
    removed = p14.strip_channels([ACT_XU_SIT, ACT_ZHOU_SIT], MANUAL_BONES)
    print("[previs15] stripped", len(removed), "channels", flush=True)

    for a in (xu, zhou):
        a.rotation_mode = "XYZ"
    xu_ad, zhou_ad = xu.animation_data, zhou.animation_data

    # 脚高校正必须拿站姿 Idle 测（shot14 同法）。坐姿 clip 的骨骼原点被压低约 0.75，
    # 拿它测会把整个人抬高、臀部浮在椅面上方
    ACT_XU_IDLE = act_by_clip(xu_acts, 1)
    ACT_ZHOU_IDLE = act_by_clip(zhou_acts, 1)
    scene = bpy.context.scene
    p14.set_loop(xu_ad, ACT_XU_IDLE, {"key": None}, "idle_probe")
    p14.set_loop(zhou_ad, ACT_ZHOU_IDLE, {"key": None}, "idle_probe")
    scene.frame_set(1)
    bpy.context.view_layer.update()
    xu_dz = -p14.feet_z(xu) + 0.02
    zhou_dz = -p14.feet_z(zhou) + 0.02
    print(f"[previs15] dz xu={xu_dz:.3f} zhou={zhou_dz:.3f}", flush=True)

    # 白模统一材质（保留场景自带材质，角色染哑光白）
    matte = p14.make_matte("char_matte15", 0.82)
    for o in [o for o in scene.objects if o.type == "MESH"]:
        if o.name in ("paper", "pen", "drawer_front", "drawer_body"):
            continue
        mnames = [m.name for m in o.data.materials] if o.data.materials else []
        if any(n.startswith("s15_") for n in mnames):
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

    cam_data = bpy.data.cameras.new("previs_cam15")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam15", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    sp, ep = Vector(CAM_START), Vector(CAM_END)
    aim_static = Vector((0.40, 0.88, 0.98))

    st_x, st_z = {"key": None}, {"key": None}
    test_mode = os.environ.get("PREVIS_TEST") == "1"
    if test_mode:
        frames_iter = [1, 30, 64, 80, 100, 120, 140, 158, 170, 185, 192]
    elif os.environ.get("PREVIS_RANGE"):
        a, b = os.environ["PREVIS_RANGE"].split("-")
        frames_iter = range(int(a), int(b) + 1)
    else:
        frames_iter = range(1, N_FRAMES + 1)

    PAPER_HOME = (TABLE_CENTER[0] - 0.05, TABLE_CENTER[1] + 0.02, 0.775)
    PEN_HOME = (TABLE_CENTER[0] - 0.16, TABLE_CENTER[1] - 0.04, 0.80)
    PAPER_SCALE = tuple(paper.scale)
    for f in frames_iter:
        t = p14.ease((f - 1) / (N_FRAMES - 1))

        # ---- 动作：全程坐姿 idle，靠剥出的头/颈/脊柱通道做表情与前后态 ----
        p14.set_loop(xu_ad, ACT_XU_SIT, st_x, "sit")
        p14.set_loop(zhou_ad, ACT_ZHOU_SIT, st_z, "sit")
        xu.location = (*CHAIR_LEFT, xu_dz)
        xu.rotation_euler = (0, 0, math.radians(90))     # 面向 +x（朝桌心）
        zhou.location = (*CHAIR_RIGHT, zhou_dz)
        zhou.rotation_euler = (0, 0, math.radians(-90))  # 面向 -x（朝桌心）
        scene.frame_set(f)

        # 许宁：f1-64 低头算 → f65-92 停笔抬头 → f93-124 说话 → f125-160 收纸低头 → 结尾静坐
        if f <= 64:
            xu_down, xu_lean = 10.0, 6.0
            xu_turn = 0.0
        elif f <= 92:
            k = p14.ease((f - 65) / 27)
            xu_down, xu_lean = 10.0 * (1 - k), 6.0 * (1 - k)
            xu_turn = 0.0
        elif f <= 124:
            xu_down, xu_lean, xu_turn = 0.0, 0.0, 0.0
        elif f <= 160:
            k = p14.ease((f - 125) / 20)
            xu_down, xu_lean = 5.0 * k, 3.5 * k
            xu_turn = 0.0
        else:
            k = p14.ease((f - 161) / 20)
            xu_down, xu_lean = 5.0 * (1 - k), 3.5 * (1 - k)
            xu_turn = 0.0
        # 说话时头极轻的点动（不引入突变）
        if 93 <= f <= 124:
            xu_down += 2.2 * math.sin((f - 93) / 7.0)
        head_pose(xu, xu_down, xu_turn, xu_lean)

        # 周远：f1-104 低头算 → f105-124 停笔抬头 → 结尾与她对视、静坐
        if f <= 104:
            zh_down, zh_lean = 9.0, 5.0
        elif f <= 124:
            k = p14.ease((f - 105) / 19)
            zh_down, zh_lean = 9.0 * (1 - k), 5.0 * (1 - k)
        else:
            zh_down, zh_lean = 0.0, 0.0
        head_pose(zhou, zh_down, 0.0, zh_lean)

        # ---- 道具：笔（斜立点算 → 平放） ----
        if f <= 64:
            amp = math.sin(f / 5.5)
            pen.location = (PEN_HOME[0] + 0.010 * amp, PEN_HOME[1], PEN_HOME[2])
            pen.rotation_euler = (math.radians(28), math.radians(12 * amp), 0)
        elif f <= 92:
            k = p14.ease((f - 65) / 27)
            pen.location = (PEN_HOME[0], PEN_HOME[1], PEN_HOME[2] - 0.012 * k)
            # 圆柱轴线初始沿 z，要躺平必须绕 x 转 90°；绕 z 转对竖直圆柱没有效果
            pen.rotation_euler = (math.radians(28 + 62 * k), 0, 0)
        else:
            pen.location = (PEN_HOME[0], PEN_HOME[1], PEN_HOME[2] - 0.012)
            pen.rotation_euler = (math.radians(90), 0, 0)

        # ---- 道具：纸（桌面 → 收拢抬起 → 入抽屉消失）与抽屉（合 → 拉 → 合）----
        DRAWER_Y = 0.62          # 合上：藏在桌板下
        DRAWER_BODY_Y = 0.80
        PAPER_LIFT = (0.12, 0.66, 0.805)  # 贴着桌面滑向抽屉，不悬空飘
        DRAWER_IN = (0.10, 0.52, 0.64)    # 再落进已拉出的抽屉
        if f <= 124:
            paper.location = PAPER_HOME
            paper.scale = PAPER_SCALE
            paper.rotation_euler = (0, 0, 0)
            drawer.location.y = DRAWER_Y
            drawer_body.location.y = DRAWER_BODY_Y
        else:
            k_open = p14.ease((f - 125) / 15) if f <= 140 else 1.0
            k_close = p14.ease((f - 152) / 13) if f >= 152 else 0.0
            dy = (0.0 if f <= 125 else 0.22 * k_open) * (1 - k_close)
            drawer.location.y = DRAWER_Y - dy
            drawer_body.location.y = DRAWER_BODY_Y - dy
            if f <= 140:
                k = p14.ease((f - 125) / 15)
                paper.location = tuple(a + (b - a) * k
                                       for a, b in zip(PAPER_HOME, PAPER_LIFT))
                paper.rotation_euler = (math.radians(18 * k), 0, math.radians(12 * k))
            elif f <= 152:
                k = p14.ease((f - 141) / 11)
                paper.location = tuple(a + (b - a) * k
                                       for a, b in zip(PAPER_LIFT, DRAWER_IN))
                paper.rotation_euler = (math.radians(18), 0, math.radians(12))
                paper.scale = tuple(s * (1 - 0.82 * k) for s in PAPER_SCALE)
            else:
                paper.scale = tuple(s * 0.001 for s in PAPER_SCALE)
                paper.location = DRAWER_IN

        # ---- 道具：窗台小灯渐亮（f161-192）----
        k_lamp = p14.ease((f - 161) / 26) if f >= 161 else 0.0
        lamp.data.energy = 330.0 * k_lamp
        for n in bulb_mat.node_tree.nodes:
            if n.bl_idname == "ShaderNodeBsdfPrincipled":
                n.inputs["Emission Strength"].default_value = 0.05 + 1.25 * k_lamp

        # ---- 相机：缓慢推近 + 轻微手持 ----
        cam.location = sp.lerp(ep, t)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (aim_static - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs15] frame {f}/{N_FRAMES}", flush=True)

    # 分三段渲时由最后一段负责写报告（避免重跑全帧只为拿 json）
    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot15", "title": "再攒两年", "source": "剧本五 L269-275",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E09 朝北出租屋折叠餐桌（与 shot13 同坐标）",
            "table": TABLE_CENTER, "chair_left": CHAIR_LEFT, "chair_right": CHAIR_RIGHT,
            "camera": [list(CAM_START), list(CAM_END)],
            "lamp": LAMP_POS,
            "timeline": {
                "f1-64": "两人低头算账，纸摊桌面、许宁执笔点算",
                "f65-92": "许宁停笔，笔渐平放，抬头看向周远",
                "f93-124": "许宁说再攒两年吧；周远 f105-124 停笔抬头，两人对视",
                "f125-160": "抽屉拉出、纸收拢抬起入柜、抽屉合上",
                "f161-192": "窗台小灯渐亮，墙上暖光晕开，两人静坐",
            },
            "characters": {"xu": "C06 ten-clip / clip 4 = Sitting_Idle_Loop（按名称取，非列表下标）",
                           "zhou": "C15 four-clip / clip 4.001 = Sitting_Idle_Loop"},
        }
        with open(os.path.join(OUT_DIR, "previs15_report.json"), "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS15_DONE", flush=True)


if __name__ == "__main__":
    main()
