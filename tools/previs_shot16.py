# -*- coding: utf-8 -*-
"""白模预演：shot16「婚礼·胸针与旧发带」（剧本五 L277-283）。

场景：E09 折叠餐桌，婚礼办得很简单，桌面铺一块浅色桌布（不新建宴会厅）。
白天暖光，与 E09_v01 参考图同族；窗台小灯沿用 shot15 结尾的道具但恒定不渐亮。

三人都用**站姿 Idle**：C10 妈妈只有 2 个 clip（animation_1=Walk / animation_2=Idle），
没有坐姿动作，硬摆坐姿会腿部穿模；三人站立也符合「敬酒前」的情境。

站位（相机在 y 负方向，模型默认面向 -y）：
- 妈妈 C10  (-0.75, 0.55)  yaw +48°  画面左前景
- 许宁 C06  ( 0.10, 0.42)  yaw -48°  画面左前景、与妈妈相距 0.86m，伸手够得到胸口
- 周远 C15  ( 1.75, 1.35)  yaw -12°  桌后偏右，安静在场
桌子中心 (0.55, 1.05)，桌面在前景两人身后，发带与小包不被身体遮挡。

时间轴（192f / 8s），变化三态全部写成渐变，无硬切：
- f1-48    三人站定（前态）：妈妈暗红外套上胸针明显歪 28°，话说一半停住、头微低；
           许宁看着妈妈，旧发带摊在桌面，小包空着搁在椅面上
- f49-96   扶正胸针（过程）：许宁上身渐前倾、头转向妈妈、身体微靠近 0.12m，
           胸针角度 28° → 0°（f70-96 归零），妈妈低头看自己胸口
- f97-136  握住手（后态第一层）：许宁轻轻点头说「我知道」，妈妈缓缓抬头，
           两人上身各向对方靠近 0.04m
- f137-176 叠旧发带（再一层变化）：许宁回正转向桌面，发带沿长度折叠变短、
           移向包口、渐隐入包（前态：摊开在桌面 → 过程：折短并平移
           → 后态：完全在包内）
- f177-192 收束：小包稳定搁在椅面（椅背旁），三人静立，镜头微推

硬约束：三人全程双脚贴地、无走位（避免滑步）、无穿模悬浮；胸针/发带/小包不漂浮
不瞬移；无第四人；三张脸不互换；所有段间切换用 ease 渐变。

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot16.py
  set PREVIS_RANGE=1-64 && blender.exe --background --python tools/previs_shot16.py
  blender.exe --background --python tools/previs_shot16.py
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
FRAMES_DIR = os.path.join(OUT_DIR, "frames16")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720

TABLE_CENTER = (0.55, 1.05)
MOM_POS = (-0.75, 0.55)
XU_POS = (0.10, 0.42)
ZHOU_POS = (1.75, 1.35)
MOM_YAW = math.radians(48)
XU_YAW = math.radians(-48)
ZHOU_YAW = math.radians(-12)

WIN_X0, WIN_X1 = -2.7, -1.3
WIN_Z0, WIN_Z1 = 1.15, 2.35
WALL_Y = 3.2
CAM_START = (0.15, -3.55, 1.50)
CAM_END = (0.28, -3.20, 1.46)
CAM_LENS = 30

BAG_POS = (0.98, 0.30, 0.54)          # 小包中心，搁在第三把椅子的椅面上
BAG_MOUTH = (0.98, 0.30, 0.655)
RIBBON_FOLD_END = (0.98, 0.62, 0.782)  # 桌面右前角，仍在桌布范围内
RIBBON_HOME = (0.40, 0.80, 0.782)     # 旧发带摊在桌布上
BROOCH_TILT_DEG = 28.0                # 胸针初始歪斜角

MANUAL_BONES = ("mixamorig:Head", "mixamorig:Neck",
                "mixamorig:Spine", "mixamorig:Spine1")


def mat(key, shade, emission=None):
    return p14.mat("s16_" + key, shade, emission)


def add_chair(name, px, py, shade=0.55):
    """一把木椅；椅子不坐人，只作场景与放包的道具。"""
    c = mat("chair", shade)
    p14.add_box(f"{name}_seat", (px, py, 0.44), (0.45, 0.45, 0.05), c)
    # 椅背用栏杆而不是整块板：实心方板正对相机时会被读成「一块板子长出来」，
    # 还会挡住后面的人（HANDOFF §5.15 的坑，shot16 首版已踩过一次）
    for dx in (-0.17, 0.17):
        p14.add_box(f"{name}_post_{dx}", (px + dx, py + 0.20, 0.75),
                    (0.045, 0.045, 0.60), c)
    for z in (0.62, 0.99):
        p14.add_box(f"{name}_rail_{z}", (px, py + 0.20, z),
                    (0.40, 0.045, 0.05), c)
    for lx in (-0.18, 0.18):
        for ly in (-0.18, 0.18):
            p14.add_box(f"{name}_leg_{lx}_{ly}", (px + lx, py + ly, 0.22),
                        (0.04, 0.04, 0.44), c)


def build_room():
    """E09 白天版：折叠餐桌 + 浅色桌布 + 三把木椅 + 后墙窗 + 窗台小灯。"""
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
    p14.add_box("win_f_h", (cx, WALL_Y - 0.03, WIN_Z1), (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    p14.add_box("win_f_b", (cx, WALL_Y - 0.03, WIN_Z0), (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    p14.add_box("win_f_m", (cx, WALL_Y - 0.03, cz), (0.05, 0.08, WIN_Z1 - WIN_Z0), frame)
    # 白天亮窗（E09_v01 是白天）；shot15 的 night 材质在这里换成暖白日光
    p14.add_box("daylight", (cx, WALL_Y + 3.0, 1.8), (7.0, 0.1, 3.6),
                mat("daylight", 0.72, emission=(0.60, 0.64, 0.70, 1.0)))
    p14.add_box("windowsill", (cx, WALL_Y - 0.22, WIN_Z0 - 0.03),
                (WIN_X1 - WIN_X0 + 0.24, 0.42, 0.05), mat("sill", 0.68))
    p14.add_box("curtain", (WIN_X0 - 0.12, WALL_Y - 0.12, 1.75),
                (0.34, 0.05, 1.20), mat("curtain", 0.82))
    # 窗台小灯：shot15 结尾添的那盏，本场恒定亮着，不再做渐亮
    lamp_pos = (cx + 0.18, WALL_Y - 0.22, WIN_Z0 + 0.06)
    p14.add_cyl("lamp_base", lamp_pos, 0.075, 0.05, mat("lamp_base", 0.52))
    p14.add_cyl("lamp_shade", (lamp_pos[0], lamp_pos[1], lamp_pos[2] + 0.16),
                0.10, 0.15, mat("lamp_shade", 0.76))

    # 折叠方桌 + 婚礼的简单浅色桌布
    tx, ty = TABLE_CENTER
    p14.add_box("table_top", (tx, ty, 0.74), (1.55, 1.0, 0.05), mat("table", 0.62))
    p14.add_box("tablecloth", (tx, ty, 0.769), (1.62, 1.06, 0.012), mat("cloth", 0.88))
    for dx in (-0.65, 0.65):
        p14.add_box(f"table_leg_{dx}", (tx + dx, ty, 0.37), (0.05, 0.85, 0.72),
                    mat("leg", 0.45))
    # 桌上：两只碗 + 暖壶，呼应 E09 与 shot13「两只碗」
    for i, wx in enumerate((tx - 0.38, tx + 0.30)):
        p14.add_cyl(f"bowl_{i}", (wx, ty + 0.12, 0.815), 0.085, 0.055,
                    mat("bowl", 0.86))
    p14.add_cyl("thermos", (tx + 0.55, ty - 0.30, 0.90), 0.055, 0.32,
                mat("thermos", 0.50))
    # 预演不放矮柜：它正对镜头会被读成「一块板子长出来」并挡住第三人下半身；
    # E09 参考图里那只木柜交给 H3 由 <Picture 4> 补齐，白模只留关键道具

    add_chair("chair_left", -0.75, 0.98)
    add_chair("chair_right", 1.55, 0.98)
    add_chair("chair_bag", BAG_POS[0], BAG_POS[1])

    # ---- 三件驱动道具 ----
    # 胸针：细长条贴在妈妈左胸，初始绕 y 轴歪 28°（在屏幕 xz 平面内可见倾斜）
    brooch = p14.add_box("brooch", (0, 0, 1.3), (0.14, 0.020, 0.014),
                         mat("brooch", 0.32))  # 加深，白模上才看得见倾斜
    brooch.rotation_euler = (0, math.radians(BROOCH_TILT_DEG), 0)
    # 旧发带：细长条摊在桌布上
    ribbon = p14.add_box("ribbon", RIBBON_HOME, (0.42, 0.030, 0.006),
                         mat("ribbon", 0.70))
    # 小包：搁在第三把椅子的椅面上，位置恒定
    bag = p14.add_box("bag", BAG_POS, (0.24, 0.16, 0.20), mat("bag", 0.58))
    # 不再追加包盖薄片：作为场景里最后一个几何体，它的 dimensions 写入
    # 尚未被依赖图评估就被渲染，会保持 1m 立方体挡住整幅画面（见下方 update）

    # add_box 用 dimensions 实现尺寸，本质是 scale；后续驱动必须基于这个基准，
    # 直接写 (1,1,1) 会把薄片还原成 1 米立方体挡住画面（HANDOFF §5.15）
    RIBBON_SCALE = tuple(ribbon.scale)
    # 强制刷新依赖图：add_box 靠 box.dimensions 写 scale，最后创建的那一个
    # 若没有后续对象触发评估，渲染时会保持默认 1x1x1，变成挡画面的大方块
    bpy.context.view_layer.update()
    print(f"[previs16] base scale ribbon={tuple(round(v,4) for v in RIBBON_SCALE)}", flush=True)
    return brooch, ribbon, bag, RIBBON_SCALE


def add_lighting():
    world = bpy.data.worlds.new("previz_world16")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.24, 0.25, 0.28, 1.0)
            n.inputs[1].default_value = 0.85
    bpy.context.scene.world = world
    # 窗外日光（白天）
    bpy.ops.object.light_add(type="AREA", location=((WIN_X0 + WIN_X1) / 2, WALL_Y + 1.6, 2.0))
    key = bpy.context.active_object
    key.data.energy = 220
    key.data.size = 3.2
    key.data.color = (0.92, 0.94, 1.0)
    key.rotation_euler = (math.radians(65), 0, math.radians(180))
    # 桌面暖光，全程恒定（本场无渐亮）
    bpy.ops.object.light_add(type="AREA", location=(0.55, 0.7, 2.30))
    fill = bpy.context.active_object
    fill.data.energy = 150
    fill.data.size = 2.2
    fill.data.color = (1.0, 0.88, 0.74)
    fill.rotation_euler = (math.radians(25), 0, 0)


def act_by_clip(acts, n):
    """按 glb 内 clip 序号取 action（HANDOFF §5.14：bpy 按名称字典序排）。"""
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


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    brooch, ribbon, bag, RIBBON_SCALE = build_room()
    add_lighting()

    mom, mom_acts, _ = p14.import_glb(
        os.path.join(MODELS, "C10", "tex_mesh_v08_animated.glb"))
    xu, xu_acts, _ = p14.import_glb(
        os.path.join(MODELS, "C06", "tex_mesh_animated.glb"))
    zhou, zhou_acts, _ = p14.import_glb(
        os.path.join(MODELS, "C15", "tex_mesh_animated.glb"))
    print("[previs16] acts mom", [a.name for a in mom_acts], flush=True)
    print("[previs16] acts xu ", [a.name for a in xu_acts], flush=True)
    print("[previs16] acts zhou", [a.name for a in zhou_acts], flush=True)

    # C10 只有 2 clip：1=Walk / 2=Idle（见 previs_shot06.py 的映射）
    ACT_MOM = act_by_clip(mom_acts, 2)
    ACT_XU = act_by_clip(xu_acts, 1)       # Idle_Loop
    ACT_ZHOU = act_by_clip(zhou_acts, 1)   # Idle_Loop
    print(f"[previs16] idle clips: mom={ACT_MOM.name} xu={ACT_XU.name} zhou={ACT_ZHOU.name}",
          flush=True)
    for a in (ACT_MOM, ACT_XU, ACT_ZHOU):
        p14.make_loop(a)
    removed = p14.strip_channels([ACT_MOM, ACT_XU, ACT_ZHOU], MANUAL_BONES)
    print("[previs16] stripped", len(removed), "channels", flush=True)

    for a in (mom, xu, zhou):
        a.rotation_mode = "XYZ"
    st_m, st_x, st_z = {"key": None}, {"key": None}, {"key": None}
    scene = bpy.context.scene
    p14.set_loop(mom.animation_data, ACT_MOM, st_m, "idle")
    p14.set_loop(xu.animation_data, ACT_XU, st_x, "idle")
    p14.set_loop(zhou.animation_data, ACT_ZHOU, st_z, "idle")
    scene.frame_set(1)
    bpy.context.view_layer.update()
    dz_m = -p14.feet_z(mom) + 0.02
    dz_x = -p14.feet_z(xu) + 0.02
    dz_z = -p14.feet_z(zhou) + 0.02
    print(f"[previs16] dz mom={dz_m:.3f} xu={dz_x:.3f} zhou={dz_z:.3f}", flush=True)

    # 白模统一材质：角色染哑光白，场景 s16_* 与三件道具保留自身 shade
    matte = p14.make_matte("char_matte16", 0.82)
    for o in [o for o in scene.objects if o.type == "MESH"]:
        if o.name in ("brooch", "ribbon", "bag"):
            continue
        mnames = [m.name for m in o.data.materials] if o.data.materials else []
        if any(n.startswith("s16_") for n in mnames):
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

    cam_data = bpy.data.cameras.new("previs_cam16")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam16", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    sp, ep = Vector(CAM_START), Vector(CAM_END)
    aim_static = Vector((0.38, 0.95, 0.98))

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    if test_mode:
        frames_iter = [1, 24, 48, 68, 88, 110, 136, 150, 168, 180, 192]
    elif os.environ.get("PREVIS_RANGE"):
        a, b = os.environ["PREVIS_RANGE"].split("-")
        frames_iter = range(int(a), int(b) + 1)
    else:
        frames_iter = range(1, N_FRAMES + 1)

    # 妈妈胸口方向：面向 -y 时 yaw=0，旋转 yaw 后的前向量与左向量
    d = Vector((math.sin(MOM_YAW), -math.cos(MOM_YAW), 0))
    left = Vector((math.cos(MOM_YAW), math.sin(MOM_YAW), 0))
    mom_pos_v = Vector((*MOM_POS, 0))
    xu_pos_v = Vector((*XU_POS, 0))

    for f in frames_iter:
        t = p14.ease((f - 1) / (N_FRAMES - 1))

        p14.set_loop(mom.animation_data, ACT_MOM, st_m, "idle")
        p14.set_loop(xu.animation_data, ACT_XU, st_x, "idle")
        p14.set_loop(zhou.animation_data, ACT_ZHOU, st_z, "idle")

        # ---- 站位：全程不走位，只做 <0.12m 的靠近渐变（无滑步）----
        if f <= 48:
            k_near, k_hand = 0.0, 0.0
        elif f <= 96:
            k_near = p14.ease((f - 49) / 47)
            k_hand = 0.0
        elif f <= 136:
            k_near = 1.0
            k_hand = p14.ease((f - 97) / 39)
        else:
            k_back = p14.ease((f - 137) / 24)
            k_near, k_hand = 1.0 - k_back, 0.0

        mom.location = (*MOM_POS, dz_m)
        mom.rotation_euler = (0, 0, MOM_YAW)
        xu.location = (XU_POS[0] - 0.12 * k_near - 0.04 * k_hand,
                       XU_POS[1] + 0.03 * k_near, dz_x)
        xu.rotation_euler = (0, 0, XU_YAW)
        zhou.location = (*ZHOU_POS, dz_z)
        zhou.rotation_euler = (0, 0, ZHOU_YAW)
        scene.frame_set(f)

        # ---- 头/上身：许宁前倾看妈妈 → 轻点头 → 回正转向桌面 ----
        if f <= 48:
            xu_down, xu_lean, xu_turn = 2.0, 1.5, -6.0
        elif f <= 96:
            k = p14.ease((f - 49) / 47)
            xu_down, xu_lean = 2.0 + 6.0 * k, 1.5 + 7.0 * k
            xu_turn = -6.0 + 6.0 * k
        elif f <= 136:
            xu_down, xu_lean, xu_turn = 8.0, 8.5, 0.0
            xu_down += 2.0 * math.sin((f - 97) / 8.0)   # 说「我知道」时轻点头
        elif f <= 176:
            k = p14.ease((f - 137) / 30)
            xu_down, xu_lean = 8.0 * (1 - k) + 9.0 * k, 8.5 * (1 - k) + 5.0 * k
            xu_turn = 14.0 * k                          # 转头看桌面上的发带
        else:
            k = p14.ease((f - 177) / 15)
            xu_down, xu_lean, xu_turn = 9.0 * (1 - k), 5.0 * (1 - k), 14.0 * (1 - k)
        head_pose(xu, xu_down, xu_turn, xu_lean)

        # 妈妈：话说一半停住 → 低头看胸口 → 缓缓抬头
        if f <= 48:
            mo_down, mo_turn = 5.0, 8.0
        elif f <= 96:
            k = p14.ease((f - 49) / 47)
            mo_down, mo_turn = 5.0 + 7.0 * k, 8.0 * (1 - k)
        elif f <= 136:
            k = p14.ease((f - 97) / 39)
            mo_down, mo_turn = 12.0 * (1 - k), 0.0
        else:
            mo_down, mo_turn = 0.0, 0.0
        head_pose(mom, mo_down, mo_turn, 1.0 + 2.0 * k_hand)

        # 周远：全程静立，只做极轻的呼吸式点头
        head_pose(zhou, 1.5 + 0.8 * math.sin(f / 21.0), 0.0, 0.0)

        # ---- 胸针：贴着妈妈 Spine2 走，歪 28° → 在 f70-96 渐变归零 ----
        sp2 = mom.matrix_world @ mom.pose.bones["mixamorig:Spine2"].head
        brooch.location = sp2 + d * 0.135 + left * 0.09 + Vector((0, 0, 0.035))
        k_fix = p14.ease((f - 70) / 26) if f >= 70 else 0.0
        brooch.rotation_euler = (0, math.radians(BROOCH_TILT_DEG * (1 - k_fix)), 0)

        # ---- 旧发带：摊开 → 沿长度折短并平移到包口 → 渐隐入包 ----
        if f <= 136:
            ribbon.location = RIBBON_HOME
            ribbon.scale = RIBBON_SCALE
            ribbon.rotation_euler = (0, 0, 0)
        elif f <= 160:
            k = p14.ease((f - 137) / 23)
            # 全程贴着桌布滑向右前角，不抬离桌面；否则从相机看像条子飘在空中
            ribbon.location = tuple(a + (b - a) * k
                                    for a, b in zip(RIBBON_HOME, RIBBON_FOLD_END))
            ribbon.scale = (RIBBON_SCALE[0] * (1 - 0.62 * k),
                            RIBBON_SCALE[1], RIBBON_SCALE[2])
            ribbon.rotation_euler = (0, 0, math.radians(18 * k))
        else:
            k = p14.ease((f - 161) / 15)
            ribbon.location = RIBBON_FOLD_END
            s = (1 - 0.62) * (1 - 0.995 * k)
            ribbon.scale = tuple(v * s for v in RIBBON_SCALE)
            ribbon.rotation_euler = (0, 0, math.radians(18))

        # 小包全程恒定，只是被「放进」——不做位移，避免漂浮感
        bag.location = BAG_POS

        # ---- 相机：缓慢推近 + 轻微手持 ----
        cam.location = sp.lerp(ep, t)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (aim_static - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs16] frame {f}/{N_FRAMES}", flush=True)

    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot16", "title": "婚礼·胸针与旧发带", "source": "剧本五 L277-283",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E09 折叠餐桌白天版，铺浅色桌布（婚礼办得很简单）",
            "layout": "三人围桌站立；C10 只有走/站两个 clip，无坐姿动作，故全用站姿 Idle",
            "table": TABLE_CENTER,
            "positions": {"mom_C10": MOM_POS, "xu_C06": XU_POS, "zhou_C15": ZHOU_POS},
            "yaw_deg": {"mom": 48, "xu": -48, "zhou": -12},
            "props": {"brooch_tilt_deg": BROOCH_TILT_DEG, "ribbon_home": RIBBON_HOME,
                      "bag": BAG_POS, "bag_mouth": BAG_MOUTH, "ribbon_fold_end": RIBBON_FOLD_END},
            "camera": [list(CAM_START), list(CAM_END)],
            "timeline": {
                "f1-48": "三人站定，妈妈胸针歪 28°、话说一半停住；发带摊在桌布上，小包空置",
                "f49-96": "许宁前倾靠近、胸针 f70-96 渐变扶正到 0°，妈妈低头看胸口",
                "f97-136": "许宁轻点头说我知道，妈妈缓缓抬头，两人上身各自微靠近",
                "f137-176": "许宁回正转向桌面，发带折短、平移到包口、渐隐入包",
                "f177-192": "小包稳定搁在椅面（椅背旁），三人静立，镜头微推",
            },
            "characters": {"mom": "C10 clip 2 = Idle（clip 1 是 Walk）",
                           "xu": "C06 ten-clip / clip 1 = Idle_Loop",
                           "zhou": "C15 four-clip / clip 1 = Idle_Loop"},
            "hard_constraints": "三人双脚贴地、无走位、胸针/发带/小包不漂浮不瞬移、无第四人、段间全 ease 渐变",
        }
        with open(os.path.join(OUT_DIR, "previs16_report.json"), "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS16_DONE", flush=True)


if __name__ == "__main__":
    main()
