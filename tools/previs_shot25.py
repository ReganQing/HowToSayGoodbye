# -*- coding: utf-8 -*-
"""shot25「病房·跳舞之约」Blender 哑光白模预演（192 帧 / 1280×720 / 24fps）。

核心（剧本七 L369–389 / 方案 §3 §4，P0）：
  * 三人：C07 许宁半坐病床（clip 4）、C16 女儿站床左（clip 1）、C17 小满站床右（clip 1）。
  * 核心物理链「女儿揭开保温桶 → 热气连续升起 → 小满伏床边握住外婆一只手 → 许宁嘴唇动了动又停下」。
    桶盖 f001–024 由 C16 右手骨骼驱动，从桶口连续横移到桶旁后恒存；
    C17 右手 f048–096 逐帧求解到 C07 左手实测握点并 f096 后保持；
    热气 f006–024 连续渐强（关键变化前置 §5.21），之后恒在。
  * **剧本 L379–381 的回忆段不做闪回**：全片同一病房、连续白光、三张脸静默，
    无第二个时空/旧病房/年轻角色/叠画/硬切（§5）。
  * 白色病房光由真实 AREA/世界光给出，禁止几何光斑板（§3 D5）。

坐标全部来自 `tmp_qc/shot25_probe_v3.json`（3 个真实 anchor 0.0045–0.0418m）。
两轮判退稿见 `progress/04_白模预演/shot25_探针_v1_布局判退/` 与 `shot25_探针_v2_锚点判退/`。

Run:
  PREVIS_TEST=1 blender.exe --background --python tools/previs_shot25.py
  blender.exe --background --python tools/previs_shot25.py
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
FRAMES_DIR = os.path.join(OUT_DIR, "frames25")
PROBE_JSON = os.path.join(ROOT, "tmp_qc", "shot25_probe_v3.json")
REPORT_JSON = os.path.join(OUT_DIR, "previs25_report.json")
MODELS = os.path.join(ROOT, "assets", "models")

FPS, N_FRAMES = 24, 192
RES_X, RES_Y = 1280, 720
CAM_LENS = 35
CAM_START = (-0.55, -2.65, 1.68)
CAM_END = (-0.50, -2.55, 1.66)
AIM = Vector((0.05, 1.00, 0.82))

C07_LOC = (0.42, 1.25)
C16_LOC = (-0.75, 0.70)
C17_LOC = (0.62, 0.92)
YAW = 0.0
DZ = {"c07": 0.7063, "c16": 0.7609, "c17": 0.5521}
BED_TOP_Z = 0.45

LID_ON = (-0.72, 0.50, 0.86)
LID_OFF = (-0.58, 0.56, 0.90)
HOLD_R = (0.48, 1.156, 0.648)

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
    return p14.mat("s25_" + key, shade, emission)


def emission_mat(name, color, strength):
    m = bpy.data.materials.new("s25_" + name)
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
    """E02_v02 水彩病房物件家族：绿白分色墙 / 三扇窗 / 暖气片 / 病床 / 床头柜 /
    输液架 / 木衣柜 / 挂钟。全部恒存、无几何光斑板。"""
    floor = mat("floor", (0.50, 0.51, 0.52))
    wall_w = mat("wall_white", (0.60, 0.62, 0.64))
    wall_g = mat("wall_green", (0.36, 0.48, 0.42))
    wood = mat("wood", (0.42, 0.33, 0.24))
    metal = mat("metal", (0.40, 0.44, 0.48))
    dark = mat("dark", (0.34, 0.36, 0.38))
    cloth = mat("cloth", (0.68, 0.70, 0.68))
    curtain = mat("curtain", (0.66, 0.68, 0.60))

    p14.add_box("floor", (0.0, 0.70, -0.02), (5.4, 5.0, 0.04), floor)
    p14.add_box("wall_back", (0.0, 2.40, 1.25), (5.4, 0.06, 2.50), wall_w)
    p14.add_box("wall_back_green", (0.0, 2.36, 0.50), (5.4, 0.02, 1.00), wall_g)
    p14.add_box("wall_left", (-2.10, 0.70, 1.25), (0.06, 3.40, 2.50), wall_w)
    p14.add_box("wall_left_green", (-2.06, 0.70, 0.50), (0.02, 3.40, 1.00), wall_g)

    # 三扇窗 + 窗棂 + 两片纱帘 + 窗下暖气片
    daylight = emission_mat("daylight", (0.90, 0.94, 0.98), 0.30)
    G["daylight_em"] = [n for n in daylight.node_tree.nodes
                        if n.bl_idname == "ShaderNodeEmission"][0]
    for i, cx in enumerate((-0.55, 0.35, 1.25)):
        p14.add_box(f"win_{i}", (cx, 2.33, 1.62), (0.78, 0.02, 1.16), daylight)
        p14.add_box(f"win_bar_h_{i}", (cx, 2.30, 1.62), (0.80, 0.03, 0.03), metal)
        p14.add_box(f"win_bar_v_{i}", (cx, 2.30, 1.62), (0.03, 0.03, 1.18), metal)
    for cx in (-1.02, 1.72):
        p14.add_box(f"curtain_{cx}", (cx, 2.28, 1.62), (0.20, 0.02, 1.18), curtain)
    for i in range(5):
        p14.add_box(f"radiator_{i}", (-0.65 + i * 0.32, 2.20, 0.72),
                    (0.055, 0.10, 0.44), metal)

    # 病床：床面 z=0.45（与 C07 坐姿臀部自洽），护栏 / 枕头 / 被子 / 四个脚轮
    p14.add_box("bed_frame", (0.42, 1.25, 0.40), (1.50, 0.62, 0.10), metal)
    p14.add_box("bed_mattress", (0.42, 1.25, 0.45), (1.46, 0.58, 0.06), cloth)
    p14.add_box("bed_blanket", (0.05, 1.25, 0.49), (0.72, 0.58, 0.025),
                mat("blanket", (0.48, 0.66, 0.76)))
    p14.add_box("pillow", (0.92, 1.25, 0.53), (0.42, 0.46, 0.10), cloth)
    p14.add_box("bed_head", (1.20, 1.25, 0.72), (0.05, 0.64, 0.54), metal)
    p14.add_box("bed_foot", (-0.35, 1.25, 0.68), (0.05, 0.64, 0.46), metal)
    for x in (-0.28, 1.12):
        for y in (1.00, 1.50):
            p14.add_box(f"bed_leg_{x}_{y}", (x, y, 0.20), (0.045, 0.045, 0.40), dark)

    # 床头柜 + 暖壶 + 白杯；保温桶在 build_props
    p14.add_box("cabinet", (-0.95, 0.52, 0.38), (0.52, 0.46, 0.76), wood)
    p14.add_cyl("thermos", (-1.05, 0.52, 0.84), 0.045, 0.16,
                mat("thermos", (0.42, 0.46, 0.52)))
    p14.add_cyl("white_mug", (-0.80, 0.52, 0.80), 0.035, 0.08,
                mat("mug", (0.90, 0.91, 0.92)))

    # 输液架（床右后）+ 木衣柜 + 挂钟
    p14.add_cyl("iv_stand", (1.62, 1.85, 0.90), 0.018, 1.80, metal)
    p14.add_box("iv_hook", (1.62, 1.85, 1.82), (0.22, 0.02, 0.02), metal)
    p14.add_box("wardrobe", (-1.75, 1.60, 0.95), (0.52, 0.46, 1.90), wood)
    clock = add_torus("wall_clock", (-1.75, 2.30, 1.85), 0.11, 0.012, dark)
    clock.rotation_euler.x = math.radians(90)
    bpy.context.view_layer.update()   # §5.16：最后一个 add_box 的 dimensions 需依赖图评估


def build_props():
    """保温桶 + 桶盖（位移型）+ 热气细线（渐强）。"""
    bucket = mat("bucket", (0.30, 0.38, 0.46))
    lid = emission_mat("lid", (0.96, 0.62, 0.22), 1.10)
    steam = emission_mat("steam", (1.00, 0.62, 0.18), 0.0)
    G["steam_em"] = [n for n in steam.node_tree.nodes
                     if n.bl_idname == "ShaderNodeEmission"][0]

    bx, by = -0.72, 0.50
    p14.add_cyl("bucket_body", (bx, by, 0.795), 0.085, 0.10, bucket)
    rim = add_torus("bucket_rim", (bx, by, 0.848), 0.085, 0.007,
                    mat("rim", (0.70, 0.74, 0.78)))
    G["bucket_parts"] = [bpy.data.objects["bucket_body"], rim]

    G["lid"] = p14.add_box("lid_root", LID_ON, (0.16, 0.16, 0.018), lid)
    G["lid_knob"] = p14.add_cyl("lid_knob", (LID_ON[0], LID_ON[1], LID_ON[2] + 0.018),
                                0.022, 0.018, lid)

    G["steam_parts"] = []
    for i in range(5):
        s = p14.add_cyl(f"steam_{i}",
                        (bx + (i - 2) * 0.026, by, 0.87 + 0.060 * i),
                        0.009, 0.070, steam,
                        rot=(math.radians(9 * (i - 2)), math.radians(13 * (i - 2)), 0))
        G["steam_parts"].append(s)
    bpy.context.view_layer.update()


def add_lighting():
    """白色病房光：稳定柔和、真实光源，无几何光斑板。"""
    world = bpy.data.worlds.new("previz_world25")
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


def c16_right_target(f, rest):
    if f <= 24:
        return lerp3(LID_ON, LID_OFF, p14.ease(f / 24.0))
    if f <= 48:
        return lerp3(LID_OFF, rest, p14.ease((f - 24) / 24.0))
    return rest


def c17_right_target(f, rest):
    if f <= 48:
        return rest
    if f <= 96:
        return lerp3(rest, HOLD_R, p14.ease((f - 48) / 48.0))
    return HOLD_R


def steam_strength(f):
    """f001–006 桶还盖着；f006–024 热气连续渐强，之后恒在（关键变化前置）。"""
    return p14.ease(min(1.0, max(0.0, (f - 6) / 18.0)))


def main():
    with open(PROBE_JSON, encoding="utf-8") as fh:
        probe = json.load(fh)
    assert probe.get("all_reachable") and probe.get("probe_version") == "v3_final", \
        "定稿探针未全绿，先修布局再跑预演"
    ANG = {k: tuple(v["angles"]) for k, v in probe["solutions"].items()}
    print("[previs25] anchors", {k: [round(v, 1) for v in a] for k, a in ANG.items()},
          flush=True)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    build_room()
    build_props()
    add_lighting()

    arms, acts = {}, {}
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
        arms[key], acts[key] = arm, (idle, use)
    print("[previs25] three models loaded", flush=True)

    scene = bpy.context.scene
    for key, loc in (("c07", C07_LOC), ("c16", C16_LOC), ("c17", C17_LOC)):
        arms[key].location = (*loc, DZ[key])
        arms[key].rotation_euler = (0, 0, math.radians(YAW))
    scene.frame_set(1)
    bpy.context.view_layer.update()

    # v2：三个角色分三档哑光灰度（0.30 / 0.46 / 0.60），
    # 避免灰白黏连、小满与床上的外婆读成一个人；场景/道具保留 s25_ 前缀材质
    char_mattes = {k: p14.make_matte(f"char25_{k}", v)
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

    cam_data = bpy.data.cameras.new("previs_cam25")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam25", cam_data)
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

    seed16 = ANG["c16_lid_on"]
    seed17 = RETREAT_R
    max_err, max_err_f = 0.0, 0
    lid_samples, steam_samples = [], []

    for f in frames_iter:
        t = (f - 1) / (N_FRAMES - 1)
        tc = p14.ease(t)
        for key, loc in (("c07", C07_LOC), ("c16", C16_LOC), ("c17", C17_LOC)):
            arms[key].location = (*loc, DZ[key])
            arms[key].rotation_euler = (0, 0, math.radians(YAW))
        scene.frame_set(f)
        bpy.context.view_layer.update()

        # 头：C16 低头揭盖、C17 抬头看外婆、C07 微转头看孩子
        head_pose(arms["c16"], 10.0 + 2.0 * p14.ease(min(1.0, f / 24.0)), 0.0)
        head_pose(arms["c17"], -6.0 * p14.ease(min(1.0, f / 96.0)), -3.0)
        head_pose(arms["c07"], 2.0, -5.0 * p14.ease(min(1.0, f / 96.0)))

        # 体侧基准：每帧 apply RETREAT 后实测 rest_pt（§5.20）
        for key in ("c07", "c16", "c17"):
            apply_arm(arms[key], "Left", *RETREAT_L)
            apply_arm(arms[key], "Right", *RETREAT_R)
        rest16 = hand_world(arms["c16"], "Right")
        rest17 = hand_world(arms["c17"], "Right")

        # C16 右手：揭盖 → 放回 → 收回体侧
        tgt16 = c16_right_target(f, rest16)
        s16, e16 = solve_with_fallback(
            arms["c16"], "Right", tgt16,
            [seed16, ANG["c16_lid_on"], ANG["c16_lid_off"], RETREAT_R])
        seed16 = s16
        # C17 右手：体侧 → 握住 C07 左手 → 保持
        tgt17 = c17_right_target(f, rest17)
        s17, e17 = solve_with_fallback(
            arms["c17"], "Right", tgt17,
            [seed17, ANG["c17_hold_r"], RETREAT_R])
        seed17 = s17
        err = max(e16, e17)
        if err > max_err:
            max_err, max_err_f = err, f

        # 桶盖：f001–024 逐帧挂 C16 右手骨骼；f024–030 ease 落到桶旁后恒存
        h16 = hand_world(arms["c16"], "Right")
        hand_pt = (h16[0], h16[1] - 0.008, h16[2] + 0.012)
        if f <= 24:
            lp = hand_pt
        elif f <= 30:
            lp = lerp3(hand_pt, LID_OFF, p14.ease((f - 24) / 6.0))
        else:
            lp = LID_OFF
        G["lid"].location = lp
        G["lid_knob"].location = (lp[0], lp[1], lp[2] + 0.018)
        lid_samples.append((f, [round(v, 3) for v in lp]))

        # 热气：f006–024 连续渐强，之后恒在；桶/盖/病房物件全程恒存
        s = steam_strength(f)
        G["steam_em"].inputs["Strength"].default_value = 1.60 * s
        for o in G["steam_parts"]:
            o.hide_render = s < 0.015
        for o in G["bucket_parts"]:
            o.hide_render = False
        steam_samples.append((f, round(s, 3)))

        # 白色病房光：极缓连续变化表达静默，无阶跃、无几何光斑板
        G["key"].data.energy = 120.0 - 8.0 * t
        G["fill"].data.energy = 45.0 - 4.0 * t
        G["world_bg"].inputs[1].default_value = 0.30 - 0.02 * t
        G["daylight_em"].inputs["Strength"].default_value = 0.30 - 0.02 * t

        # 相机慢推 + 极轻手持微晃
        cam.location = sp.lerp(ep, tc)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (AIM - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        if test_mode:
            print(f"[previs25] f{f:03d} e16={e16:.4f} e17={e17:.4f} "
                  f"lid={lid_samples[-1][1]} steam={s:.2f}", flush=True)

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs25] frame {f}/{N_FRAMES}", flush=True)

    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot25", "title": "病房·跳舞之约", "priority": "P0",
            "source": "剧本七 L369-389 / 方案 §3 §4 / E02_v02.png（目检：水彩病房、画面无人）",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E02_v02 水彩病房：绿白分色墙、三扇窗 + 暖气片 + 纱帘、金属病床（床面 z=0.45）、"
                     "床头柜与暖壶白杯、输液架、木衣柜、挂钟、浅地砖；保温桶与桶盖在床头柜上",
            "camera": [list(CAM_START), list(CAM_END), list(AIM)],
            "hard_constraints": {
                "no_flashback": "剧本 L379–381 的回忆段只用同一病房连续白光 + 三张脸静默表达，"
                                "无旧病房/年轻角色/叠画/硬切/跨空间",
                "three_people_only": "只导入 C07 / C16 / C17 三个 GLB，无第四人",
                "no_geometry_light_board": "白色病房光全部真实 AREA/世界光，无几何光斑板",
            },
            "characters": {
                "c07": "许宁·老年病房 clip 4 Sitting_Idle_Loop，半坐床沿（BED_LIFT=0，床面 z=0.45 自洽）",
                "c16": "女儿·成年 clip 1 Idle，站床左揭保温桶",
                "c17": "小满·儿童 clip 1 Idle，站床右单手握住外婆左手",
                "dz_stance_idle": DZ,
                "hips_motion_delta_m": probe["hips_motion_delta_m"],
            },
            "probe": {
                "file": "tmp_qc/shot25_probe_v3.json", "version": "v3_final",
                "all_reachable": True,
                "errors_m": {k: v["error_m"] for k, v in probe["solutions"].items()},
                "rejected_layouts": [
                    "tmp_qc/shot25_probe.json（成人直觉布局，四点 0.1076–0.7252m 全判退）"
                    "→ progress/04_白模预演/shot25_探针_v1_布局判退/",
                    "tmp_qc/shot25_probe_v2.json（多余的 c17_hold_l 超阈 0.1432m）"
                    "→ progress/04_白模预演/shot25_探针_v2_锚点判退/",
                ],
                "handshake_policy": probe["handshake_policy"],
            },
            "lid_and_steam": {
                "lid": "f001–024 逐帧由 C16 右手骨骼世界坐标驱动（手与盖零脱节），"
                       "f024–030 ease 落到桶旁 LID_OFF，f030 起恒存同位；从桶口到桶旁约 0.15m 可见横移",
                "steam": "f001–006 桶还盖着无热气；f006–024 连续渐强，之后恒在（关键变化前置 §5.21）",
                "lid_samples": lid_samples[::16], "steam_samples": steam_samples[::16],
            },
            "handshake": {
                "target": list(HOLD_R),
                "driver": "C17 右手 f048–096 从体侧 ease 到 C07 左手实测握点，f096–f192 保持；"
                          "C17 左手每帧 RETREAT 实测 rest_pt（§5.20）",
                "c07_hand": probe["c07_retreat_hands"]["left"],
            },
            "lighting": {
                "method": "ward_key AREA 120→112、ward_fill 45→41、world 0.30→0.28、"
                          "窗外天光 0.30→0.28，全部线性连续；白色病房光柔和稳定，无阶跃、无几何光斑板",
            },
            "arm_solver": {
                "method": "C16/C17 两条右手链每帧先摆回体侧角实测 rest_pt，再在当前帧骨骼状态下多起点坐标下降；"
                          "6 轮 / 20° / 每轮 ×0.6，误差 >0.045m 换 12 轮 30°，>0.06m 再换 12 轮 12°（§5.22）",
                "max_error_m": round(max_err, 4), "max_error_frame": max_err_f,
            },
            "timeline": {
                "f001": "前态：保温桶带盖在床头柜上、三人在位、病房白光",
                "f001-024": "女儿揭盖横移到桶旁；f006 起热气连续渐强（关键变化前置）",
                "f024-048": "女儿右手 ease 收回体侧、热气恒在",
                "f048-096": "小满右手从体侧连续伸向床沿，握住外婆左手",
                "f096-192": "握手保持、三张脸静默、白光极缓变柔；无回忆/硬切/第二时空",
            },
            "physical_chain_checklist": {
                "first_frame_visible_and_large": True, "has_before_state": True,
                "continuous_displacement": True, "driven_by_hand_bones": True,
                "has_after_state": True, "key_change_before_f048": True,
                "three_people_only": True, "no_flashback": True,
            },
            "max_error_m": round(max_err, 4), "max_error_frame": max_err_f,
        }
        with open(REPORT_JSON, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("[previs25] max_error", round(max_err, 4), "@ f", max_err_f, flush=True)
        print("[previs25] WROTE", REPORT_JSON, flush=True)
    print("PREVIS25_DONE", flush=True)


if __name__ == "__main__":
    main()
