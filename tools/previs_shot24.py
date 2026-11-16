# -*- coding: utf-8 -*-
"""shot24「两碗面」Blender 哑光白模预演（192 帧 / 1280×720 / 24fps）。

概念级交付：只出水彩概念动画的运动参考，不交付 .blend/.obj 真模型源文件。

核心（方案 §3 shot24 / 剧本七 L363-367，P0）：
  * **硬约束：对面椅子全程空**——白模里只有 C07b 一个人体，绝不创建第二个人、人影或替身。
  * 两只面碗是「状态保持型」道具：f001 起就在桌面、全程恒存同位、不被触碰；
    唯一变化是热气从可见连续渐弱到无，且**前置 f001–f048**（§5.21，H3 会压到前 2 秒）。
  * 手机是位移型道具：桌面 → 右手 → 贴耳，f144 起逐帧由右手骨骼世界坐标驱动（零脱节），
    f138–144 ease 过渡，不瞬移、不凭空出现。
  * 午后→傍晚/次日由真实连续光源给出：sun AREA 120→25 且缓移 + 色温转冷、
    fill 40→15、world 0.30→0.14、窗外天光 Emission 0.34→0.08；**禁止几何光斑板**（§3 D5）。
  * 膝前浅桌不落地、不横跨腿前（shot23 v3 教训：落地桌腿=半蹲，桌裙栅栏=笼子）；
    只在桌子两端各放一组细 X 腿作 E09 折叠桌识别。

坐标全部来自 `tmp_qc/shot24_probe_v3.json`（5 个真实 anchor 误差 0.0001–0.0185m）。
两轮判退稿见 `progress/04_白模预演/shot24_探针_v1_布局判退/` 与 `shot24_探针_v2_锚点判退/`。

Run:
  PREVIS_TEST=1 blender.exe --background --python tools/previs_shot24.py   # 15 帧测试帧
  blender.exe --background --python tools/previs_shot24.py                  # 192 帧一次性全渲
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import previs_shot14 as p14  # noqa: E402

OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames24")
PROBE_JSON = os.path.join(ROOT, "tmp_qc", "shot24_probe_v3.json")
REPORT_JSON = os.path.join(OUT_DIR, "previs24_report.json")
MODEL = os.path.join(ROOT, "assets", "models", "C07b", "tex_mesh_animated.glb")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720
CAM_LENS = 35
CAM_START = (0.15, -2.30, 1.55)
CAM_END = (0.12, -2.20, 1.53)
AIM = Vector((0.00, 0.95, 0.82))

XU_LOC = (-0.30, 0.95)
YAW_DEG = 0.0
TABLE_CENTER = (0.00, 0.82, 0.715)
TABLE_DIMS = (1.30, 0.32, 0.04)
TOP_Z = 0.735

BOWL_A = (-0.52, 0.78, 0.775)
BOWL_B = (0.20, 0.80, 0.775)
PHONE_TABLE = (-0.292, 0.844, 0.741)
PHONE_LIFT_MID = (-0.14, 0.995, 0.882)
PHONE_EAR = (-0.161, 1.076, 0.959)
RIGHT_REST = (-0.30, 0.86, 0.74)

EMPTY_CHAIR = (0.62, 1.30)

BONES = ("mixamorig:RightArm", "mixamorig:RightForeArm",
         "mixamorig:LeftArm", "mixamorig:LeftForeArm",
         "mixamorig:Head", "mixamorig:Neck",
         "mixamorig:Spine", "mixamorig:Spine1")
RETREAT_R = (-45.0, -132.1, 0.0, 56.6)
RETREAT_L = (-45.0, 132.1, 0.0, -56.6)

G = {}


def mat(key, shade, emission=None):
    # p14.mat 的 shade 是单值灰度；本脚本按 RGB 写更直观，这里统一取亮度均值
    if isinstance(shade, (tuple, list)):
        shade = sum(shade) / len(shade)
    return p14.mat("s24_" + key, shade, emission)


def emission_mat(name, color, strength):
    m = bpy.data.materials.new("s24_" + name)
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
    if m:
        o.data.materials.append(m)
    return o


def build_room():
    """E09 折叠餐桌房间：后墙 + 左墙 + 北窗纱帘 + 右侧矮柜 + 两把木椅。

    ⚠️ 对面椅子只建椅子几何，**绝不创建第二个人体或人影**（P0 硬约束）。
    """
    floor = mat("floor", (0.62, 0.63, 0.66))
    wall = mat("wall", (0.55, 0.58, 0.64))
    wood = mat("wood", (0.66, 0.52, 0.36))
    dark = mat("darkwood", (0.38, 0.31, 0.26))
    curtain = mat("curtain", (0.90, 0.90, 0.88))

    p14.add_box("floor", (0.0, 0.70, -0.02), (5.2, 5.0, 0.04), floor)
    p14.add_box("wall_back", (0.0, 2.35, 1.25), (5.2, 0.06, 2.50), wall)
    p14.add_box("wall_left", (-2.05, 0.70, 1.25), (0.06, 3.40, 2.50), wall)

    # 北窗（墙上偏左）：发光天光板 + 4 根窗棂 + 2 片白纱帘
    daylight = emission_mat("daylight", (0.82, 0.88, 0.98), 0.34)
    G["daylight_em"] = daylight.node_tree.nodes.get("Emission") or [
        n for n in daylight.node_tree.nodes if n.bl_idname == "ShaderNodeEmission"][0]
    p14.add_box("window_light", (-1.15, 2.31, 1.58), (1.10, 0.02, 1.10), daylight)
    p14.add_box("window_bar_h", (-1.15, 2.28, 1.58), (1.12, 0.035, 0.035), dark)
    p14.add_box("window_bar_v", (-1.15, 2.28, 1.58), (0.035, 0.035, 1.12), dark)
    p14.add_box("curtain_l", (-1.62, 2.26, 1.58), (0.22, 0.02, 1.12), curtain)
    p14.add_box("curtain_r", (-0.68, 2.26, 1.58), (0.22, 0.02, 1.12), curtain)

    # 右侧矮柜 + 锅 + 一叠碗 + 白杯
    p14.add_box("cabinet", (1.12, 1.90, 0.42), (0.78, 0.46, 0.84), wood)
    pot = mat("pot", (0.34, 0.36, 0.40))
    p14.add_cyl("pot_body", (1.02, 1.90, 0.90), 0.13, 0.14, pot)
    p14.add_cyl("pot_lid", (1.02, 1.90, 0.98), 0.135, 0.015, pot)
    p14.add_cyl("bowl_stack", (1.38, 1.90, 0.87), 0.09, 0.05, mat("stack", (0.86, 0.86, 0.84)))
    p14.add_cyl("white_mug", (1.38, 1.62, 0.90), 0.045, 0.10,
                mat("mug", (0.88, 0.89, 0.90)))

    # 主椅（人物坐）：镂空椅背，避免整块实心板挡人
    p14.add_box("chair_seat", (XU_LOC[0], 1.08, 0.44), (0.44, 0.42, 0.045), wood)
    p14.add_box("chair_back_top", (XU_LOC[0], 1.29, 0.92), (0.44, 0.045, 0.10), wood)
    for dx in (-0.19, 0.19):
        p14.add_box(f"chair_post_{dx}", (XU_LOC[0] + dx, 1.29, 0.70),
                    (0.035, 0.045, 0.48), wood)
    for dx in (-0.18, 0.18):
        for dy in (0.92, 1.24):
            p14.add_box(f"chair_leg_{dx}_{dy}", (XU_LOC[0] + dx, dy, 0.22),
                        (0.035, 0.035, 0.44), dark)

    # **对面空椅**（同款、全片无人）：位置更靠右后，避免与人物重叠
    ex, ey = EMPTY_CHAIR
    p14.add_box("empty_chair_seat", (ex, ey, 0.44), (0.44, 0.42, 0.045), wood)
    p14.add_box("empty_chair_back_top", (ex, ey + 0.21, 0.92), (0.44, 0.045, 0.10), wood)
    for dx in (-0.19, 0.19):
        p14.add_box(f"empty_chair_post_{dx}", (ex + dx, ey + 0.21, 0.70),
                    (0.035, 0.045, 0.48), wood)
    for dx in (-0.18, 0.18):
        for dy in (ey - 0.16, ey + 0.16):
            p14.add_box(f"empty_chair_leg_{dx}_{dy}", (ex + dx, dy, 0.22),
                        (0.035, 0.035, 0.44), dark)
    # 空椅标识：椅面上的浅色坐垫（恒存），便于 H3 读出「这把椅子空着」
    p14.add_box("empty_chair_cushion", (ex, ey, 0.468), (0.36, 0.34, 0.012),
                mat("cushion", (0.45, 0.36, 0.26)))

    # 折叠桌：不落地浅托盘 + 两端细 X 腿（不做桌裙栅栏）
    p14.add_box("table_top", TABLE_CENTER, TABLE_DIMS,
                mat("tabletop", (0.68, 0.66, 0.60)))
    for side, sx in (("l", -0.46), ("r", 0.46)):
        for sgn in (-1, 1):
            leg = p14.add_box(f"table_leg_{side}_{sgn}",
                              (sx, 0.82 + 0.06 * sgn, 0.36),
                              (0.022, 0.022, 0.70), dark)
            leg.rotation_euler.x = math.radians(10 * sgn)

    # 桌上恒存小物：保温杯
    p14.add_cyl("thermos", (0.44, 0.82, 0.85), 0.035, 0.22,
                mat("thermos", (0.62, 0.50, 0.66)))
    p14.add_cyl("thermos_cap", (0.44, 0.82, 0.965), 0.037, 0.02,
                mat("thermos_cap", (0.30, 0.30, 0.34)))
    bpy.context.view_layer.update()   # §5.16：最后一个 add_box 的 dimensions 需依赖图评估


def build_props():
    """两碗面（恒存）+ 筷子 + 热气细线 + 手机（位移型）。"""
    bowl_mat = mat("bowl", (0.32, 0.36, 0.42))
    noodle = emission_mat("noodle", (0.98, 0.58, 0.16), 1.10)
    chop = mat("chopsticks", (0.25, 0.18, 0.10))
    steam = emission_mat("steam", (1.00, 0.96, 0.86), 1.30)
    G["steam_em"] = steam.node_tree.nodes.get("Emission") or [
        n for n in steam.node_tree.nodes if n.bl_idname == "ShaderNodeEmission"][0]
    phone = emission_mat("phone", (0.16, 0.30, 0.62), 1.30)
    screen = emission_mat("phone_screen", (0.95, 0.98, 1.00), 1.20)

    G["bowls"] = []
    G["steam_parts"] = []
    for tag, (bx, by, bz) in (("a", BOWL_A), ("b", BOWL_B)):
        body = p14.add_cyl(f"bowl_{tag}_body", (bx, by, bz - 0.010), 0.105, 0.065, bowl_mat)
        rim = add_torus(f"bowl_{tag}_rim", (bx, by, bz + 0.018), 0.105, 0.007, bowl_mat)
        nd = p14.add_cyl(f"bowl_{tag}_noodles", (bx, by, bz + 0.016), 0.090, 0.010, noodle)
        G["bowls"].extend([body, rim, nd])
        for i in range(2):
            c = p14.add_cyl(f"chop_{tag}_{i}",
                            (bx + 0.055 + 0.012 * i, by - 0.10, bz + 0.030),
                            0.004, 0.24, chop, rot=(0, math.radians(78), math.radians(8 * i)))
            G["bowls"].append(c)
        # 热气：每碗 3 段细线，方向分散、z 分三层（避免糊成一片或读成道具）
        for i in range(4):
            s = p14.add_cyl(f"steam_{tag}_{i}",
                            (bx + (i - 1.5) * 0.026, by, bz + 0.085 + 0.070 * i),
                            0.007, 0.075, steam,
                            rot=(math.radians(9 * (i - 1.5)), math.radians(14 * (i - 1.5)), 0))
            G["steam_parts"].append(s)

    ph = p14.add_box("phone_root", PHONE_TABLE, (0.145, 0.078, 0.016), phone)
    sc = p14.add_box("phone_screen", (PHONE_TABLE[0], PHONE_TABLE[1], PHONE_TABLE[2] + 0.011),
                     (0.118, 0.058, 0.003), screen)
    G["phone_root"] = ph
    G["phone_screen"] = sc
    bpy.context.view_layer.update()


def add_lighting():
    """午后→傍晚连续渐变，全部真实光源，不做几何光斑板（§3 D5）。"""
    world = bpy.data.worlds.new("previz_world24")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.22, 0.25, 0.31, 1.0)
            n.inputs[1].default_value = 0.30
    bpy.context.scene.world = world
    G["world_bg"] = [n for n in world.node_tree.nodes
                     if n.bl_idname == "ShaderNodeBackground"][0]

    bpy.ops.object.light_add(type="AREA", location=(-1.30, 0.60, 2.30))
    sun = bpy.context.active_object
    sun.name = "afternoon_key"
    sun.data.energy = 120
    sun.data.size = 1.55
    sun.data.color = (1.00, 0.90, 0.76)
    sun.rotation_euler = (math.radians(52), math.radians(-18), 0)
    G["sun"] = sun

    bpy.ops.object.light_add(type="AREA", location=(0.95, -1.20, 2.30))
    fill = bpy.context.active_object
    fill.name = "cool_fill"
    fill.data.energy = 40
    fill.data.size = 2.60
    fill.data.color = (0.74, 0.82, 1.00)
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
        ((0, 1, 0), ay), ((1, 0, 0), ax), ((0, 0, 1), az)])
    p14.rotate_ops(arm, f"mixamorig:{side}ForeArm", [((0, 1, 0), fb)])


def hand_world(arm, side):
    bpy.context.view_layer.update()
    w = arm.matrix_world @ arm.pose.bones[f"mixamorig:{side}Hand"].matrix.translation
    return (round(w.x, 4), round(w.y, 4), round(w.z, 4))


def head_pose(arm, down, turn):
    p14.rotate_ops(arm, "mixamorig:Head", [
        ((1, 0, 0), down), ((0, 0, 1), turn)])
    p14.rotate_ops(arm, "mixamorig:Neck", [((1, 0, 0), down * 0.35)])


def lerp3(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def solve_arm(arm, side, target, seeds, iters=6, step=20.0):
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
    solved, err = solve_arm(arm, side, target, seeds, iters=6, step=20.0)
    if err > 0.045:
        solved, err = solve_arm(arm, side, target, [solved] + seeds[:2],
                                iters=12, step=30.0)
    if err > 0.06:
        solved, err = solve_arm(arm, side, target, [solved] + seeds[:2],
                                iters=12, step=12.0)
    return solved, err


def right_target(f):
    """右手：静放桌沿 → 桌面手机 → 抬起 → 贴耳（末段，剧本「第二天打电话」）。"""
    if f <= 120:
        return RIGHT_REST
    if f <= 144:
        return lerp3(RIGHT_REST, PHONE_TABLE, p14.ease((f - 120) / 24.0))
    if f <= 160:
        return lerp3(PHONE_TABLE, PHONE_LIFT_MID, p14.ease((f - 144) / 16.0))
    if f <= 176:
        return lerp3(PHONE_LIFT_MID, PHONE_EAR, p14.ease((f - 160) / 16.0))
    return PHONE_EAR


def xu_head(f):
    """低头看面 → 静坐侧看空椅 → 打电话时微微低头。"""
    if f <= 24:
        return 8.0 + 4.0 * p14.ease(f / 24.0), 0.0
    if f <= 120:
        return 12.0, 3.0 * p14.ease((f - 24) / 96.0)
    return 6.0 + 4.0 * p14.ease((f - 120) / 72.0), -2.0


def steam_strength(f):
    """关键变化前置：热气 f001 可见 → f048 完全凉透（§5.21）。"""
    return max(0.0, 1.0 - p14.ease(min(1.0, (f - 1) / 47.0)))


def main():
    with open(PROBE_JSON, encoding="utf-8") as fh:
        probe = json.load(fh)
    assert probe.get("all_reachable") and probe.get("probe_version") == "v3_final", \
        "定稿探针未全绿，先修布局再跑预演"
    ANG = {k: tuple(v["angles"]) for k, v in probe["solutions"].items()}
    print("[previs24] anchors", {k: [round(v, 1) for v in a] for k, a in ANG.items()},
          flush=True)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    build_room()
    build_props()
    add_lighting()

    xu, acts, _ = p14.import_glb(MODEL)
    assert xu is not None and len(acts) >= 5, "C07b 应有 10 clips"
    idle = act_by_clip(acts, 1)
    sit = act_by_clip(acts, 4)
    for a in (idle, sit):
        p14.make_loop(a)
    removed = p14.strip_channels([idle, sit], BONES)
    print("[previs24] sit clip", sit.name, "| stripped", len(removed), flush=True)

    scene = bpy.context.scene
    p14.set_loop(xu.animation_data, idle, {"key": None}, "idle_probe")
    xu.rotation_mode = "XYZ"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    dz = -p14.feet_z(xu) + 0.02
    assert abs(dz - probe["dz_stance_idle"]) < 0.01, "脚高与探针不一致"
    print(f"[previs24] feet dz = {dz:.4f}（站姿 Idle 实测）", flush=True)
    p14.set_loop(xu.animation_data, sit, {"key": None}, "sit")

    char_matte = p14.make_matte("char_matte24", 0.34)
    for o in [o for o in scene.objects if o.type == "MESH"]:
        names = [m.name for m in o.data.materials] if o.data.materials else []
        if any(n.startswith("s24_") for n in names):
            continue
        o.data.materials.clear()
        o.data.materials.append(char_matte)

    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = RES_X, RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, N_FRAMES
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    cam_data = bpy.data.cameras.new("previs_cam24")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam24", cam_data)
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

    seed_r = ANG["right_rest"]
    max_err, max_err_f = 0.0, 0
    phone_samples, steam_samples, light_samples = [], [], []

    for f in frames_iter:
        t = (f - 1) / (N_FRAMES - 1)
        tc = p14.ease(t)
        xu.location = (*XU_LOC, dz)
        xu.rotation_euler = (0, 0, math.radians(YAW_DEG))
        scene.frame_set(f)
        bpy.context.view_layer.update()

        xd, xt = xu_head(f)
        head_pose(xu, xd, xt)

        # 非工作手：每帧 apply RETREAT 后实测 rest_pt（§5.20），不硬写绝对体侧点
        apply_arm(xu, "Left", *RETREAT_L)
        apply_arm(xu, "Right", *RETREAT_R)
        rest_r = hand_world(xu, "Right")

        tgt_r = right_target(f)
        sr, er = solve_with_fallback(
            xu, "Right", tgt_r,
            [seed_r, ANG["right_rest"], ANG["phone_table"],
             ANG["phone_lift_mid"], ANG["phone_ear"], RETREAT_R])
        seed_r = sr
        max_err, max_err_f = (er, f) if er > max_err else (max_err, max_err_f)

        # ---------- 手机：f001–138 恒在桌面（前态）→ f138–144 ease 贴手 → 逐帧挂右手骨骼 ----------
        hr = hand_world(xu, "Right")
        hand_pt = (hr[0], hr[1] - 0.008, hr[2] + 0.012)
        if f <= 138:
            pp = PHONE_TABLE
        elif f <= 144:
            pp = lerp3(PHONE_TABLE, hand_pt, p14.ease((f - 138) / 6.0))
        else:
            pp = hand_pt
        G["phone_root"].location = pp
        G["phone_screen"].location = (pp[0], pp[1], pp[2] + 0.011)
        phone_samples.append((f, [round(v, 3) for v in pp]))

        # ---------- 两碗恒存；唯一变化是热气连续渐弱（前置 f001–048） ----------
        s = steam_strength(f)
        G["steam_em"].inputs["Strength"].default_value = 1.30 * s
        for o in G["steam_parts"]:
            o.hide_render = s < 0.015
        for o in G["bowls"]:
            o.hide_render = False
        steam_samples.append((f, round(s, 3)))

        # ---------- 午后→傍晚：真实连续光源 ----------
        G["sun"].data.energy = 120.0 - 95.0 * t
        G["sun"].location.x = -1.30 + 1.55 * t
        G["sun"].data.color = (1.00 - 0.40 * t, 0.90 - 0.20 * t, 0.76 + 0.14 * t)
        G["fill"].data.energy = 40.0 - 25.0 * t
        G["world_bg"].inputs[1].default_value = 0.30 - 0.16 * t
        G["daylight_em"].inputs["Strength"].default_value = 0.34 - 0.26 * t
        light_samples.append((f, round(G["sun"].data.energy, 1),
                              round(G["fill"].data.energy, 1)))

        # ---------- 相机慢推 + 极轻手持微晃 ----------
        cam.location = sp.lerp(ep, tc)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (AIM - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        if test_mode:
            print(f"[previs24] f{f:03d} R=({hr[0]:.3f},{hr[1]:.3f},{hr[2]:.3f}) "
                  f"err={er:.4f} phone={phone_samples[-1][1]} steam={s:.2f} "
                  f"sun={G['sun'].data.energy:.0f}", flush=True)

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs24] frame {f}/{N_FRAMES}", flush=True)

    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot24", "title": "两碗面", "priority": "P0",
            "source": "剧本七 L363-367 / 方案 §3 §4 / E09_v01.png（目检：水彩折叠餐桌、两只面碗、两把椅子都空、全图无人）",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E09 折叠餐桌房间：北窗带白纱帘、右侧矮柜（锅/碗叠/白杯）、两把木椅（一把有人、一把全程空）、"
                     "不落地膝前浅桌 + 两端细 X 腿；两碗面与筷子、保温杯、手机恒存",
            "camera": [list(CAM_START), list(CAM_END), list(AIM)],
            "hard_constraint": {
                "opposite_chair_empty_whole_shot": True,
                "implementation": "只导入 C07b 一个 GLB；空椅仅建椅子几何 + 浅色坐垫，绝不创建第二个人体/人影/替身",
                "second_person_count": 0,
            },
            "characters": {
                "xu": "C07b 许宁·老年居家 ten-clip / clip 4 Sitting_Idle_Loop",
                "feet_dz": round(dz, 4),
                "feet_note": "脚高用站姿 clip 1 Idle 实测（§5.14）；坐姿 Hips 位移探针实测 0",
            },
            "probe": {
                "file": "tmp_qc/shot24_probe_v3.json", "version": "v3_final",
                "all_reachable": True,
                "errors_m": {k: v["error_m"] for k, v in probe["solutions"].items()},
                "rejected_layouts": [
                    "tmp_qc/shot24_probe.json（按 E09 参考图把手机放桌面右侧 x=+0.16，超出 C07b 右手包络 0.3615m）"
                    "→ progress/04_白模预演/shot24_探针_v1_布局判退/",
                    "tmp_qc/shot24_probe_v2.json（phone_table 0.0796m / left_bowl_edge 0.0922m 超阈）"
                    "→ progress/04_白模预演/shot24_探针_v2_锚点判退/",
                ],
            },
            "bowls": {
                "type": "状态保持型核心道具",
                "centers": [list(BOWL_A), list(BOWL_B)],
                "driver": "全程固定在桌面、手不碰碗、不被移动/吃掉/加盖/消失",
                "only_change": "热气 f001 可见 → f048 完全凉透，连续 ease 渐弱，Emission 1.30→0（关键变化前置 §5.21）",
                "first_frame_visible_and_large": True,
                "steam_samples": steam_samples[::16],
            },
            "phone": {
                "type": "位移型核心道具",
                "driver": "f001–138 恒在桌面 (-0.292,0.844,0.741) 作前态；f138–144 ease 贴手；"
                          "f144 起逐帧由右手 hand_world 驱动（手与手机零脱节，§1.2）",
                "chain": "桌面 → 右手 → 抬起弧线中点 (-0.14,0.995,0.882) → 贴耳 (-0.161,1.076,0.959)",
                "never_teleports": True,
                "samples": phone_samples[::16],
            },
            "empty_chair": "位置 (0.62,1.30)，全程恒在同位、恒空；浅色坐垫便于 H3 读出空椅",
            "lighting": {
                "method": "afternoon_key AREA 120→25 且 x -1.30→+0.25、色温暖白→冷蓝；cool_fill 40→15；"
                          "world 0.30→0.14；窗外天光 Emission 0.34→0.08。全部线性连续，无阶跃、无几何光斑板",
                "continuous": True, "samples": light_samples[::24],
            },
            "arm_solver": {
                "method": "右手每帧先摆回体侧角实测 rest_pt，再在当前帧骨骼状态下做多起点坐标下降；"
                          "起点=上一帧解 + 五段探针 anchor + 体侧角；6 轮 / 20° / 每轮 ×0.6；"
                          "误差 >0.045m 换 12 轮 30° 大步长，>0.06m 再换 12 轮 12° 细修（§5.22）",
                "left_hand": "每帧 apply RETREAT_L 后实测 rest_pt，不设绝对体侧目标（§5.20）",
                "retreat": {"right": list(RETREAT_R), "left": list(RETREAT_L)},
                "max_error_m": round(max_err, 4), "max_error_frame": max_err_f,
            },
            "timeline": {
                "f001": "前态：两碗面在桌面大而清晰、热气明显，对面椅子空，手机在桌面可见",
                "f001-048": "热气连续渐弱到完全凉透（唯一关键变化，前置）",
                "f049-120": "她静坐、说完一句话停下等那声「嗯」，午后光连续转晚",
                "f120-144": "右手从桌沿移到桌面手机",
                "f144-160": "手机随手连续抬离桌面到弧线中点",
                "f160-176": "手机贴耳",
                "f176-192": "保持贴耳安静打电话，两碗与空椅恒在",
            },
            "three_state": {
                "noodles": "热（f001 有热气）→ 连续渐弱 → 凉透（f048 起无热气）→ 恒存到 f192",
                "phone": "桌面（f001）→ 右手 → 贴耳（f192）",
                "light": "明亮午后窗光 → 连续渐弱渐冷 → 安静蓝灰傍晚",
            },
            "hard_constraints": "对面椅子全程空、全片仅 1 人；两碗面恒存同位且不被触碰；手机必须完整连续位移且不得凭空出现；"
                                "无硬切/回忆/跨空间；段间全 ease；192 帧一次性全渲保证逐帧求解器 seed 连续",
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
        print("[previs24] max_error", round(max_err, 4), "@ f", max_err_f, flush=True)
        print("[previs24] WROTE", REPORT_JSON, flush=True)
    print("PREVIS24_DONE", flush=True)


if __name__ == "__main__":
    main()
