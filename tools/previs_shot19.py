# -*- coding: utf-8 -*-
"""白模预演：shot19「报纸后面」（剧本六 L315-319，方案 §4）。

场景 E09 折叠餐桌白天版（与 shot15/16/17 同族）：桌、两把木椅、后墙窗与窗帘、
暖壶、碗、矮柜上的盖锅。周远 C18 坐右椅，许宁 C06b 从桌子左后方缓步走近。

核心动作链（HANDOFF §5.19，必须靠白模给出，prompt 补不出来）：
  前态   周远举着完全展开的报纸挡住大半张脸，双手握左右两缘，半天没应
  过程A  许宁走过去站到椅旁，右手渐伸向报纸上沿左角并贴住
  过程B  她把报纸上沿往下按一按：报纸在周远双手里**整体渐降**，双手同步跟着降
  过程C  周远缓缓抬头，脸从报纸上方露出来；许宁的手抽回身侧，带着一点好笑
  后态   报纸仍完全展开、仍在周远双手里、只是低到全脸可见；两人安静站着坐着

变化三态全部 ease 渐变，无硬切。报纸全程不落桌、不消失、不换形、不脱手。

预演经历两轮判退：v1 报纸举太高只挡额头、许宁手臂角度插值回摆；v2 求解未收敛
导致手没收回、报纸横线像栅栏。v3（本文件）过审，两轮测试帧、坐标日志与判定书
留在 progress/04_白模预演/shot19_测试帧_v1/ 与 _v2/。

关键设计：**报纸不是独立插值的道具，而是由周远双手骨骼的当帧世界坐标驱动**。
左右手角度在 tmp_qc/probe_shot19_final.py 实测的两个端点（举高 / 降下）之间插值，
每帧读回两手坐标，把报纸 root 放到两点中点、宽度覆盖两点、按连线倾斜。
这样「手握报纸」零脱节，且报纸下降本身就是手臂运动的结果，物理链完整可辨。
许宁右手贴报纸上沿左角的角度也来自同一份实测，按同一条 k_down 时间轴插值。

已知坑（HANDOFF §5）已规避：
  §5.14 按 clip 序号名称取 action、脚高用站姿 Idle 测
  §5.15 add_box 的 dimensions 本质是 scale；报纸用 Empty 作 root，子件局部坐标
  §5.16 build_room() 末尾补 view_layer.update()
  §5.17 椅背用镂空栏杆，矮柜用细杆，不做正对相机的实心大方板
  §5.19 关键道具必须有完整物理链；报纸全程在双手里
  §5.20 不动 Spine，避免上身旋转传导到手臂让实测角度失准

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot19.py
  set PREVIS_RANGE=1-64 && blender.exe --background --python tools/previs_shot19.py
  blender.exe --background --python tools/previs_shot19.py
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
FRAMES_DIR = os.path.join(OUT_DIR, "frames19")
POSES_JSON = os.path.join(ROOT, "tmp_qc", "shot19_final_poses.json")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720
CAM_LENS = 36
CAM_START = (0.32, -2.28, 1.44)
CAM_END = (0.34, -2.10, 1.41)
AIM = Vector((0.55, 1.60, 1.12))

TABLE_CENTER = (0.40, 1.05)
CHAIR_ZHOU = (0.85, 1.72)
CHAIR_SPARE = (1.85, 1.15)     # 第二把椅放桌子右侧，不挡走位
XU_START = (-0.70, 2.05)
XU_END = (0.35, 1.68)
YAW_ZHOU = math.radians(-25)
YAW_XU = math.radians(70)
WALL_Y = 3.2
WIN_X0, WIN_X1 = -2.7, -1.3
WIN_Z0, WIN_Z1 = 1.15, 2.35

# 报纸几何：宽度覆盖双手且让许宁够得到左上角，高度保证举高时挡脸、降下时露脸
PAPER_W, PAPER_H, PAPER_T = 0.46, 0.22, 0.010

BONES_ZHOU = ("mixamorig:Head", "mixamorig:Neck", "mixamorig:Spine", "mixamorig:Spine1",
              "mixamorig:RightArm", "mixamorig:RightForeArm", "mixamorig:RightHand",
              "mixamorig:LeftArm", "mixamorig:LeftForeArm", "mixamorig:LeftHand")
BONES_XU = ("mixamorig:Head", "mixamorig:Neck", "mixamorig:Spine", "mixamorig:Spine1",
            "mixamorig:RightArm", "mixamorig:RightForeArm", "mixamorig:RightHand",
            "mixamorig:LeftArm", "mixamorig:LeftForeArm", "mixamorig:LeftHand")


def mat(key, shade, emission=None):
    return p14.mat("s19_" + key, shade, emission)


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
    """E09 白天版：折叠餐桌 + 两把木椅 + 后墙窗 + 窗帘 + 暖壶/碗/盖锅。"""
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
    p14.add_box("win_f_h", (cx, WALL_Y - 0.03, WIN_Z1),
                (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    p14.add_box("win_f_b", (cx, WALL_Y - 0.03, WIN_Z0),
                (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    p14.add_box("win_f_m", (cx, WALL_Y - 0.03, cz), (0.05, 0.08, WIN_Z1 - WIN_Z0), frame)
    p14.add_box("daylight", (cx, WALL_Y + 3.0, 1.8), (7.0, 0.1, 3.6),
                mat("daylight", 0.72, emission=(0.60, 0.64, 0.70, 1.0)))
    p14.add_box("windowsill", (cx, WALL_Y - 0.22, WIN_Z0 - 0.03),
                (WIN_X1 - WIN_X0 + 0.24, 0.42, 0.05), mat("sill", 0.68))
    p14.add_box("curtain", (WIN_X0 - 0.12, WALL_Y - 0.12, 1.75),
                (0.34, 0.05, 1.20), mat("curtain", 0.82))

    # 折叠餐桌（与 shot15/16/17 同坐标同尺寸）
    tx, ty = TABLE_CENTER
    p14.add_box("table_top", (tx, ty, 0.74), (1.55, 1.0, 0.05), mat("table", 0.62))
    p14.add_box("tablecloth", (tx, ty, 0.769), (1.62, 1.06, 0.012), mat("cloth", 0.88))
    for dx in (-0.65, 0.65):
        p14.add_box(f"table_leg_{dx}", (tx + dx, ty, 0.37), (0.05, 0.85, 0.72),
                    mat("leg", 0.45))
    for i, wx in enumerate((tx - 0.38, tx + 0.30)):
        p14.add_cyl(f"bowl_{i}", (wx, ty + 0.12, 0.815), 0.085, 0.055,
                    mat("bowl", 0.86))
    p14.add_cyl("thermos", (tx + 0.55, ty - 0.30, 0.865), 0.055, 0.18,
                mat("thermos", 0.50))

    # 矮柜：细杆通透结构，不做实心大方板（§5.17）；盖锅在柜面上
    sx, sy = 1.55, 2.15
    p14.add_box("sideboard_top", (sx, sy, 0.66), (0.80, 0.42, 0.04), mat("sideboard", 0.58))
    for dx in (-0.36, 0.36):
        for dy in (-0.17, 0.17):
            p14.add_box(f"sideboard_leg_{dx}_{dy}", (sx + dx, sy + dy, 0.33),
                        (0.035, 0.035, 0.66), mat("sideboard_leg", 0.44))
    p14.add_box("sideboard_rail", (sx, sy + 0.19, 0.22), (0.74, 0.025, 0.025),
                mat("sideboard_leg", 0.44))
    p14.add_cyl("pot", (sx - 0.12, sy, 0.735), 0.130, 0.110, mat("pot", 0.34))
    p14.add_cyl("pot_lid", (sx - 0.12, sy, 0.798), 0.140, 0.018, mat("pot_lid", 0.40))

    add_chair("chair_zhou", *CHAIR_ZHOU)
    add_chair("chair_spare", *CHAIR_SPARE, shade=0.52)

    # §5.16：强制刷新依赖图，最后创建的几何体 dimensions 才会生效
    bpy.context.view_layer.update()


def build_paper():
    """报纸：Empty 作 root，所有部件挂局部坐标，每帧只驱动 root。

    上沿深色细条让「按下上沿」在白模里可辨；几道文字行与中缝让「展开的报纸」
    一眼能认出来，且全程尺寸恒定、不换形、不消失。
    """
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    root = bpy.context.active_object
    root.name = "paper_root"

    paper_mat = mat("paper", 0.90)
    # v2：加深上沿与文字行，让白模里「展开的报纸」和「被按下的上沿」更可辨
    edge_mat = mat("paper_edge", 0.10)
    ink_mat = mat("paper_ink", 0.30)
    seam_mat = mat("paper_seam", 0.24)

    parts = []

    def piece(name, loc, dims, m):
        o = p14.add_box(name, loc, dims, m)
        o.parent = root
        parts.append(o)
        return o

    piece("paper_sheet", (0, 0, 0), (PAPER_W, PAPER_T, PAPER_H), paper_mat)
    piece("paper_top_edge", (0, -0.002, PAPER_H / 2), (PAPER_W, PAPER_T + 0.004, 0.016), edge_mat)
    piece("paper_bottom_edge", (0, -0.002, -PAPER_H / 2), (PAPER_W, PAPER_T + 0.004, 0.008), ink_mat)
    # v3：五道贯穿的横线会被读成栅栏/百叶窗；改成分两栏的长短不一的短行 +
    # 一条粗标题行，保留中缝，白模里更像一份摊开的报纸版面
    piece("paper_headline", (0, -0.007, 0.082),
          (PAPER_W - 0.05, 0.004, 0.012), edge_mat)
    for ci, x0 in enumerate((-0.105, 0.105)):
        for r in range(6):
            z = 0.055 - r * 0.022
            w = 0.145 if r % 3 else 0.105
            piece(f"paper_text_{ci}_{r}", (x0, -0.007, z),
                  (w, 0.004, 0.0045), ink_mat)
    piece("paper_fold", (0, -0.007, 0), (0.006, 0.004, PAPER_H - 0.02), seam_mat)
    bpy.context.view_layer.update()
    return root


def add_lighting():
    world = bpy.data.worlds.new("previz_world19")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.26, 0.27, 0.30, 1.0)
            n.inputs[1].default_value = 0.86
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
    target = f"animation_{n}"
    for a in acts:
        if a.name.split(".")[0] == target:
            return a
    raise RuntimeError(f"找不到 {target}，现有 {[a.name for a in acts]}")


def apply_arm(arm, side, ax, ay, az, fb):
    """4 自由度手 K：绕 Y / X / Z 的上臂旋转 + 绕 Y 的前臂旋转。"""
    p14.rotate_ops(arm, f"mixamorig:{side}Arm", [
        ((0, 1, 0), ay), ((1, 0, 0), ax), ((0, 0, 1), az),
    ])
    p14.rotate_ops(arm, f"mixamorig:{side}ForeArm", [((0, 1, 0), fb)])


def hand_world(arm, side):
    bpy.context.view_layer.update()
    w = arm.matrix_world @ arm.pose.bones[f"mixamorig:{side}Hand"].matrix.translation
    return (w.x, w.y, w.z)


def lerp_ang(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(4))


def lerp3(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


def solve_xu_right(arm, target, seed, anchor, iters=4, step=20.0):
    """许宁右手每帧坐标下降贴目标轨迹，不再插值端点角度。

    v1 把 retreat→press_up 的四元角度直接线性插值，f072 手臂先甩到身前平伸
    再绕回来（角度空间不是笛卡尔空间，插值会走大弧线），目检判退。
    v2 改成三维目标点插值 + 每帧只从上一帧解出发微调，但 3 轮收敛不足，
    结尾手仍停在报纸旁（误差 0.11-0.20m）。
    v3 加分段 anchor：每帧同时从「上一帧解」和「本段实测角度」出发，
    取误差更小的分支（HANDOFF §5.20 shot18 的做法）。
    """
    best = None
    for start in (seed, anchor):
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
                apply_arm(arm, "Right", *c)
                scored.append((math.dist(hand_world(arm, "Right"), target), c))
            _, cur = min(scored, key=lambda s: s[0])
            s *= 0.6
        apply_arm(arm, "Right", *cur)
        e = math.dist(hand_world(arm, "Right"), target)
        if best is None or e < best[0]:
            best = (e, tuple(cur))
    apply_arm(arm, "Right", *best[1])
    return best[1], best[0]


def head_pose(arm, down, turn):
    """只动 Head/Neck，不动 Spine：避免上身旋转传导到手臂让实测角度失准（§5.20）。"""
    p14.rotate_ops(arm, "mixamorig:Head", [
        ((1, 0, 0), down), ((0, 0, 1), turn * 0.55),
    ])
    p14.rotate_world(arm, "mixamorig:Neck", (0, 0, 1), turn * 0.6)


def k_paper_down(f):
    """报纸下降进度：f101 开始、f152 到底，段内 ease。"""
    if f <= 100:
        return 0.0
    if f <= 152:
        return p14.ease((f - 101) / 51.0)
    return 1.0


PRESS_LOCAL = Vector((-PAPER_W / 2 + 0.035, -0.012, PAPER_H / 2 - 0.015))


def press_target(root):
    """报纸上沿偏左处的当帧世界坐标；许宁的手贴这里，随报纸一起下降。"""
    bpy.context.view_layer.update()
    w = root.matrix_world @ PRESS_LOCAL
    return (w.x, w.y, w.z)


def xu_hand_target(f, retreat_pt, press_pt):
    """身侧 → 伸向上沿 → 贴着上沿随报纸下降 → 抽回身侧，全部三维插值。"""
    if f <= 56:
        return retreat_pt
    if f <= 100:
        return lerp3(retreat_pt, press_pt, p14.ease((f - 57) / 43.0))
    if f <= 152:
        return press_pt
    if f <= 176:
        return lerp3(press_pt, retreat_pt, p14.ease((f - 153) / 23.0))
    return retreat_pt


def place_paper(root, left_pt, right_pt):
    """把报纸放到周远双手之间。LeftHand 在 x 大侧、RightHand 在 x 小侧。

    v2：报纸中心比双手低 0.09m，也就是手握在报纸**上沿**而不是纸面中央。
    v1 让中心贴双手均值，结果报纸举在额头上方只挡住发际、整张脸全露（目检判退）。
    """
    cx = (left_pt[0] + right_pt[0]) / 2
    cy = (left_pt[1] + right_pt[1]) / 2
    cz = (left_pt[2] + right_pt[2]) / 2 - 0.09
    dx, dy = left_pt[0] - right_pt[0], left_pt[1] - right_pt[1]
    yaw = math.atan2(dy, dx)
    root.location = (cx, cy, cz)
    root.rotation_euler = (math.radians(-9), 0, yaw)
    bpy.context.view_layer.update()
    return (cx, cy, cz)


def main():
    global ANG
    with open(POSES_JSON, encoding="utf-8") as fh:
        poses = json.load(fh)
    ANG = {k: tuple(v["angles"]) for k, v in poses["solutions"].items()}
    # 许宁「手在身侧」的相对站位偏移（探针在站定点实测的手世界坐标减去站位），
    # 走位时目标点跟着身体一起平移，不会把手留在原地
    rh = poses["solutions"]["xu_retreat"]["hand_world"]
    st = poses["stand"]["xu"]
    retreat_offset = (rh[0] - st[0], rh[1] - st[1], rh[2] - poses["dz"]["xu"])
    print("[previs19] arm anchors", {k: [round(x, 1) for x in v] for k, v in ANG.items()},
          flush=True)
    print("[previs19] retreat_offset", [round(v, 3) for v in retreat_offset], flush=True)

    os.makedirs(FRAMES_DIR, exist_ok=True)
    p14.clean_scene()
    build_room()
    paper_root = build_paper()
    add_lighting()

    zhou, z_acts, _ = p14.import_glb(os.path.join(MODELS, "C18", "tex_mesh_animated.glb"))
    xu, x_acts, _ = p14.import_glb(os.path.join(MODELS, "C06b", "tex_mesh_animated.glb"))
    print("[previs19] zhou_acts", len(z_acts), [a.name for a in z_acts], flush=True)
    print("[previs19] xu_acts", len(x_acts), [a.name for a in x_acts], flush=True)
    if len(z_acts) < 5 or len(x_acts) < 5:
        raise RuntimeError("C18 / C06b 都应有 10 个动作 clip")

    z_sit = act_by_clip(z_acts, 4)      # Sitting_Idle_Loop
    z_idle = act_by_clip(z_acts, 1)     # 站姿 Idle，只用于测脚高
    x_idle = act_by_clip(x_acts, 1)
    for a in (z_sit, z_idle, x_idle):
        p14.make_loop(a)
    removed = p14.strip_channels([z_sit], BONES_ZHOU)
    removed += p14.strip_channels([x_idle], BONES_XU)
    print("[previs19] stripped", len(removed), "channels", flush=True)

    z_ad, x_ad = zhou.animation_data, xu.animation_data
    # 脚高校正必须拿站姿 Idle 测（§5.14）
    p14.set_loop(z_ad, z_idle, {"key": None}, "idle_probe")
    p14.set_loop(x_ad, x_idle, {"key": None}, "idle_probe")
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    dz_z = -p14.feet_z(zhou) + 0.02
    dz_x = -p14.feet_z(xu) + 0.02
    print(f"[previs19] dz zhou={dz_z:.3f} xu={dz_x:.3f}", flush=True)

    p14.set_loop(z_ad, z_sit, {"key": None}, "sit")
    p14.set_loop(x_ad, x_idle, {"key": None}, "idle")
    for a in (zhou, xu):
        a.rotation_mode = "XYZ"

    matte = p14.make_matte("char_matte19", 0.82)
    for o in [o for o in scene.objects if o.type == "MESH"]:
        mnames = [m.name for m in o.data.materials] if o.data.materials else []
        if any(n.startswith("s19_") for n in mnames):
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

    cam_data = bpy.data.cameras.new("previs_cam19")
    cam_data.type, cam_data.lens = "PERSP", CAM_LENS
    cam = bpy.data.objects.new("previs_cam19", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    sp, ep = Vector(CAM_START), Vector(CAM_END)

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    if test_mode:
        frames_iter = [1, 24, 48, 72, 88, 100, 112, 128, 144, 160, 176, 192]
    elif os.environ.get("PREVIS_RANGE"):
        a, b = os.environ["PREVIS_RANGE"].split("-")
        frames_iter = range(int(a), int(b) + 1)
    else:
        frames_iter = range(1, N_FRAMES + 1)

    paper_centers = []
    xu_seed = tuple(ANG["xu_retreat"])
    max_xu_err, max_xu_err_f = 0.0, 0
    for f in frames_iter:
        t = p14.ease((f - 1) / (N_FRAMES - 1))
        kd = k_paper_down(f)

        # 许宁走近：f1-80 缓行平移、ease 渐停；f81 起站定不动
        k_walk = p14.ease((f - 1) / 79.0) if f <= 80 else 1.0
        xu_xy = (XU_START[0] + (XU_END[0] - XU_START[0]) * k_walk,
                 XU_START[1] + (XU_END[1] - XU_START[1]) * k_walk)
        xu.location = (*xu_xy, dz_x)
        xu.rotation_euler = (0, 0, YAW_XU)
        zhou.location = (*CHAIR_ZHOU, dz_z)
        zhou.rotation_euler = (0, 0, YAW_ZHOU)
        scene.frame_set(f)

        # 周远：坐姿、头低看报 → 缓缓抬头看她；Spine 不动
        zhou_down = 6.0 - 14.0 * (p14.ease((f - 145) / 40.0) if f > 145 else 0.0)
        zhou_turn = -6.0 + 4.0 * (p14.ease((f - 145) / 40.0) if f > 145 else 0.0)
        head_pose(zhou, zhou_down, zhou_turn)

        # 双手角度按实测端点插值；报纸随后由双手的当帧坐标驱动
        apply_arm(zhou, "Left", *lerp_ang(ANG["zhou_left_up"], ANG["zhou_left_down"], kd))
        apply_arm(zhou, "Right", *lerp_ang(ANG["zhou_right_up"], ANG["zhou_right_down"], kd))
        lp = hand_world(zhou, "Left")
        rp = hand_world(zhou, "Right")
        pc = place_paper(paper_root, lp, rp)
        paper_centers.append((f, [round(v, 3) for v in pc]))

        # 许宁：头微侧看他、结尾带一点好笑的轻点头；右臂按同一条 kd 时间轴
        xu_turn = -8.0 if f <= 96 else -8.0 + 4.0 * p14.ease((f - 97) / 60.0)
        xu_down = 2.0
        if 177 <= f <= 192:
            xu_down += 1.6 * math.sin((f - 177) / 6.0)
        head_pose(xu, xu_down, xu_turn)
        # v2：目标轨迹在三维空间插值，每帧求解贴手，避免 v1 的角度弧线回摆
        press_pt = press_target(paper_root)
        retreat_pt = (xu_xy[0] + retreat_offset[0],
                      xu_xy[1] + retreat_offset[1],
                      dz_x + retreat_offset[2])
        tgt = xu_hand_target(f, retreat_pt, press_pt)
        if f <= 100:
            anchor = ANG["xu_press_up"]
        elif f <= 152:
            anchor = ANG["xu_press_down"]
        else:
            anchor = ANG["xu_retreat"]
        if f <= 56 or f >= 177:
            # 首尾锁回探针实测的「手在身侧」角度，终态确定，不会被求解误差留在报纸旁
            apply_arm(xu, "Right", *ANG["xu_retreat"])
            xu_seed, xu_err = tuple(ANG["xu_retreat"]), 0.0
        else:
            solved, xu_err = solve_xu_right(xu, tgt, xu_seed, anchor)
            if f >= 153:
                # 抽回段把求解结果渐混到实测收手角度，24 帧内手确实回到身侧
                k_back = p14.ease((f - 153) / 23.0)
                solved = lerp_ang(solved, ANG["xu_retreat"], k_back)
                apply_arm(xu, "Right", *solved)
            xu_seed = solved
        if xu_err > max_xu_err:
            max_xu_err, max_xu_err_f = xu_err, f

        cam.location = sp.lerp(ep, t)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (AIM - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()

        if test_mode:
            xh = hand_world(xu, "Right")
            print(f"[previs19] f{f:03d} kd={kd:.2f} walk={k_walk:.2f} "
                  f"paper=({pc[0]:.3f},{pc[1]:.3f},{pc[2]:.3f}) "
                  f"zhouL=({lp[0]:.3f},{lp[1]:.3f},{lp[2]:.3f}) "
                  f"zhouR=({rp[0]:.3f},{rp[1]:.3f},{rp[2]:.3f}) "
                  f"press=({press_pt[0]:.3f},{press_pt[1]:.3f},{press_pt[2]:.3f}) "
                  f"xuR=({xh[0]:.3f},{xh[1]:.3f},{xh[2]:.3f}) err={xu_err:.4f}", flush=True)

        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs19] frame {f}/{N_FRAMES}", flush=True)

    rng = os.environ.get("PREVIS_RANGE", "")
    if not test_mode and (not rng or rng.endswith("-192")):
        zs = [c[1][2] for c in paper_centers]
        report = {
            "shot": "shot19", "title": "报纸后面",
            "source": "剧本六 L315-319 / 方案 §4 / E09_v01.png",
            "frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
            "scene": "E09 折叠餐桌白天版：折叠餐桌+桌布、两把镂空木椅、后墙窗与窗帘、暖壶、两只碗、右侧矮柜上的盖锅",
            "camera": [list(CAM_START), list(CAM_END), list(AIM)],
            "stand": {
                "zhou": list(CHAIR_ZHOU), "yaw_zhou_deg": -25, "feet_dz": round(dz_z, 3),
                "xu_start": list(XU_START), "xu_end": list(XU_END), "yaw_xu_deg": 70,
                "feet_dz_xu": round(dz_x, 3),
                "walk": "f1-80 缓行平移 ease 渐停、f81 起站定；全程 Idle_Loop，不做 Walk→Idle 硬切",
            },
            "paper": {
                "width": PAPER_W, "height": PAPER_H, "thickness": PAPER_T,
                "driver": "由周远双手骨骼当帧世界坐标驱动：root 放在两手中点再降 0.09m（手握上沿）、按两手连线绕 z 倾斜、绕 x 后仰 9°；子件（纸面/上沿深色条/下沿/粗标题行/两栏共 12 条长短不一的短行/中缝）全挂 root 局部坐标",
                "center_offset_from_hands_m": -0.09,
                "why": "HANDOFF §5.19：关键道具必须有完整物理链。独立插值会让 H3 读成『报纸自己飘下来』；由双手驱动则手与报纸零脱节，报纸下降本身就是手臂运动的结果",
                "center_z_first": zs[0] if zs else None,
                "center_z_last": zs[-1] if zs else None,
                "center_z_drop_m": round(zs[0] - zs[-1], 4) if zs else None,
                "shape_constant": True,
                "in_hands_all_frames": True,
            },
            "arm_solver": {
                "method": "周远双手：4 自由度 (ax,ay,az,fb) 端点实测 + 每帧 ease 插值（本镜 Spine 保持不变，实测角度不失准）；许宁右手：每帧坐标下降贴三维目标轨迹，双起点（上一帧解 + 本段实测 anchor）取误差较小分支、4 轮 / 初始步长 20° / 每轮 ×0.6；f1-56 与 f177-192 锁回实测收手角度、f153-176 把求解结果 ease 渐混到收手角度",
                "probes": ["tmp_qc/probe_shot19_bones.py", "tmp_qc/probe_shot19_layout.py",
                           "tmp_qc/probe_shot19_final.py", "tmp_qc/shot19_layout_envelope.json",
                           "tmp_qc/shot19_final_poses.json"],
                "probe_v1_finding": "首版把报纸放在 (0.85,1.40,1.42)，超出坐姿双臂可达范围（误差 0.32-0.52m）；实测脸中心 y≈1.91/z≈1.06 后把报纸移到脸前 y≈1.77，并把许宁移到同排转身朝 +x",
                "xu_right_max_error_m": round(max_xu_err, 4),
                "xu_right_max_error_frame": max_xu_err_f,
                "anchors": {k: [round(x, 1) for x in v] for k, v in ANG.items()},
            },
            "previs_v2_rework": {
                "v1_test_frames": "progress/04_白模预演/shot19_测试帧_v1/",
                "v1_verdict": "rejected",
                "issues": [
                    "报纸中心贴双手均值，实际举在额头上方只挡住发际，整张脸全露（f001 原分辨率确认）",
                    "许宁右手用端点角度线性插值，f072 手臂先甩到身前平伸再绕回，角度空间插值走了大弧线",
                    "报纸上沿与文字行对比度偏低，缩略图里接近一块灰板",
                ],
                "fixes": [
                    "报纸中心比双手低 0.09m，改成手握报纸上沿；UP 覆盖 1.00~1.22 正好挡脸、DOWN 覆盖 0.77~0.99 全脸露出",
                    "许宁右手改为三维目标点插值 + 每帧坐标下降求解，手走直线、贴着上沿随报纸同步下降",
                    "上沿加深到 0.10、文字行 0.30、中缝 0.24",
                ],
            },
            "previs_v3_rework": {
                "v2_test_frames": "progress/04_白模预演/shot19_测试帧_v2/",
                "v2_verdict": "rejected（局部残留）",
                "v2_issues": [
                    "许宁右手求解器单起点 3 轮收敛不足，误差 0.11-0.20m，f192 原分辨率里手仍斜搭在报纸左下角，未回到身侧",
                    "五道贯穿横线 + 中缝竖线被读成栅栏/百叶窗，不像报纸版面",
                ],
                "v3_fixes": [
                    "求解器改双起点（上一帧解 + 分段 anchor）、4 轮 / step 20°，f100 误差 0.19→0.066、f128 0.058→0.033",
                    "f1-56 与 f177-192 直接锁回探针实测收手角度，f153-176 把求解结果 ease 渐混过去；f176 手回到 (0.372,1.482,0.835)、f192 (0.383,1.481,0.834)",
                    "文字行改成两栏 12 条长短不一的短行 + 一条粗标题行，保留中缝",
                ],
                "v3_test_frames": "tmp_qc/shot19_test_contact_v3.jpg + assets/previs/frames19/ 测试帧",
                "v3_verdict": "pass（进入 192 帧全渲）",
            },
            "review_nonblocking": [
                "周远左前臂在报纸降下后横过纸面上缘，是双手握报纸两侧的自然姿态，不遮挡脸也不改变道具运动链",
                "许宁走近用 Idle_Loop + 缓行平移、未用 Walk clip（避免 Walk→Idle 硬切），下肢保持站立姿态；位移仅 1.12m / 80 帧且 ease 渐停，参考视频只需给出『走近并站定』拓扑",
                "桌子遮住周远坐姿的小腿，但他始终坐在同一椅面、脚高校正已用站姿 Idle 实测；许宁 f001 全身入镜、脚贴地可查",
            ],
            "timeline": {
                "f1-56": "前态：周远坐椅举着完全展开的报纸挡住大半张脸、双手握左右两缘；许宁从桌子左后方缓步走近",
                "f57-100": "许宁走到椅旁站定，右手渐伸向报纸上沿左角并贴住，报纸高度不变",
                "f101-152": "核心动作：她把上沿往下按，报纸在周远双手里整体渐降，双手同步下降",
                "f145-192": "周远缓缓抬头，脸从报纸上方完整露出",
                "f153-176": "许宁的手抽回自己身侧",
                "f177-192": "后态：报纸仍展开、仍在双手里、只是低到全脸可见；她带一点好笑忘了要说什么，镜头微推",
            },
            "three_state": {
                "newspaper": "举高挡脸（双手上举、纸面完整）→ 过程 ease 渐降、双手与纸面同步 → 降到胸口高度全脸露出；全程不落桌、不消失、不换形、不脱手",
                "xu_right_hand": "身侧 → 渐伸向上沿左角 → 贴着上沿随报纸一起下降 → 渐抽回身侧",
                "zhou_head": "低头对着报纸 → 缓缓抬起 → 看向她",
                "xu_walk": "左后方缓行 → ease 渐停 → 站定在椅旁；无硬切 clip",
            },
            "characters": {
                "zhou": "C18 周远·老年 ten-clip / clip 4 = Sitting_Idle_Loop（头颈与双臂通道剥出后手 K）",
                "xu": "C06b 许宁·中老年居家 ten-clip / clip 1 = Idle_Loop（头颈与双臂通道剥出后手 K）",
            },
            "hard_constraints": "脚贴地；周远始终坐在同一把椅子、许宁走近渐停；报纸全程在双手里且不落桌不消失不换形；桌椅窗与桌上道具不移动；无第三人；段间全 ease 渐变；椅背与矮柜用镂空细杆不做实心大方板",
            "paper_centers_sample": paper_centers[::24],
        }
        with open(os.path.join(OUT_DIR, "previs19_report.json"), "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS19_DONE", flush=True)


if __name__ == "__main__":
    main()
