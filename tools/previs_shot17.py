# -*- coding: utf-8 -*-
"""白模预演：shot17「我自己来」（剧本六 L285-303，方案 §4）。

场景：E09 折叠餐桌白天版，与 shot16 同族（不新建门口场景；门由 H3 prompt 补）。
两人**并坐**在桌子靠窗一侧、微微相对，一起看妈妈手里的手机。
相机在桌子正前方（y 负），两张略侧的正脸、桌面与背景的窗都能入镜。

站位（模型默认面向 -y，即面向相机；yaw 让两人微微相对）：
- 许宁 C06  (-0.05, 1.72)  yaw +10°  画面左
- 妈妈 C11  ( 0.80, 1.72)  yaw -10°  画面右
- 桌子中心 (0.40, 1.05)；手机在妈妈手里、略偏向两人中间

时间轴（192f / 8s），变化三态全部写成渐变，无硬切：
- f1-48    教第一遍（前态）：手机在妈妈手里、屏幕朝向两人；许宁侧身指屏幕，
           妈妈低头点了一下屏幕
- f49-96   教第二遍：妈妈第二次仍点错（f70-82 手机轻颤），许宁前倾加大、头略低
- f97-136  **核心动作**：许宁的手渐伸向手机想代劳（reach 0→1，f97-124）；
           f121 起妈妈开始把手机往自己身前收回
- f137-168 手机收回完成（f137-156）；许宁的手在半空停住后渐收回（f149-176），
           妈妈缓缓抬头看向女儿
- f169-192 许宁收回手、上身回正、重新开口（头轻点）；手机稳定在妈妈手里，
           两人并坐静下来，镜头微推

三态（手机）：前态 (0.55,1.38,0.95) 略偏中间 → 过程沿 +x/+y 渐移 →
              后态 (0.70,1.55,1.00) 更靠妈妈。全程在手里、不落桌、不消失、不转手。
三态（许宁右手）：指屏幕 → 渐伸向手机 → 停在半空 → 渐收回体侧。

硬约束：两人全程坐在椅面上、脚贴地；椅子/桌子/碗/暖壶/叠好的小衣服不移动；
手机不漂浮不瞬移不消失、始终在妈妈手中；无第三人；所有段间切换用 ease 渐变。

已知坑（HANDOFF §5）已规避：
  §5.14 按 clip 序号名称取 action、脚高用站姿 Idle 测
  §5.15 add_box 的 dimensions 本质是 scale，驱动道具按倍率缩放
  §5.16 build_room() 末尾补 view_layer.update()，最后创建的几何体才不会保持 1x1x1
  §5.17 椅背用镂空栏杆而非实心板

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot17.py
  set PREVIS_RANGE=1-64 && blender.exe --background --python tools/previs_shot17.py
  blender.exe --background --python tools/previs_shot17.py
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
FRAMES_DIR = os.path.join(OUT_DIR, "frames17")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720

TABLE_CENTER = (0.40, 1.05)
SEAT_XU = (-0.05, 1.72)
SEAT_MOM = (0.80, 1.72)
YAW_XU = math.radians(10)
YAW_MOM = math.radians(-10)

WIN_X0, WIN_X1 = -2.7, -1.3
WIN_Z0, WIN_Z1 = 1.15, 2.35
WALL_Y = 3.2
CAM_START = (0.38, -1.95, 1.34)
CAM_END = (0.42, -1.78, 1.32)
CAM_LENS = 40

PHONE_HOME = (0.40, 1.32, 0.845)    # 略偏向两人中间、贴近桌布上方，屏幕朝双方
PHONE_END = (0.86, 1.58, 0.865)     # 往妈妈身前收回约 0.5m，位移在画面里可辨
PHONE_DIMS = (0.080, 0.150, 0.008)  # 手机薄片

# 许宁右臂通道从坐姿 idle 里剥出来逐帧手 K；妈妈保留 idle 的臂通道
MANUAL_BONES_MOM = ("mixamorig:Head", "mixamorig:Neck",
                    "mixamorig:Spine", "mixamorig:Spine1",
                    "mixamorig:RightArm", "mixamorig:RightForeArm",
                    "mixamorig:RightHand")
MANUAL_BONES_XU = MANUAL_BONES_MOM + (
    "mixamorig:RightArm", "mixamorig:RightForeArm", "mixamorig:RightHand")


def mat(key, shade, emission=None):
    return p14.mat("s17_" + key, shade, emission)


def add_chair(name, px, py, shade=0.55):
    """镂空栏杆椅背（HANDOFF §5.17），不用整块实心板。"""
    c = mat("chair", shade)
    p14.add_box(f"{name}_seat", (px, py, 0.44), (0.45, 0.45, 0.05), c)
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
    """E09 白天版：折叠餐桌 + 浅色桌布 + 两把并排木椅 + 后墙窗 + 窗台小灯。"""
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
    p14.add_box("daylight", (cx, WALL_Y + 3.0, 1.8), (7.0, 0.1, 3.6),
                mat("daylight", 0.72, emission=(0.60, 0.64, 0.70, 1.0)))
    p14.add_box("windowsill", (cx, WALL_Y - 0.22, WIN_Z0 - 0.03),
                (WIN_X1 - WIN_X0 + 0.24, 0.42, 0.05), mat("sill", 0.68))
    p14.add_box("curtain", (WIN_X0 - 0.12, WALL_Y - 0.12, 1.75),
                (0.34, 0.05, 1.20), mat("curtain", 0.82))
    lamp_pos = (cx + 0.18, WALL_Y - 0.22, WIN_Z0 + 0.06)
    p14.add_cyl("lamp_base", lamp_pos, 0.075, 0.05, mat("lamp_base", 0.52))
    p14.add_cyl("lamp_shade", (lamp_pos[0], lamp_pos[1], lamp_pos[2] + 0.16),
                0.10, 0.15, mat("lamp_shade", 0.76))

    # 折叠方桌 + 桌布（与 E09 / shot16 同坐标同尺寸）
    tx, ty = TABLE_CENTER
    p14.add_box("table_top", (tx, ty, 0.74), (1.55, 1.0, 0.05), mat("table", 0.62))
    p14.add_box("tablecloth", (tx, ty, 0.769), (1.62, 1.06, 0.012), mat("cloth", 0.88))
    for dx in (-0.65, 0.65):
        p14.add_box(f"table_leg_{dx}", (tx + dx, ty, 0.37), (0.05, 0.85, 0.72),
                    mat("leg", 0.45))
    for i, wx in enumerate((tx - 0.38, tx + 0.30)):
        p14.add_cyl(f"bowl_{i}", (wx, ty + 0.12, 0.815), 0.085, 0.055,
                    mat("bowl", 0.86))
    p14.add_cyl("thermos", (tx + 0.55, ty - 0.30, 0.90), 0.055, 0.32,
                mat("thermos", 0.50))
    # 剧本 L297「妈妈低头叠孩子的小衣服」：桌上一叠折好的小衣服，静态道具
    p14.add_box("baby_clothes_1", (tx - 0.30, ty - 0.20, 0.790),
                (0.28, 0.20, 0.025), mat("clothes", 0.90))
    p14.add_box("baby_clothes_2", (tx - 0.29, ty - 0.19, 0.812),
                (0.26, 0.18, 0.022), mat("clothes", 0.94))
    # 车票 / 便签，静态
    p14.add_box("ticket", (tx + 0.15, ty - 0.24, 0.782),
                (0.22, 0.11, 0.004), mat("ticket", 0.88))

    add_chair("chair_xu", *SEAT_XU)
    add_chair("chair_mom", *SEAT_MOM)

    # 手机：唯一的驱动道具，全程在妈妈手里
    phone = p14.add_box("phone", PHONE_HOME, PHONE_DIMS, mat("phone", 0.30))
    phone.rotation_euler = (math.radians(-18), 0, math.radians(8))

    PHONE_SCALE = tuple(phone.scale)
    # 强制刷新依赖图：最后一个 add_box 的 dimensions 需要评估才生效（HANDOFF §5.16）
    bpy.context.view_layer.update()
    print(f"[previs17] base scale phone={tuple(round(v,4) for v in PHONE_SCALE)}", flush=True)
    return phone, PHONE_SCALE


def add_lighting():
    world = bpy.data.worlds.new("previz_world17")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.24, 0.25, 0.28, 1.0)
            n.inputs[1].default_value = 0.85
    bpy.context.scene.world = world
    bpy.ops.object.light_add(type="AREA", location=((WIN_X0 + WIN_X1) / 2, WALL_Y + 1.6, 2.0))
    key = bpy.context.active_object
    key.data.energy = 220
    key.data.size = 3.2
    key.data.color = (0.92, 0.94, 1.0)
    key.rotation_euler = (math.radians(65), 0, math.radians(180))
    bpy.ops.object.light_add(type="AREA", location=(0.40, 0.7, 2.30))
    fill = bpy.context.active_object
    fill.data.energy = 150
    fill.data.size = 2.2
    fill.data.color = (1.0, 0.88, 0.74)
    fill.rotation_euler = (math.radians(25), 0, 0)


def act_by_clip(acts, n):
    """按 glb 内的 clip 序号取 action（HANDOFF §5.14）。"""
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


def xu_right_arm(arm, reach):
    """许宁右手：reach=0 指屏幕（半抬），reach=1 伸向手机。

    右臂通道已从 idle 里剥出，这里每帧覆盖式写入。世界轴角度以
    PREVIS_TEST 的测试帧目检为准，若方向相反在此处调符号即可。
    """
    p14.rotate_ops(arm, "mixamorig:RightArm", [
        ((0, 1, 0), -62 + 6 * reach),
        ((1, 0, 0), -26 - 12 * reach),
        ((0, 0, 1), 10 + 8 * reach),
    ])
    p14.rotate_ops(arm, "mixamorig:RightForeArm", [
        ((0, 1, 0), 18 + 8 * reach),
        ((1, 0, 0), -14 - 8 * reach),
    ])


def mom_right_arm(arm, k):
    """妈妈右臂：k=0 持机略伸向两人中间 → k=1 把手机收回自己身前。

    通道已从坐姿 idle 剥出，逐帧覆盖写入；手机位置直接跟随 RightHand 骨骼，
    所以这里的旋转就是「把手机往回一收」的运动通道本身（HANDOFF §5.19）。
    角度以 PREVIS_TEST 目检为准，方向反了在此处调符号。
    """
    p14.rotate_ops(arm, "mixamorig:RightArm", [
        ((0, 1, 0), -46 - 10 * k),
        ((1, 0, 0), -16 - 10 * k),
        ((0, 0, 1), 16 + 16 * k),
    ])
    p14.rotate_ops(arm, "mixamorig:RightForeArm", [
        ((0, 1, 0), 20 + 14 * k),
        ((1, 0, 0), -10 - 8 * k),
    ])


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    phone, PHONE_SCALE = build_room()
    add_lighting()

    xu, xu_acts, _ = p14.import_glb(os.path.join(MODELS, "C06", "tex_mesh_animated.glb"))
    mom, mom_acts, _ = p14.import_glb(os.path.join(MODELS, "C11", "tex_mesh_animated.glb"))
    print("[previs17] xu_acts", len(xu_acts), [a.name for a in xu_acts], flush=True)
    print("[previs17] mom_acts", len(mom_acts), [a.name for a in mom_acts], flush=True)
    if len(xu_acts) < 5 or len(mom_acts) < 5:
        raise RuntimeError("动作 clip 数量不符：C06 / C11 都应有 10 个")

    # clip 4 = Sitting_Idle_Loop（两者都是 10-clip 模型，按名称取而非列表下标）
    ACT_XU_SIT = act_by_clip(xu_acts, 4)
    ACT_MOM_SIT = act_by_clip(mom_acts, 4)
    print(f"[previs17] sit clips: xu={ACT_XU_SIT.name} mom={ACT_MOM_SIT.name}", flush=True)
    for a in (ACT_XU_SIT, ACT_MOM_SIT):
        p14.make_loop(a)
    removed = p14.strip_channels([ACT_XU_SIT], MANUAL_BONES_XU)
    removed += p14.strip_channels([ACT_MOM_SIT], MANUAL_BONES_MOM)
    print("[previs17] stripped", len(removed), "channels", flush=True)

    for a in (xu, mom):
        a.rotation_mode = "XYZ"
    xu_ad, mom_ad = xu.animation_data, mom.animation_data

    # 脚高校正必须拿站姿 Idle 测（HANDOFF §5.14）
    ACT_XU_IDLE = act_by_clip(xu_acts, 1)
    ACT_MOM_IDLE = act_by_clip(mom_acts, 1)
    scene = bpy.context.scene
    p14.set_loop(xu_ad, ACT_XU_IDLE, {"key": None}, "idle_probe")
    p14.set_loop(mom_ad, ACT_MOM_IDLE, {"key": None}, "idle_probe")
    scene.frame_set(1)
    bpy.context.view_layer.update()
    xu_dz = -p14.feet_z(xu) + 0.02
    mom_dz = -p14.feet_z(mom) + 0.02
    print(f"[previs17] dz xu={xu_dz:.3f} mom={mom_dz:.3f}", flush=True)

    matte = p14.make_matte("char_matte17", 0.82)
    for o in [o for o in scene.objects if o.type == "MESH"]:
        mnames = [m.name for m in o.data.materials] if o.data.materials else []
        if any(n.startswith("s17_") for n in mnames):
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

    cam_data = bpy.data.cameras.new("previs_cam17")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam17", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    sp, ep = Vector(CAM_START), Vector(CAM_END)
    aim_static = Vector((0.38, 1.42, 1.00))

    st_x, st_m = {"key": None}, {"key": None}
    test_mode = os.environ.get("PREVIS_TEST") == "1"
    if test_mode:
        frames_iter = [1, 30, 48, 70, 96, 110, 124, 140, 156, 168, 182, 192]
    elif os.environ.get("PREVIS_RANGE"):
        a, b = os.environ["PREVIS_RANGE"].split("-")
        frames_iter = range(int(a), int(b) + 1)
    else:
        frames_iter = range(1, N_FRAMES + 1)

    for f in frames_iter:
        t = p14.ease((f - 1) / (N_FRAMES - 1))

        p14.set_loop(xu_ad, ACT_XU_SIT, st_x, "sit")
        p14.set_loop(mom_ad, ACT_MOM_SIT, st_m, "sit")
        xu.location = (*SEAT_XU, xu_dz)
        xu.rotation_euler = (0, 0, YAW_XU)
        mom.location = (*SEAT_MOM, mom_dz)
        mom.rotation_euler = (0, 0, YAW_MOM)
        scene.frame_set(f)

        # ---- 手机收回进度：三态时间轴，驱动妈妈右臂手 K（不再直接插值手机坐标）----
        if f <= 120:
            k_phone = 0.0
        elif f <= 156:
            k_phone = p14.ease((f - 121) / 35)
        else:
            k_phone = 1.0
        # 妈妈点屏幕：两次极轻的颤动（第一遍 f30-40、第二遍 f70-82 点错）
        tap = 0.0
        if 30 <= f <= 40:
            tap = 1.6 * math.sin(math.pi * (f - 30) / 10)
        elif 70 <= f <= 82:
            tap = 2.2 * math.sin(math.pi * (f - 70) / 12)

        # ---- 许宁：头/上身 + 右手 reach ----
        if f <= 48:
            xu_down, xu_lean, xu_turn, reach = 6.0, 5.0, 6.0, 0.0
        elif f <= 96:
            k = p14.ease((f - 49) / 47)
            xu_down, xu_lean, xu_turn, reach = 6.0 + 2.0 * k, 5.0 + 2.0 * k, 6.0, 0.0
        elif f <= 124:
            k = p14.ease((f - 97) / 27)
            xu_down, xu_lean, xu_turn, reach = 8.0, 7.0 + 5.0 * k, 6.0, k
        elif f <= 148:
            xu_down, xu_lean, xu_turn, reach = 8.0, 12.0, 6.0, 1.0
        elif f <= 176:
            k = p14.ease((f - 149) / 27)
            xu_down, xu_lean, xu_turn, reach = 8.0 * (1 - k), 12.0 * (1 - k), 6.0, 1.0 - k
        else:
            xu_down, xu_lean, xu_turn, reach = 0.0, 0.0, 6.0, 0.0
        # 结尾重新开口：极轻的点头
        if 177 <= f <= 192:
            xu_down += 1.8 * math.sin((f - 177) / 6.0)
        head_pose(xu, xu_down, xu_turn, xu_lean)
        xu_right_arm(xu, reach)

        # ---- 妈妈：低头点屏幕 → 缓缓抬头看向女儿；右臂随手机渐收回 ----
        if f <= 96:
            mom_down, mom_lean, mom_turn = 11.0, 5.0, -6.0
        elif f <= 136:
            mom_down, mom_lean, mom_turn = 11.0, 5.0, -6.0
        elif f <= 168:
            k = p14.ease((f - 137) / 31)
            mom_down, mom_lean, mom_turn = 11.0 * (1 - k), 5.0 * (1 - k), -6.0 * (1 - k)
        else:
            mom_down, mom_lean, mom_turn = 0.0, 0.0, 0.0
        head_pose(mom, mom_down, mom_turn, mom_lean)
        mom_right_arm(mom, k_phone)

        # ---- 手机：可见性优先，与妈妈右臂手 K 共用同一条时间轴 ----
        # v2 首版把手机直接挂在 RightHand 骨骼上，结果坐姿 idle 的手在桌沿以下，
        # 手机被桌布完全挡住、整段不可见。白模只需给 H3 运动拓扑：手机保持在
        # 桌面上方可见、随 k_phone 往妈妈身前移，妈妈右臂同步做收回动作，
        # 两者由同一个 k_phone 驱动；H3 会把手与手机贴合（shot16 v03 已验证）。
        phone.location = (
            PHONE_HOME[0] + (PHONE_END[0] - PHONE_HOME[0]) * k_phone,
            PHONE_HOME[1] + (PHONE_END[1] - PHONE_HOME[1]) * k_phone,
            PHONE_HOME[2] + (PHONE_END[2] - PHONE_HOME[2]) * k_phone,
        )
        phone.rotation_euler = (math.radians(-18 + tap), 0, math.radians(8 + 0.4 * tap))
        phone.scale = PHONE_SCALE   # 尺寸恒定，不缩放不消失

        # ---- 相机：缓慢推近 + 轻微手持 ----
        cam.location = sp.lerp(ep, t)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (aim_static - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs17] frame {f}/{N_FRAMES}", flush=True)

    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot17", "title": "我自己来", "source": "剧本六 L285-303 / 方案 §4",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E09 折叠餐桌白天版，两人并坐在桌子靠窗一侧（门由 H3 prompt 补，不进白模）",
            "table": TABLE_CENTER, "seat_xu": SEAT_XU, "seat_mom": SEAT_MOM,
            "camera": [list(CAM_START), list(CAM_END)],
            "props": {"phone_home": PHONE_HOME, "phone_end": PHONE_END,
                      "phone_dims": PHONE_DIMS, "phone_base_scale": PHONE_SCALE,
                      "phone_note": "v2：手机保持桌面上方可见并随 k_phone 渐移；妈妈右臂由同一 k_phone 逐帧手 K 做收回，两者同步（首版直接挂 RightHand 骨骼导致手机被桌布挡住，已弃）"},
            "previs_version": "v2（相机拉近 + 手机跟右手 + 妈妈右臂手 K）",
            "timeline": {
                "f1-48": "教第一遍：手机在妈妈手里，许宁侧身指屏幕，妈妈低头点一下",
                "f49-96": "教第二遍：妈妈第二次仍点错（f70-82 轻颤），许宁前倾加大",
                "f97-136": "许宁的手渐伸向手机想代劳；f121 起妈妈开始把手机往回收",
                "f137-168": "手机收回完成，许宁的手半空停住后渐收回，妈妈抬头看向女儿",
                "f169-192": "许宁收手回正、重新开口，手机稳定在妈妈手里，镜头微推",
            },
            "three_state": {
                "phone": "前态妈妈右臂持机略伸向两人中间 → 过程右臂渐把手机收回身前（f121-156），手机全程贴 RightHand 骨骼 → 后态稳定在妈妈手里；不落桌、不消失、不漂浮",
                "xu_right_hand": "指屏幕 → 渐伸向手机 → 半空停住 → 渐收回体侧",
                "xu_posture": "微前倾 → 前倾加大 → 回正",
                "mom_head": "低头看屏幕 → 缓缓抬起 → 看向女儿",
            },
            "characters": {"xu": "C06 ten-clip / clip 4 = Sitting_Idle_Loop（右臂通道剥出手 K）",
                           "mom": "C11 ten-clip / clip 4 = Sitting_Idle_Loop（横版 T-pose 重建后的模型）"},
            "hard_constraints": "两人脚贴地、椅子桌子与桌上道具不移动、手机不漂浮不瞬移不消失且始终贴在妈妈右手骨骼上、无第三人、段间全 ease 渐变",
            "previs_v1_issues": ["相机过远、两人过小", "手机独立插值导致悬空", "核心动作缺手部运动通道"],
            "previs_v1_archive": "progress/04_白模预演/shot17_测试帧_v1/"
        }
        with open(os.path.join(OUT_DIR, "previs17_report.json"), "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS17_DONE", flush=True)


if __name__ == "__main__":
    main()
