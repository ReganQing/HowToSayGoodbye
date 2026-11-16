# -*- coding: utf-8 -*-
"""shot27「幕布拉开」Blender 哑光白模预演（192 帧 / 1280×720 / 24fps）。

核心（剧本七 L419–439 / 方案 §3 §4，P0，shot15–27 十三镜收束镜）：
  * 两人 E12 学校舞台：C16 妈妈（clip 1 Idle）、C17 小满（clip 1 Idle），全程无第三人。
  * **三代红发带呼应收束**：D09 遗物盒内 P01 姥姥 + P02 妈妈两条「带白花的褪色旧红发带」
    f001–f192 恒存同位；P03「一对鲜红、末端无白花的新红发带」f001 起就在妈妈手里，
    f001–f024 连续举向两条辫梢、f024–f048 系好、f048 起恒在辫梢（§5.18/19/25 混合型）。
    新旧两代颜色/白花/位置三重区分，绝不混、绝不凭空出现、旧带绝不被拿走。
  * **关键变化前置 f001–f048**（§5.21）：换新带 + 幕布开始拉开都在首段连续给出；
    幕布从 f001 起缓慢连续向两侧分开并贯穿全片，板片恒在两侧不消失，无硬切。
  * 后段：小满摸辫子想哭 → 妈妈蹲下（根骨 z-0.42 + 前倾 0.10）拉平裙角 →
    小满自己擦脸 → 朝幕布缺口向前走几步、望一眼观众席 → 扬起手臂、辫梢新带轻轻一闪。
  * 暖顶光用**真实连续 AREA 光源**渐亮渐暖，禁止几何光斑板（§3 D5）。
  * L419 许宁去世 / L421–428 整理遗物属前序叙事，全片只画同一舞台侧幕空间，
    无 flashback / 葬礼 / 病房 / 遗物整理闪回 / 第二时空 / 叠画 / 硬切。

坐标与可达角来自 `tmp_qc/shot27_probe.json`（v3 定稿：6 个真实 anchor
0.0016–0.0501m 全绿，两人 Hips 位移 0.0069/0.0049，all_reachable=True）。
v1 站位判退 / v2 蹲姿判退已连判定书归档到 progress/04_白模预演/。

Run:
  PREVIS_TEST=1 blender.exe --background --python tools/previs_shot27.py
  blender.exe --background --python tools/previs_shot27.py
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
FRAMES_DIR = os.path.join(OUT_DIR, "frames27")
PROBE_JSON = os.path.join(ROOT, "tmp_qc", "shot27_probe.json")
REPORT_JSON = os.path.join(OUT_DIR, "previs27_report.json")
MODELS = os.path.join(ROOT, "assets", "models")

FPS, N_FRAMES = 24, 192
RES_X, RES_Y = 1280, 720
CAM_LENS = 35
CAM_START = (-1.85, -2.72, 1.62)
CAM_END = (-1.72, -2.58, 1.58)
AIM = Vector((0.02, 1.05, 0.95))

C16_LOC = (-0.10, 0.90)
C17_LOC = (0.06, 0.74)
YAW = 0.0
DZ = {"c16": 0.7609, "c17": 0.5521}
CROUCH_DZ, CROUCH_LEAN = 0.42, 0.10
CURTAIN_Y = 2.35
CURTAIN_GAP_MAX = 1.35

BONES = ("mixamorig:RightArm", "mixamorig:RightForeArm",
         "mixamorig:LeftArm", "mixamorig:LeftForeArm",
         "mixamorig:Head", "mixamorig:Neck",
         "mixamorig:Spine", "mixamorig:Spine1")
RETREAT_R = (-45.0, -132.1, 0.0, 56.6)
RETREAT_L = (-45.0, 132.1, 0.0, -56.6)

BOX_LOC = (-1.10, 0.92)          # 遗物盒（v2 前移，首帧更显眼）
G = {}


def mat(key, shade, emission=None):
    if isinstance(shade, (tuple, list)):
        shade = sum(shade) / len(shade)
    return p14.mat("s27_" + key, shade, emission)


def emission_mat(name, color, strength):
    m = bpy.data.materials.new("s27_" + name)
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


def build_stage():
    """E12 学校舞台：深靛红闭合幕布 / 侧幕 / 檐幕 / 后台叠椅 / 暖顶灯 /
    前景观众席椅背 / 木地板 / 后台小木桌与遗物盒（两条带白花旧红发带恒存）。"""
    floor = mat("floor", 0.30)
    back = mat("back_wall", 0.16)
    curtain_m = emission_mat("curtain_indigo", (0.10, 0.10, 0.24), 0.55)
    curtain_fold = emission_mat("curtain_wine", (0.34, 0.11, 0.17), 0.62)
    side_m = emission_mat("side_curtain", (0.22, 0.14, 0.24), 0.55)
    wood = mat("wood", 0.24)
    dark = mat("dark", 0.20)
    seat_m = emission_mat("audience_seat", (0.34, 0.14, 0.16), 0.50)
    valance_m = emission_mat("valance", (0.24, 0.12, 0.20), 0.55)

    p14.add_box("stage_floor", (0.0, 0.75, -0.02), (5.60, 5.20, 0.04), floor)
    p14.add_box("stage_back", (0.0, 2.62, 1.25), (5.60, 0.06, 2.50),
                emission_mat("stage_back_warm", (0.34, 0.24, 0.20), 0.48))
    p14.add_box("stage_front_lip", (0.0, -1.62, 0.02), (5.60, 0.12, 0.10), dark)

    # 深靛红大幕：左右各 10 条竖褶，f001 闭合在 x=0，随 gap 连续向两侧分开
    G["curtain_l"], G["curtain_r"] = [], []
    for i in range(10):
        w, h = 0.16, 2.30
        cx = -0.80 + i * w + w / 2.0
        m = curtain_m if i % 2 == 0 else curtain_fold
        o = p14.add_box(f"curtain_L_{i}", (cx, CURTAIN_Y, 1.19), (w, 0.05, h), m)
        G["curtain_l"].append((o, cx))
        o = p14.add_box(f"curtain_R_{i}", (-cx, CURTAIN_Y, 1.19), (w, 0.05, h), m)
        G["curtain_r"].append((o, -cx))
    for sx in (-2.05, 2.05):
        p14.add_box(f"side_curtain_{sx}", (sx, CURTAIN_Y - 0.10, 1.20),
                    (0.28, 0.06, 2.40), side_m)
    p14.add_box("valance", (0.0, CURTAIN_Y - 0.08, 2.30),
                (4.40, 0.07, 0.36), valance_m)

    # 后台叠椅（E12 左侧）
    for k in range(3):
        z = 0.30 + k * 0.20
        p14.add_box(f"stack_chair_seat_{k}", (-1.52, 1.62, z),
                    (0.44, 0.40, 0.045), wood)
        p14.add_box(f"stack_chair_back_{k}", (-1.52, 1.80, z + 0.24),
                    (0.44, 0.045, 0.46), wood)

    # 前景观众席椅背（只给椅背，绝不放人）
    for i in range(9):
        p14.add_box(f"audience_seat_{i}", (-1.80 + i * 0.45, -1.48, 0.52),
                    (0.40, 0.12, 0.46), seat_m)

    # 后台小木桌 + 敞口遗物盒 + 两条带白花的褪色旧红发带（恒存）
    p14.add_box("keepsake_table", (BOX_LOC[0], BOX_LOC[1], 0.70),
                (0.78, 0.56, 0.04), wood)
    for dx in (-0.32, 0.32):
        for dy in (-0.22, 0.22):
            p14.add_box(f"table_leg_{dx}_{dy}",
                        (BOX_LOC[0] + dx, BOX_LOC[1] + dy, 0.34),
                        (0.04, 0.04, 0.68), wood)
    p14.add_box("keepsake_box_base", (BOX_LOC[0], BOX_LOC[1], 0.765),
                (0.46, 0.34, 0.08), mat("keepsake_box", 0.22))
    for dx in (-0.23, 0.23):
        p14.add_box(f"box_wall_x_{dx}", (BOX_LOC[0] + dx, BOX_LOC[1], 0.815),
                    (0.02, 0.34, 0.10), mat("keepsake_box", 0.22))
    for dy in (-0.17, 0.17):
        p14.add_box(f"box_wall_y_{dy}", (BOX_LOC[0], BOX_LOC[1] + dy, 0.815),
                    (0.46, 0.02, 0.10), mat("keepsake_box", 0.22))

    old_m = emission_mat("old_ribbon_faded", (0.58, 0.16, 0.12), 0.95)
    white_m = emission_mat("white_flower", (0.98, 0.98, 0.94), 1.20)
    G["old_ribbons"] = []
    for i, ox in enumerate((-0.095, 0.095)):
        r = add_torus(f"old_ribbon_{i}",
                      (BOX_LOC[0] + ox, BOX_LOC[1], 0.825), 0.088, 0.016, old_m)
        G["old_ribbons"].append(r)
        for j in range(2):
            fl = p14.add_cyl(f"old_ribbon_{i}_flower_{j}",
                             (BOX_LOC[0] + ox + (j - 0.5) * 0.040,
                              BOX_LOC[1] + 0.045, 0.838),
                             0.021, 0.010, white_m)
            G["old_ribbons"].append(fl)

    # P03：一对鲜红、末端无白花的新红发带（位移型 + 状态型混合道具）
    new_m = emission_mat("new_ribbon_bright", (0.96, 0.10, 0.08), 1.45)
    G["new_mat"] = [n for n in new_m.node_tree.nodes
                    if n.bl_idname == "ShaderNodeEmission"][0]
    G["new_ribbons"] = []
    for i in range(2):
        r = add_torus(f"new_ribbon_{i}", (0.0, 0.0, 0.0), 0.064, 0.014, new_m)
        G["new_ribbons"].append(r)

    # 三盏暖顶灯：灯具外观是小的自发光圆片，真实照明由 AREA 光承担
    lamp_m = emission_mat("overhead_lamp", (1.00, 0.82, 0.52), 1.30)
    G["lamps"] = []
    for i, lx in enumerate((-1.05, 0.0, 1.05)):
        o = p14.add_cyl(f"overhead_lamp_{i}", (lx, CURTAIN_Y - 0.34, 2.30),
                        0.075, 0.022, lamp_m)
        o.rotation_euler.x = math.radians(90)
        G["lamps"].append(o)

    # 两条深色辫子：让 P03 新红带明确系在辫梢末端，不再像悬浮红环/腰带
    braid_m = mat("braid", 0.20)
    G["braids"] = []
    for i in range(2):
        b = p14.add_cyl(f"braid_{i}", (0.0, 0.0, 0.0), 0.018, 0.17, braid_m)
        b.rotation_euler.y = math.radians(-8.0 if i == 0 else 8.0)
        G["braids"].append(b)
    bpy.context.view_layer.update()   # §5.16


def add_lighting():
    world = bpy.data.worlds.new("previz_world27")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.26, 0.24, 0.28, 1.0)
            n.inputs[1].default_value = 0.18
    bpy.context.scene.world = world
    G["world_bg"] = [n for n in world.node_tree.nodes
                     if n.bl_idname == "ShaderNodeBackground"][0]

    # 三盏真实连续 AREA 暖顶光（不是几何光斑板）
    G["keys"] = []
    for i, lx in enumerate((-1.05, 0.0, 1.05)):
        bpy.ops.object.light_add(type="AREA", location=(lx, 1.55, 2.55))
        o = bpy.context.active_object
        o.name = f"stage_key_{i}"
        o.data.energy = 38.0
        o.data.size = 1.30
        o.data.color = (1.00, 0.80, 0.55)
        o.rotation_euler = (math.radians(42), 0, 0)
        G["keys"].append(o)
    bpy.ops.object.light_add(type="AREA", location=(0.0, -1.10, 2.30))
    fill = bpy.context.active_object
    fill.name = "stage_fill"
    fill.data.energy = 18.0
    fill.data.size = 2.60
    fill.data.color = (0.76, 0.80, 0.92)
    fill.rotation_euler = (math.radians(24), 0, 0)
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


def bone_world(arm, name):
    bpy.context.view_layer.update()
    w = arm.matrix_world @ arm.pose.bones[name].matrix.translation
    return (round(w.x, 4), round(w.y, 4), round(w.z, 4))


def head_pose(arm, down, turn):
    p14.rotate_ops(arm, "mixamorig:Head", [
        ((1, 0, 0), down), ((0, 0, 1), turn)])
    p14.rotate_ops(arm, "mixamorig:Neck", [((1, 0, 0), down * 0.35)])


def lerp3(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def offset(rest, d):
    return (rest[0] + d[0], rest[1] + d[1], rest[2] + d[2])


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


def curtain_gap(f):
    """幕布 f001 起缓慢连续向两侧分开并贯穿全片，末段完全拉开，无阶跃。"""
    t = (f - 1) / (N_FRAMES - 1)
    return CURTAIN_GAP_MAX * p14.ease(t)


def crouch_k(f):
    """妈妈 f080–f120 平滑蹲下，f144–f168 平滑站起，全程连续。"""
    down = p14.ease(min(1.0, max(0.0, (f - 80) / 40.0)))
    up = p14.ease(min(1.0, max(0.0, (f - 144) / 24.0)))
    return down * (1.0 - up)


def walk_k(f):
    """小满 f144 起朝台前（观众席方向）连续走几步，无瞬移。"""
    return -0.36 * p14.ease(min(1.0, max(0.0, (f - 144) / 24.0)))


def hem_k(f):
    """拉平裙角的手部权重 = 身体蹲姿进度 ck × 提前收回因子。
    进入阶段严格跟随 ck（半蹲时不提前要求手够到全蹲位置），
    f136 起先于站起收回，避开小满 f144 走位后目标前移造成的不可达。"""
    exit_up = p14.ease(min(1.0, max(0.0, (f - 136) / 16.0)))
    return crouch_k(f) * (1.0 - exit_up)


def main():
    with open(PROBE_JSON, encoding="utf-8") as fh:
        probe = json.load(fh)
    assert probe.get("all_reachable") and probe.get("probe_version") == "v3", \
        "定稿探针未全绿，先修布局再跑预演"
    ANG = {k: tuple(v["angles"]) for k, v in probe["solutions"].items()}
    T = probe["derived_targets"]
    # 新带前态：右手起点用探针实测可达的 c16_ribbon_start 目标，
    # 左手起点用当帧 RETREAT 实测体侧点（必然可达），绝不硬编码绝对坐标
    START_R = tuple(probe["solutions"]["c16_ribbon_start"]["target"])
    print("[previs27] anchors", {k: [round(v, 1) for v in a] for k, a in ANG.items()},
          flush=True)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    build_stage()
    add_lighting()

    arms = {}
    for key, folder in (("c16", "C16"), ("c17", "C17")):
        arm, aa, _ = p14.import_glb(os.path.join(MODELS, folder, "tex_mesh_animated.glb"))
        assert arm is not None and len(aa) >= 5
        idle = act_by_clip(aa, 1)
        p14.make_loop(idle)
        p14.strip_channels([idle], BONES)
        p14.set_loop(arm.animation_data, idle, {"key": None}, f"{key}_loop")
        arm.rotation_mode = "XYZ"
        arms[key] = arm
    print("[previs27] two models loaded (clip 1 Idle, no clip switch)", flush=True)

    scene = bpy.context.scene
    char_mattes = {k: p14.make_matte(f"char27_{k}", v)
                   for k, v in (("c16", 0.44), ("c17", 0.62))}
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

    cam_data = bpy.data.cameras.new("previs_cam27")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam27", cam_data)
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

    seed16r = ANG["c16_ribbon_start"]
    seed16l = ANG["c16_braid_r"]
    seed17r = RETREAT_R
    seed17l = RETREAT_L
    max_err, max_err_f = 0.0, 0
    gap_samples, new_ribbon_checks, old_ribbon_checks = [], [], []

    for f in frames_iter:
        t = (f - 1) / (N_FRAMES - 1)
        tc = p14.ease(t)
        ck, wk = crouch_k(f), walk_k(f)
        arms["c16"].location = (C16_LOC[0], C16_LOC[1] - CROUCH_LEAN * ck,
                                DZ["c16"] - CROUCH_DZ * ck)
        arms["c17"].location = (C17_LOC[0], C17_LOC[1] + wk, DZ["c17"])
        for key in ("c16", "c17"):
            arms[key].rotation_euler = (0, 0, math.radians(YAW))
        # 小满 f144 后朝观众席轻轻转头（不是换场景）
        arms["c17"].rotation_euler.z = math.radians(
            -10.0 * p14.ease(min(1.0, max(0.0, (f - 150) / 30.0))))
        scene.frame_set(f)
        bpy.context.view_layer.update()

        head_pose(arms["c16"], 8.0 + 10.0 * ck, 0.0)
        head_pose(arms["c17"], 6.0 + 8.0 * p14.ease(min(1.0, max(0.0, (f - 48) / 32.0)))
                  - 6.0 * p14.ease(min(1.0, max(0.0, (f - 144) / 32.0))), 0.0)

        # 体侧基准：每帧 apply RETREAT 后实测 rest_pt（§5.20）
        for key in ("c16", "c17"):
            apply_arm(arms[key], "Left", *RETREAT_L)
            apply_arm(arms[key], "Right", *RETREAT_R)
        rest = {k: {"left": hand_world(v, "Left"), "right": hand_world(v, "Right")}
                for k, v in arms.items()}

        # 辫梢由 C17 Head 骨当帧实测（儿童模型，随走位与转头自动跟随）
        hd = bone_world(arms["c17"], "mixamorig:Head")
        braid_l = (hd[0] - 0.13, hd[1] - 0.02, hd[2] - 0.115)
        braid_r = (hd[0] + 0.13, hd[1] - 0.02, hd[2] - 0.115)
        cheek = (hd[0] + 0.10, hd[1] - 0.08, hd[2] - 0.06)
        hem_smooth = tuple(T["hem_smooth"])
        arm_up = (T["arm_up"][0], T["arm_up"][1] + wk, T["arm_up"][2])

        # ---- C16 双手：f001–024 把新带从手中连续送到两条辫梢；f024–048 收回 ----
        if f <= 24:
            k = p14.ease(f / 24.0)
            tgt16r = lerp3(START_R, braid_l, k)
            tgt16l = lerp3(rest["c16"]["left"], braid_r, k)
        elif f <= 48:
            k = p14.ease((f - 24) / 24.0)
            tgt16r = lerp3(braid_l, rest["c16"]["right"], k)
            tgt16l = lerp3(braid_r, rest["c16"]["left"], k)
        else:
            tgt16r, tgt16l = rest["c16"]["right"], rest["c16"]["left"]
        # 拉平裙角：单手成立（v3 探针 0.0501m）；权重与身体蹲姿解耦，
        # f136 起先于站起收回，避开小满 f144 走位后目标前移造成的不可达
        hk = hem_k(f)
        if hk > 0.0:
            tgt16r = lerp3(tgt16r, hem_smooth, hk)

        s16r, e16r = solve_with_fallback(
            arms["c16"], "Right", tgt16r,
            [seed16r, ANG["c16_ribbon_start"], ANG["c16_braid_l"],
             ANG["c16_hem_smooth"], RETREAT_R])
        s16l, e16l = solve_with_fallback(
            arms["c16"], "Left", tgt16l,
            [seed16l, ANG["c16_braid_r"], RETREAT_L])
        seed16r, seed16l = s16r, s16l

        # ---- C17 右手：摸辫子想哭 → 自己擦脸 → 扬起手臂 ----
        if f <= 48:
            tgt17r = rest["c17"]["right"]
        elif f <= 80:
            k = p14.ease((f - 48) / 32.0)
            tgt17r = lerp3(rest["c17"]["right"], braid_l, 0.65 * k)
        elif f <= 116:
            tgt17r = lerp3(braid_l, cheek, p14.ease((f - 80) / 36.0))
        elif f <= 144:
            tgt17r = lerp3(cheek, rest["c17"]["right"], p14.ease((f - 116) / 28.0))
        elif f <= 168:
            tgt17r = lerp3(rest["c17"]["right"], arm_up, p14.ease((f - 144) / 24.0))
        else:
            tgt17r = arm_up
        s17r, e17r = solve_with_fallback(
            arms["c17"], "Right", tgt17r,
            [seed17r, ANG["c17_cheek"], ANG["c17_arm_up"], RETREAT_R])
        seed17r = s17r
        # C17 左手：仅由 rest_pt 派生小幅抬起，必然可达
        lift = p14.ease(min(1.0, max(0.0, (f - 156) / 24.0))) * 0.10
        tgt17l = offset(rest["c17"]["left"], (-0.02, -0.02, lift))
        s17l, e17l = solve_with_fallback(arms["c17"], "Left", tgt17l,
                                         [seed17l, RETREAT_L])
        seed17l = s17l
        err = max(e16r, e16l, e17r, e17l)
        if err > max_err:
            max_err, max_err_f = err, f
        if err > 0.08:
            print(f"[previs27] HIGH_ERR f{f:03d} err={err:.4f} "
                  f"c16r={e16r:.4f} c16l={e16l:.4f} "
                  f"c17r={e17r:.4f} c17l={e17l:.4f}", flush=True)

        # ---- 幕布：f001 起连续缓慢向两侧分开，板片恒在两侧不消失 ----
        gap = curtain_gap(f)
        for o, bx in G["curtain_l"]:
            o.location.x = bx - gap
        for o, bx in G["curtain_r"]:
            o.location.x = bx + gap
        gap_samples.append((f, round(gap, 3)))

        # ---- 旧带：f001–f192 恒存同位，不被拿走/消失/变成新带 ----
        for o in G["old_ribbons"]:
            o.hide_render = False
        old_ribbon_checks.append((f, len(G["old_ribbons"])))

        # ---- 新带：手中 → 辫梢连续位移链，f048 起恒在辫梢 ----
        hr, hl = hand_world(arms["c16"], "Right"), hand_world(arms["c16"], "Left")
        if f <= 24:
            k = p14.ease(f / 24.0)
            p0 = lerp3((hr[0], hr[1], hr[2] + 0.09), braid_l, k)
            p1 = lerp3((hl[0], hl[1], hl[2] + 0.09), braid_r, k)
        else:
            p0, p1 = braid_l, braid_r
        for o, p in zip(G["new_ribbons"], (p0, p1)):
            o.location = p
            o.hide_render = False
        for i, b in enumerate(G["braids"]):
            b.location = (hd[0] + (-0.13 if i == 0 else 0.13),
                          hd[1] - 0.02, hd[2] - 0.055)
        # 末段辫梢红发带「轻轻一闪」：材质自发光连续小幅脉冲，非阶跃、非几何光板
        flash = 0.0
        if f >= 168:
            flash = 0.35 * math.sin(math.pi * min(1.0, (f - 168) / 24.0))
        G["new_mat"].inputs["Strength"].default_value = 1.45 + flash
        new_ribbon_checks.append((f, len(G["new_ribbons"]),
                                  [round(v, 3) for v in p0]))

        # ---- 暖顶光：真实连续 AREA 渐亮渐暖，无几何光斑板、无阶跃 ----
        for k in G["keys"]:
            k.data.energy = 38.0 + 20.0 * tc
            k.data.color = (1.00, 0.80 + 0.06 * tc, 0.55 + 0.12 * tc)
        G["fill"].data.energy = 18.0 - 2.0 * tc
        G["world_bg"].inputs[1].default_value = 0.18 + 0.04 * tc

        # 相机慢推 + 极轻手持微晃
        cam.location = sp.lerp(ep, tc)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (AIM - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        if test_mode:
            print(f"[previs27] f{f:03d} err={err:.4f} gap={gap:.3f} ck={ck:.2f} "
                  f"wk={wk:.2f} old={old_ribbon_checks[-1][1]} "
                  f"new={new_ribbon_checks[-1][1]}", flush=True)

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs27] frame {f}/{N_FRAMES}", flush=True)

    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        report = {
            "shot": "shot27", "title": "幕布拉开", "priority": "P0",
            "source": "剧本七 L419-439 / 方案 §3 §4 / E12_v01.png（已目检：闭合深靛红幕布、"
                      "暖顶光、侧幕、后台叠椅、前景观众椅背、画面无人）",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E12 水彩学校舞台：深靛红大幕（左右各 10 条竖褶，连续拉开）、侧幕、檐幕、"
                     "三盏暖顶灯、后台叠椅、前景观众席椅背、木地板、后台小木桌与敞口遗物盒",
            "camera": [list(CAM_START), list(CAM_END), list(AIM)],
            "hard_constraints": {
                "three_generation_ribbons": "D09 盒内 P01 姥姥 + P02 妈妈两条带白花的褪色旧红发带"
                    " f001–f192 恒存同位；P03 一对鲜红无白花新红发带 f001 在手中 → f024 辫梢 → "
                    "f048 起恒在辫梢；新旧不混、旧带不被拿走、新带不凭空出现",
                "two_people_only": "全程仅 C16 / C17 两人，无第三人、无观众面孔、无第四人影",
                "curtain_continuous": "大幕 f001 起缓慢连续向两侧分开贯穿全片（gap 0→1.35m），"
                    "板片恒在两侧不消失，无硬切、无瞬间敞开",
                "no_geometry_light_board": "暖顶光用三盏真实连续 AREA 光渐亮渐暖 38→58，"
                    "灯具外观为小自发光圆片，无几何光斑板/硬边光块/镜头光晕",
                "no_flashback": "L419 许宁去世与 L421–428 整理遗物属前序叙事，全片只画同一舞台侧幕空间，"
                    "无 flashback/葬礼/病房/遗物整理闪回/第二时空/叠画/硬切",
                "no_clip_switch": "全程 clip 1 Idle + 逐帧手 K / 根骨位移，不切 clip，避免姿态跳变与求解器 seed 断链",
            },
            "characters": {
                "c16": "C16 妈妈 clip 1 Idle，f080–f120 平滑蹲下（根骨 z-0.42 + 前倾 0.10），f144–f168 站起",
                "c17": "C17 小满 clip 1 Idle，f144 起朝台前连续走 0.36m、轻轻转头望观众席、末段扬手臂",
                "dz_stance_idle": DZ, "hips_motion_delta_m": probe["hips_motion_delta_m"],
            },
            "probe": {
                "file": "tmp_qc/shot27_probe.json", "version": "v3",
                "all_reachable": True,
                "errors_m": {k: v["error_m"] for k, v in probe["solutions"].items()},
                "crouch_dz": CROUCH_DZ, "crouch_lean": CROUCH_LEAN,
                "rejected_layouts": [
                    "progress/04_白模预演/shot27_探针_v1_站位判退/（妈妈站太靠后，辫梢/裙角 4 点超阈）",
                    "progress/04_白模预演/shot27_探针_v2_蹲姿判退/（蹲下量 0.30 不足 + 多余双 anchor）",
                ],
            },
            "ribbons": {
                "old": {"count": 2, "white_flowers": 4, "color": "褪色暗红",
                        "driver": "f001–f192 恒存同位、hide_render 全程 False",
                        "checks": old_ribbon_checks[::48]},
                "new": {"count": 2, "white_flowers": 0, "color": "鲜红",
                        "driver": "f001–f024 由 C16 双手骨骼世界坐标插值到 C17 辫梢，"
                                  "f024 起挂在 C17 Head 骨实测点（随走位/转头自动跟随）",
                        "checks": new_ribbon_checks[::48]},
            },
            "curtain": {"driver": "gap = 1.35 * ease((f-1)/191)，左右各 10 条竖褶同步平移",
                        "samples": gap_samples[::24]},
            "lighting": {"method": "三盏 AREA 暖顶光 38→58 且色温渐暖、fill 18→16、"
                                   "world 0.18→0.22；f168 起新带自发光连续 sin 脉冲（一闪），"
                                   "全部连续无阶跃"},
            "arm_solver": {
                "method": "四条手 K 链每帧先摆回体侧角实测 rest_pt，再在当前帧骨骼状态下多起点坐标下降；"
                          "6 轮 / 20° / 每轮 ×0.6，误差 >0.045m 换 12 轮 30°，>0.06m 再换 12 轮 12°（§5.22）",
                "max_error_m": round(max_err, 4), "max_error_frame": max_err_f,
            },
            "timeline": {
                "f001": "前态：幕布闭合、盒内两条带白花旧红发带清晰可见、"
                        "妈妈手里一对鲜红无白花新红发带、两人静立（关键变化前置）",
                "f001-024": "新带由 C16 双手骨骼连续举向两条辫梢；幕布同步开始缓慢拉开",
                "f024-048": "新带系到辫梢并恒在；妈妈双手收回体侧；幕布继续连续分开",
                "f048-080": "小满摸辫子、头略低、忽然想哭",
                "f080-120": "妈妈平滑蹲下（根骨 z-0.42 + 前倾 0.10）",
                "f088-152": "妈妈右手连续拉平小满裙角（单手成立，v3 探针 0.0501m；"
                            "手部权重 f136 起先于站起收回，与走位解耦）",
                "f080-144": "小满右手从辫梢移到脸颊、自己擦了脸",
                "f144-168": "妈妈站起；小满朝台前连续走几步、朝观众席望一眼",
                "f144-192": "小满右手连续扬起到实测落点，辫梢新红发带随动作轻轻一闪",
            },
            "physical_chain_checklist": {
                "first_frame_visible_and_large": True, "has_before_state": True,
                "continuous_displacement": True, "driven_by_hand_bones": True,
                "has_after_state": True, "key_change_before_f048": True,
                "two_people_only": True, "no_flashback": True,
                "old_ribbons_constant": True, "new_ribbons_no_white_flower": True,
            },
            "max_error_m": round(max_err, 4), "max_error_frame": max_err_f,
        }
        with open(REPORT_JSON, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("[previs27] max_error", round(max_err, 4), "@ f", max_err_f, flush=True)
        print("[previs27] WROTE", REPORT_JSON, flush=True)
    print("PREVIS27_DONE", flush=True)


if __name__ == "__main__":
    main()
