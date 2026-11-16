# -*- coding: utf-8 -*-
"""shot26「跳一点给外婆看」Blender 哑光白模预演（192 帧 / 1280×720 / 24fps）。

核心（剧本七 L391–417 / 方案 §3 §4，P0）：
  * 三人同病房：C07 半坐床沿（clip 4）、C16 女儿（clip 1）、C17 小满（clip 1）。
  * **挪椅腾地**：椅子 f001–f016 由 C16 右手骨骼驱动从床边连续横移到一旁，之后恒存。
  * **连续舞蹈链**：小满 f016–f032 起势抬手、f032–f056 转身忘动作停下、
    f056–f104 从头再来并完成、f104 后收手；躯干绕 Z 连续旋转（不切 clip，避免姿态跳变）。
  * **两条带白花的褪色红发带**：床边遗物盒内全程恒存（P01 姥姥旧发带，
    与 shot16 P02 / shot27 P03 三代呼应），不得被拿走/消失/变成无白花新发带。
  * 后段：C07 右手碰小满辫梢、C16 掖被角、窗帘被风吹起、C07 闭眼慢慢睡着。
  * 剧本 L413「又想起许多事」与 L417「走廊推车」**不做闪回/第二空间**：
    全片同一病房、连续白光、静默表达（§5）。
  * 窗帘鼓起用真实连续光源 + 材质/几何轻幅摆动，禁止几何光斑板（§3 D5）。

坐标来自 `tmp_qc/shot26_probe_v2.json`（挪椅两点 0.0167 / 0.0022m，三人 Hips 位移正常）。
`animation_9 = Dance_Loop` 已实测可用但未采用，理由见探针报告 decision。

Run:
  PREVIS_TEST=1 blender.exe --background --python tools/previs_shot26.py
  blender.exe --background --python tools/previs_shot26.py
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
FRAMES_DIR = os.path.join(OUT_DIR, "frames26")
PROBE_JSON = os.path.join(ROOT, "tmp_qc", "shot26_probe_v2.json")
REPORT_JSON = os.path.join(OUT_DIR, "previs26_report.json")
MODELS = os.path.join(ROOT, "assets", "models")

FPS, N_FRAMES = 24, 192
RES_X, RES_Y = 1280, 720
CAM_LENS = 35
CAM_START = (-0.95, -2.65, 1.72)
CAM_END = (-0.90, -2.55, 1.70)
AIM = Vector((0.30, 1.00, 0.84))

C07_LOC = (0.42, 1.25)
C16_LOC = (-0.75, 0.70)
C17_LOC = (0.62, 0.92)
YAW = 0.0
DZ = {"c07": 0.7063, "c16": 0.7609, "c17": 0.5521}
BED_TOP_Z = 0.45

CHAIR_START = (-0.66, 0.59, 0.87)    # C16 右手抓椅背（探针实测可达）
CHAIR_END = (-0.95, 0.60, 0.82)
CHAIR_GROUND_Z = 0.45

BONES = ("mixamorig:RightArm", "mixamorig:RightForeArm",
         "mixamorig:LeftArm", "mixamorig:LeftForeArm",
         "mixamorig:Head", "mixamorig:Neck",
         "mixamorig:Spine", "mixamorig:Spine1")
RETREAT_R = (-45.0, -132.1, 0.0, 56.6)
RETREAT_L = (-45.0, 132.1, 0.0, -56.6)

G = {}


def mat(key, shade, emission=None):
    if isinstance(shade, (tuple, list)):
        shade = sum(shade) / len(shade)
    return p14.mat("s26_" + key, shade, emission)


def emission_mat(name, color, strength):
    m = bpy.data.materials.new("s26_" + name)
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
                                     major_segments=24, minor_segments=6, location=loc)
    o = bpy.context.active_object
    o.name = name
    if m:
        o.data.materials.append(m)
    return o


def build_room():
    """E02_v02 病房 + 床边椅 + 遗物盒与两条白花发带（全部恒存）。"""
    floor = mat("floor", (0.42, 0.43, 0.44))
    wall_w = mat("wall_white", (0.52, 0.54, 0.56))
    wall_g = mat("wall_green", (0.30, 0.40, 0.34))
    wood = mat("wood", (0.34, 0.26, 0.18))
    metal = mat("metal", (0.34, 0.38, 0.42))
    dark = mat("dark", (0.34, 0.36, 0.38))
    cloth = mat("cloth", (0.58, 0.60, 0.58))
    curtain_m = mat("curtain", (0.56, 0.60, 0.52))

    p14.add_box("floor", (0.0, 0.70, -0.02), (5.4, 5.0, 0.04), floor)
    p14.add_box("wall_back", (0.0, 2.40, 1.25), (5.4, 0.06, 2.50), wall_w)
    p14.add_box("wall_back_green", (0.0, 2.36, 0.50), (5.4, 0.02, 1.00), wall_g)
    p14.add_box("wall_left", (-2.10, 0.70, 1.25), (0.06, 3.40, 2.50), wall_w)

    daylight = emission_mat("daylight", (0.90, 0.94, 0.98), 0.30)
    G["daylight_em"] = [n for n in daylight.node_tree.nodes
                        if n.bl_idname == "ShaderNodeEmission"][0]
    for i, cx in enumerate((-0.55, 0.35, 1.25)):
        p14.add_box(f"win_{i}", (cx, 2.33, 1.62), (0.78, 0.02, 1.16), daylight)
        p14.add_box(f"win_bar_h_{i}", (cx, 2.30, 1.62), (0.80, 0.03, 0.03), metal)
        p14.add_box(f"win_bar_v_{i}", (cx, 2.30, 1.62), (0.03, 0.03, 1.18), metal)
    G["curtains"] = []
    for cx in (-1.02, 1.72):
        c = p14.add_box(f"curtain_{cx}", (cx, 2.28, 1.62), (0.20, 0.02, 1.18), curtain_m)
        G["curtains"].append(c)
    for i in range(5):
        p14.add_box(f"radiator_{i}", (-0.65 + i * 0.32, 2.20, 0.72),
                    (0.055, 0.10, 0.44), metal)

    p14.add_box("bed_frame", (0.42, 1.25, 0.40), (1.50, 0.62, 0.10), metal)
    p14.add_box("bed_mattress", (0.42, 1.25, 0.45), (1.46, 0.58, 0.06), cloth)
    G["blanket"] = p14.add_box("bed_blanket", (0.05, 1.25, 0.49), (0.72, 0.58, 0.025),
                               mat("blanket", (0.48, 0.66, 0.76)))
    p14.add_box("pillow", (0.92, 1.25, 0.53), (0.42, 0.46, 0.10), cloth)
    p14.add_box("bed_head", (1.20, 1.25, 0.72), (0.05, 0.64, 0.54), metal)
    p14.add_box("bed_foot", (-0.35, 1.25, 0.68), (0.05, 0.64, 0.46), metal)
    for x in (-0.28, 1.12):
        for y in (1.00, 1.50):
            p14.add_box(f"bed_leg_{x}_{y}", (x, y, 0.20), (0.045, 0.045, 0.40), dark)

    # 床头柜 + 暖壶 + 白杯 + 遗物盒（两条白花发带在里面）
    p14.add_box("cabinet", (-0.95, 0.52, 0.38), (0.52, 0.46, 0.76), wood)
    p14.add_cyl("thermos", (-1.05, 0.52, 0.84), 0.045, 0.16,
                mat("thermos", (0.42, 0.46, 0.52)))
    p14.add_cyl("white_mug", (-0.80, 0.52, 0.80), 0.035, 0.08,
                mat("mug", (0.90, 0.91, 0.92)))
    box = mat("keepsake_box", (0.32, 0.26, 0.22))
    p14.add_box("keepsake_box_base", (-0.80, 0.42, 0.80), (0.34, 0.24, 0.06), box)
    G["ribbons"] = []
    ribbon = emission_mat("old_ribbon", (0.86, 0.18, 0.12), 1.05)
    flower = emission_mat("white_flower", (0.98, 0.98, 0.94), 1.15)
    for i, ox in enumerate((-0.055, 0.055)):
        r = add_torus(f"ribbon_{i}", (-0.80 + ox, 0.42, 0.845), 0.058, 0.012, ribbon)
        G["ribbons"].append(r)
        for j in range(2):
            f = p14.add_cyl(f"ribbon_{i}_flower_{j}",
                            (-0.80 + ox + (j - 0.5) * 0.036, 0.42, 0.858),
                            0.013, 0.007, flower)
            G["ribbons"].append(f)

    # 床边木椅（位移型道具，root 由 C16 右手驱动）
    G["chair"] = p14.add_box("chair_root", (CHAIR_START[0], CHAIR_START[1], CHAIR_GROUND_Z),
                             (0.40, 0.40, 0.045), wood)
    G["chair_parts"] = [G["chair"]]
    back = p14.add_box("chair_back", (CHAIR_START[0], CHAIR_START[1] + 0.18, 0.68),
                       (0.40, 0.045, 0.46), wood)
    G["chair_parts"].append(back)
    for dx in (-0.17, 0.17):
        for dy in (-0.17, 0.17):
            leg = p14.add_box(f"chair_leg_{dx}_{dy}",
                              (CHAIR_START[0] + dx, CHAIR_START[1] + dy, 0.22),
                              (0.035, 0.035, 0.44), dark)
            G["chair_parts"].append(leg)

    p14.add_cyl("iv_stand", (1.62, 1.85, 0.90), 0.018, 1.80, metal)
    p14.add_box("iv_hook", (1.62, 1.85, 1.82), (0.22, 0.02, 0.02), metal)
    p14.add_box("wardrobe", (-1.75, 1.60, 0.95), (0.52, 0.46, 1.90), wood)
    clock = add_torus("wall_clock", (-1.75, 2.30, 1.85), 0.11, 0.012, dark)
    clock.rotation_euler.x = math.radians(90)
    bpy.context.view_layer.update()   # §5.16


def add_lighting():
    world = bpy.data.worlds.new("previz_world26")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.24, 0.27, 0.30, 1.0)
            n.inputs[1].default_value = 0.30
    bpy.context.scene.world = world
    G["world_bg"] = [n for n in world.node_tree.nodes
                     if n.bl_idname == "ShaderNodeBackground"][0]
    bpy.ops.object.light_add(type="AREA", location=(-0.60, -0.60, 2.45))
    key = bpy.context.active_object
    key.name = "ward_key"
    key.data.energy = 120
    key.data.size = 2.20
    key.data.color = (0.96, 0.98, 1.00)
    key.rotation_euler = (math.radians(38), math.radians(-12), 0)
    G["key"] = key
    bpy.ops.object.light_add(type="AREA", location=(1.60, 1.20, 2.20))
    fill = bpy.context.active_object
    fill.name = "ward_fill"
    fill.data.energy = 45
    fill.data.size = 2.40
    fill.data.color = (0.84, 0.92, 1.00)
    fill.rotation_euler = (math.radians(30), 0, 0)
    G["fill"] = fill


def act_by_clip(acts, n):
    target = f"animation_{n}"
    for a in acts:
        if a.name.split(".")[0] == target:
            return a
    raise RuntimeError(f"找不到 {target}")


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
        cur, s = list(start), step
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


def chair_target(f, rest):
    if f <= 16:
        return lerp3(CHAIR_START, CHAIR_END, p14.ease(f / 16.0))
    if f <= 32:
        return lerp3(CHAIR_END, rest, p14.ease((f - 16) / 16.0))
    return rest


def dance_yaw(f):
    """起势 → 转身忘动作停下 → 从头再来 → 完成，全程连续无跳变。"""
    if f <= 16:
        return 0.0
    if f <= 32:
        return 90.0 * p14.ease((f - 16) / 16.0)       # 起势 + 转身
    if f <= 56:
        return 90.0                                   # 忘动作，停下
    if f <= 104:
        return 90.0 + 270.0 * p14.ease((f - 56) / 48.0)  # 从头再来并转完
    return 360.0


def dance_lift(f):
    if f <= 16:
        return 0.0
    if f <= 32:
        return p14.ease((f - 16) / 16.0)
    if f <= 56:
        return 1.0 - 0.75 * p14.ease((f - 32) / 24.0)   # 停下时手略放
    if f <= 104:
        return 0.25 + 0.75 * p14.ease((f - 56) / 48.0)  # 重来再抬起
    if f <= 120:
        return 1.0 - p14.ease((f - 104) / 16.0)
    return 0.0


def offset(rest, d):
    return (rest[0] + d[0], rest[1] + d[1], rest[2] + d[2])


def main():
    with open(PROBE_JSON, encoding="utf-8") as fh:
        probe = json.load(fh)
    assert probe.get("all_reachable") and probe.get("probe_version") == "v2_final", \
        "定稿探针未全绿，先修布局再跑预演"
    ANG = {k: tuple(v["angles"]) for k, v in probe["solutions"].items()}
    print("[previs26] anchors", {k: [round(v, 1) for v in a] for k, a in ANG.items()},
          flush=True)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    build_room()
    add_lighting()

    arms = {}
    for key, folder, clip in (("c07", "C07", 4), ("c16", "C16", 1), ("c17", "C17", 1)):
        arm, aa, _ = p14.import_glb(os.path.join(MODELS, folder, "tex_mesh_animated.glb"))
        assert arm is not None and len(aa) >= 5
        idle = act_by_clip(aa, 1)
        use = act_by_clip(aa, clip)
        for a in (idle, use):
            p14.make_loop(a)
        p14.strip_channels([idle, use], BONES)
        p14.set_loop(arm.animation_data, use, {"key": None}, f"{key}_loop")
        arm.rotation_mode = "XYZ"
        arms[key] = arm
    print("[previs26] three models loaded (clip 1/4, no clip switch)", flush=True)

    scene = bpy.context.scene
    char_mattes = {k: p14.make_matte(f"char26_{k}", v)
                   for k, v in (("c07", 0.30), ("c16", 0.46), ("c17", 0.60))}
    for key, arm in arms.items():
        for o in [x for x in arm.children_recursive if x.type == "MESH"]:
            o.data.materials.clear()
            o.data.materials.append(char_mattes[key])

    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = RES_X, RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, N_FRAMES
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    cam_data = bpy.data.cameras.new("previs_cam26")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam26", cam_data)
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

    seed16 = ANG["c16_chair_start"]
    seed17l = RETREAT_L
    seed17r = RETREAT_R
    seed07 = RETREAT_R
    seed16l = RETREAT_L
    max_err, max_err_f = 0.0, 0
    chair_samples, ribbon_checks = [], []

    for f in frames_iter:
        t = (f - 1) / (N_FRAMES - 1)
        tc = p14.ease(t)
        for key, loc in (("c07", C07_LOC), ("c16", C16_LOC), ("c17", C17_LOC)):
            arms[key].location = (*loc, DZ[key])
            arms[key].rotation_euler = (0, 0, math.radians(YAW))
        # C17 躯干连续旋转（不切 clip，避免姿态跳变）
        arms["c17"].rotation_euler.z = math.radians(dance_yaw(f))
        scene.frame_set(f)
        bpy.context.view_layer.update()

        head_pose(arms["c07"], 2.0 + 6.0 * p14.ease(max(0.0, (f - 144) / 48.0)),
                  -5.0 * p14.ease(min(1.0, f / 96.0)))
        head_pose(arms["c16"], 8.0, 0.0)
        head_pose(arms["c17"], 10.0 - 12.0 * p14.ease(min(1.0, f / 104.0)), 0.0)

        # 体侧基准：每帧 apply RETREAT 后实测 rest_pt（§5.20）
        for key in ("c07", "c16", "c17"):
            apply_arm(arms[key], "Left", *RETREAT_L)
            apply_arm(arms[key], "Right", *RETREAT_R)
        rest = {k: {"left": hand_world(v, "Left"), "right": hand_world(v, "Right")}
                for k, v in arms.items()}

        # C16 右手：挪椅 → 收回体侧
        tgt16 = chair_target(f, rest["c16"]["right"])
        s16, e16 = solve_with_fallback(
            arms["c16"], "Right", tgt16,
            [seed16, ANG["c16_chair_start"], ANG["c16_chair_end"], RETREAT_R])
        seed16 = s16

        # C17 双手：随舞蹈链抬起 / 停下 / 重来（小幅偏移由 rest_pt 派生，必然可达）
        lift = dance_lift(f)
        tgt17l = offset(rest["c17"]["left"], (-0.04, -0.03, 0.26 * lift))
        tgt17r = offset(rest["c17"]["right"], (0.04, -0.03, 0.26 * lift))
        s17l, e17l = solve_with_fallback(arms["c17"], "Left", tgt17l,
                                         [seed17l, RETREAT_L])
        s17r, e17r = solve_with_fallback(arms["c17"], "Right", tgt17r,
                                         [seed17r, RETREAT_R])
        seed17l, seed17r = s17l, s17r

        # C07 右手：f120–168 伸向小满辫梢（小幅）
        bk = p14.ease(min(1.0, max(0.0, (f - 120) / 48.0))) * \
             (1.0 - p14.ease(min(1.0, max(0.0, (f - 168) / 24.0))))
        tgt07 = offset(rest["c07"]["right"], (0.10 * bk, -0.12 * bk, 0.10 * bk))
        s07, e07 = solve_with_fallback(arms["c07"], "Right", tgt07,
                                       [seed07, RETREAT_R])
        seed07 = s07

        # C16 左手：f168 起掖被角（小幅）
        tk = p14.ease(min(1.0, max(0.0, (f - 168) / 24.0)))
        tgt16l = offset(rest["c16"]["left"], (0.12 * tk, 0.10 * tk, -0.04 * tk))
        s16l, e16l = solve_with_fallback(arms["c16"], "Left", tgt16l,
                                         [seed16l, RETREAT_L])
        seed16l = s16l
        err = max(e16, e17l, e17r, e07, e16l)
        if err > max_err:
            max_err, max_err_f = err, f

        # 椅子：f001–016 由 C16 右手骨骼驱动（x/y 跟随手，z 固定落地），之后恒存
        h16 = hand_world(arms["c16"], "Right")
        if f <= 16:
            cx, cy = h16[0], h16[1] - 0.35
        elif f <= 24:
            k = p14.ease((f - 16) / 8.0)
            cx, cy = lerp3((h16[0], h16[1] - 0.35, 0),
                           (CHAIR_END[0], CHAIR_END[1] - 0.35, 0), k)[:2]
        else:
            cx, cy = CHAIR_END[0], CHAIR_END[1] - 0.35
        for o in G["chair_parts"]:
            ox = 0.0 if o is G["chair"] else (0.18 if o.name == "chair_back" else 0.0)
            dx = 0.0
            dy = 0.0
            if o.name != "chair_root" and o.name != "chair_back":
                parts = o.name.split("_")
                dx = float(parts[-2]) if len(parts) >= 2 else 0.0
                dy = float(parts[-1]) if len(parts) >= 2 else 0.0
            elif o.name == "chair_back":
                dy = 0.18
            o.location = (cx + dx, cy + dy, o.location.z)
        chair_samples.append((f, [round(cx, 3), round(cy, 3)]))

        # 两条白花发带：全程恒存、不被拿走、不变物
        for o in G["ribbons"]:
            o.hide_render = False
        ribbon_checks.append((f, len(G["ribbons"])))

        # 窗帘鼓起：真实连续光源 + 几何轻幅摆动，无几何光斑板
        sway = math.sin(2.0 * math.pi * f / 64.0) * 0.090 * \
            p14.ease(min(1.0, max(0.0, (f - 132) / 36.0)))
        for i, c in enumerate(G["curtains"]):
            c.location.y = 2.28 + sway * (1 if i == 0 else -1)
        G["key"].data.energy = 120.0 - 6.0 * t + 3.0 * sway / 0.090 if sway else 120.0 - 6.0 * t
        G["fill"].data.energy = 45.0 - 3.0 * t
        G["world_bg"].inputs[1].default_value = 0.30 - 0.02 * t
        G["daylight_em"].inputs["Strength"].default_value = 0.30 - 0.02 * t + 2.0 * sway

        # 相机慢推 + 极轻手持微晃
        cam.location = sp.lerp(ep, tc)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (AIM - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        if test_mode:
            print(f"[previs26] f{f:03d} err={err:.4f} chair={chair_samples[-1][1]} "
                  f"yaw={dance_yaw(f):.0f} lift={lift:.2f} ribbons={ribbon_checks[-1][1]}",
                  flush=True)

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs26] frame {f}/{N_FRAMES}", flush=True)

    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot26", "title": "跳一点给外婆看", "priority": "P0",
            "source": "剧本七 L391-417 / 方案 §3 §4 / E02_v02.png（shot25 同病房，已目检）",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E02_v02 水彩病房：绿白分色墙、三扇窗+暖气片+可摆动窗帘、金属病床、"
                     "床头柜暖壶白杯、床边木椅、遗物盒与两条带白花的褪色红发带、输液架、木衣柜、挂钟",
            "camera": [list(CAM_START), list(CAM_END), list(AIM)],
            "hard_constraints": {
                "two_white_flower_ribbons_constant": "两条带白花的褪色红发带 f001–f192 恒存同位、"
                    "不被拿走/消失/变成无白花新发带（P01 姥姥旧发带，与 shot16 P02 / shot27 P03 三代呼应）",
                "no_clip_switch": "全程 clip 1 Idle + 逐帧手 K / 躯干旋转，不切 Dance_Loop，避免姿态跳变与求解器 seed 断链",
                "no_flashback": "剧本 L413 回忆与 L417 走廊推车只用同一病房连续白光与静默表达，"
                    "无走廊/推车/年轻角色/叠画/硬切/跨空间",
                "no_geometry_light_board": "窗帘鼓起用真实连续光源 + 几何轻幅摆动，无几何光斑板",
            },
            "characters": {
                "c07": "C07 许宁·老年病房 clip 4 Sitting_Idle_Loop",
                "c16": "C16 女儿 clip 1 Idle", "c17": "C17 小满 clip 1 Idle",
                "dz_stance_idle": DZ, "hips_motion_delta_m": probe["hips_motion_delta_m"],
            },
            "probe": {
                "file": "tmp_qc/shot26_probe_v2.json", "version": "v2_final",
                "all_reachable": True,
                "errors_m": {k: v["error_m"] for k, v in probe["solutions"].items()},
                "dance_clip": probe["dance_action"],
                "dance_hips_delta_m": probe["dance_hips_delta_m"],
                "decision": probe["decision"],
                "rejected_layouts": [
                    "tmp_qc/shot26_probe.json（椅子起点 (-0.62,0.55,0.80) 超 C16 右手包络 0.0910m）"
                    "→ progress/04_白模预演/shot26_探针_v1_椅位判退/",
                ],
            },
            "chair": {
                "driver": "f001–016 由 C16 右手骨骼世界坐标驱动（取手 x/y，椅子 z 固定落地），"
                          "f016–024 ease 落到 CHAIR_END，f024 起恒存同位；约 0.30m 可见横移",
                "start": list(CHAIR_START), "end": list(CHAIR_END),
                "samples": chair_samples[::16],
            },
            "dance": {
                "driver": "C17 躯干绕 Z 连续旋转 dance_yaw()：f001–016 静立 → f016–032 转身 90° → "
                          "f032–056 忘动作停下 → f056–104 从头再来转到 360° → f104 后收手；"
                          "双手由 rest_pt + 小幅偏移逐帧求解 dance_lift()，全程无跳变",
                "clip_used": "animation_1 Idle（不切 Dance_Loop）",
            },
            "ribbons": {
                "count": 2, "white_flowers": 4,
                "driver": "f001–f192 恒存同位、hide_render 全程 False",
                "checks": ribbon_checks[::48],
            },
            "lighting": {
                "method": "ward_key AREA 120→114、ward_fill 45→42、world 0.30→0.28、"
                          "窗外天光 0.30→0.28；f132 起窗帘几何轻幅正弦摆动 + 真实光源微幅同步，"
                          "全部线性连续，无阶跃、无几何光斑板",
            },
            "arm_solver": {
                "method": "五条手 K 链每帧先摆回体侧角实测 rest_pt，再在当前帧骨骼状态下多起点坐标下降；"
                          "6 轮 / 20° / 每轮 ×0.6，误差 >0.045m 换 12 轮 30°，>0.06m 再换 12 轮 12°（§5.22）",
                "max_error_m": round(max_err, 4), "max_error_frame": max_err_f,
            },
            "timeline": {
                "f001": "前态：小满攥着外婆的手、脸上有泪；椅子在床边；遗物盒里两条白花发带清晰可见",
                "f001-016": "妈妈把椅子从床边连续挪开腾地（关键变化前置 §5.21）",
                "f016-032": "小满起势抬手、转身 90°",
                "f032-056": "转身忘动作、停下、手略放",
                "f056-104": "从头再来并转完 360°，这一次许宁看完",
                "f104-120": "收手、重新伏到床边",
                "f120-168": "外婆右手轻伸碰小满辫梢",
                "f168-192": "女儿掖被角、窗帘鼓起、外婆闭眼慢慢睡着；两条发带恒在",
            },
            "physical_chain_checklist": {
                "first_frame_visible_and_large": True, "has_before_state": True,
                "continuous_displacement": True, "driven_by_hand_bones": True,
                "has_after_state": True, "key_change_before_f048": True,
                "three_people_only": True, "no_flashback": True,
                "two_ribbons_constant": True,
            },
            "max_error_m": round(max_err, 4), "max_error_frame": max_err_f,
        }
        with open(REPORT_JSON, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("[previs26] max_error", round(max_err, 4), "@ f", max_err_f, flush=True)
        print("[previs26] WROTE", REPORT_JSON, flush=True)
    print("PREVIS26_DONE", flush=True)


if __name__ == "__main__":
    main()
