# -*- coding: utf-8 -*-
"""白模预演：shot14「厨房的和好」（剧本五 L251-267）。

场景：E10 出租屋厨房角（与 shot13 同一套朝北出租屋的厨房侧）。
布局：后墙（y=3.2）水槽台面 x -2.5..0.5，窗在水槽上方；
餐桌在台面右侧 (1.15,1.45)，远椅（面向 -y）+ 近椅（面向 +y）。

时间轴（192f / 8s），变化三态：
- f1-35    周远水槽前洗碗（手动前倾姿态+前臂小幅度搓洗）；许宁右侧入画
           走到他右侧身旁站定（before：只有水声）
- f36-60   许宁开口道歉（侧头向周远、右手微抬）；周远搓洗渐停、
           手臂保持在水槽上方（变化：搓洗幅度→0，姿态冻结不收回）
- f61-90   周远前臂上抬拧水龙头，f85 水流消失
           （变化前：水在流 f1-84；过程：抬手拧龙头 f61-84；
             变化后：水停 f85+），他侧头面向她
- f91-105  周远手臂从关水姿态连续放回到体侧（无突变），侧头渐入
- f106-125 两人静立，许宁说爸爸的事（低头→抬头），周远凝视
- f126-148 周远沿走廊走到远椅正后方 (1.15,2.30)（许宁 f138 才起步，
           两人间距保持 0.4m 以上，镜头里不重叠；走路朝向取路径切线）
- f138-152 许宁走位到远椅前 (1.15,1.70) 站定，边走边转身面向椅子
- f149-158 周远把远椅朝 -y 拉出 0.12m，f153-158 抬手示意她坐
- f165     许宁入座（Sitting_Enter NLA 1.8x，f187 坐定，
           f188+ 切 Sitting_Idle_Loop）
- f164-175 周远沿桌西侧绕到近椅前（她入座时他正从椅后出发，不相贴）
- f176     周远入座（Sitting_Enter NLA 2.5x，f190 坐定，
           f191+ 切 Sitting_Idle_Loop）——结束两人隔桌对坐（after）

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot14.py
  blender.exe --background --python tools/previs_shot14.py
"""
import json
import math
import os

import bpy
from mathutils import Quaternion, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames14")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720

SINK_X = -1.0
COUNTER_Y = 2.85
COUNTER_TOP_Z = 0.88
ZHOU_POS = (-1.0, 2.08)
XU_ENTER = (0.75, -0.35)   # 画面右侧入画（桌边方向）
XU_STAND = (-0.35, 2.00)   # 周远右侧（靠桌一侧），镜头里与他错开
TABLE_CENTER = (1.15, 1.45)
CHAIR_FAR = (1.15, 2.02)
CHAIR_NEAR = (1.15, 0.88)

WIN_X0, WIN_X1 = -1.9, -0.1
WIN_Z0, WIN_Z1 = 1.15, 2.35
WALL_Y = 3.2

CAM_START = (-2.85, -1.15, 1.52)
CAM_END = (-2.35, -0.75, 1.46)
CAM_LENS = 32


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    before = set(bpy.data.objects)
    before_act = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    new_act = [a for a in bpy.data.actions if a not in before_act]
    kept = []
    for o in new:
        if o.type == "MESH" and ("棱角球" in o.name or "icosphere" in o.name.lower()):
            bpy.data.objects.remove(o, do_unlink=True)
        else:
            kept.append(o)
    for o in kept:
        if o.type == "MESH":
            n = remove_ground_slab(o)
            n2 = remove_bridge_soles(o)
            if n or n2:
                print(f"[previs14] cleanup {path.split(chr(92))[-1]}: slab x{n}, bridge x{n2}", flush=True)
    arms = [o for o in kept if o.type == "ARMATURE"]
    return (arms[0] if arms else None), new_act, kept


def remove_ground_slab(mesh_obj):
    """删掉模型自带的脚底底座板/残片：独立松散部件、宽扁贴地（或埋在地下）。
    Lux3D 导出的网格常在脚下带展示底座碎块，会跟着人走，必须清除。
    判定：独立连通块、整体低于 z0.09、宽扁、有一定大小（鞋子与身体连通，不受影响）。"""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    visited = set()
    removed = 0
    seeds = [v for v in bm.verts if v.co.z < 0.09]
    for s in seeds:
        if s in visited:
            continue
        stack, comp = [s], []
        visited.add(s)
        while stack:
            v = stack.pop()
            comp.append(v)
            for e in v.link_edges:
                o = e.other_vert(v)
                if o not in visited:
                    visited.add(o)
                    stack.append(o)
        xs = [v.co.x for v in comp]
        ys = [v.co.y for v in comp]
        zs = [v.co.z for v in comp]
        dx, dy, dz = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
        if (len(comp) > 15 and max(zs) < 0.09 and dz < 0.06
                and dx > 0.12 and dy > 0.08):
            faces = set()
            for v in comp:
                faces.update(v.link_faces)
            bmesh.ops.delete(bm, geom=list(faces), context="FACES")
            removed += 1
    if removed:
        bm.to_mesh(mesh_obj.data)
    bm.free()
    return removed


def strip_channels(acts, bones):
    """Blender 5.x 分层 action：删除指定骨骼的旋转通道，
    防止渲染前 depsgraph 重评估覆盖手动姿态。"""
    targets = tuple(f'pose.bones["{b}"].rotation_quaternion' for b in bones)
    removed = []
    for ac in acts:
        for layer in ac.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in list(bag.fcurves):
                        if fc.data_path in targets:
                            bone = fc.data_path.split(chr(34))[1]
                            bag.fcurves.remove(fc)
                            removed.append(f"{ac.name}:{bone}")
    return removed


def remove_bridge_soles(mesh_obj):
    """删掉左右脚之间权重混杂的鞋底面。
    自动绑骨把两脚鞋底之间的面做了左右平均加权，走路两脚分开时
    这些面被拉成橡皮筋薄片（预演里脚下的"滑雪板"）。
    只动脚踝以下、左右脚权重都 > 0.2 的面；鞋本身权重单侧，不受影响。"""
    import bmesh
    me = mesh_obj.data
    lg = {g.index for g in mesh_obj.vertex_groups
          if "Left" in g.name and ("Foot" in g.name or "Toe" in g.name or "Leg" in g.name)}
    rg = {g.index for g in mesh_obj.vertex_groups
          if "Right" in g.name and ("Foot" in g.name or "Toe" in g.name or "Leg" in g.name)}
    if not lg or not rg:
        return 0
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    me_verts = me.vertices
    wl_of, wr_of = {}, {}
    for v in bm.verts:
        if v.co.z > -0.45:
            continue
        wl = wr = 0.0
        for g in me_verts[v.index].groups:
            if g.group in lg:
                wl += g.weight
            elif g.group in rg:
                wr += g.weight
        wl_of[v.index] = wl
        wr_of[v.index] = wr
    doomed = []
    for f in bm.faces:
        wls = [wl_of.get(v.index, 0.0) for v in f.verts]
        wrs = [wr_of.get(v.index, 0.0) for v in f.verts]
        if max(wls) > 0.08 and max(wrs) > 0.08:
            doomed.append(f)
    if doomed:
        bmesh.ops.delete(bm, geom=doomed, context="FACES")
        bm.to_mesh(me)
    bm.free()
    return len(doomed)


def make_matte(name, shade, emission=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (shade, shade, shade, 1.0)
            n.inputs["Roughness"].default_value = 0.95
            n.inputs["Metallic"].default_value = 0.0
            if emission is not None:
                n.inputs["Emission Color"].default_value = emission
                n.inputs["Emission Strength"].default_value = 0.8
    return mat


def add_box(name, loc, dims, m=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    box = bpy.context.active_object
    box.name = name
    box.location = loc
    box.dimensions = dims
    if m is not None:
        box.data.materials.append(m)
    return box


def add_cyl(name, loc, radius, depth, m=None, rot=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
    c = bpy.context.active_object
    c.name = name
    if rot is not None:
        c.rotation_euler = rot
    if m is not None:
        c.data.materials.append(m)
    return c


MATS = {}
def mat(key, shade, emission=None):
    if key not in MATS:
        MATS[key] = make_matte(key, shade, emission)
    return MATS[key]


def build_kitchen():
    wall = mat("wall_mat", 0.62)
    add_box("floor", (0, 0, -0.05), (7.0, 8.0, 0.1), mat("floor_mat", 0.42))
    add_box("ceiling", (0, 0, 2.7), (7.0, 8.0, 0.1), mat("ceil_mat", 0.55))
    add_box("left_wall", (-3.2, 0, 1.35), (0.12, 8.0, 2.7), wall)
    add_box("right_wall", (3.2, 0, 1.35), (0.12, 8.0, 2.7), wall)
    add_box("wall_back_l", ((-3.3 + WIN_X0) / 2, WALL_Y, 1.35), (WIN_X0 + 3.3, 0.12, 2.7), wall)
    add_box("wall_back_r", ((WIN_X1 + 3.3) / 2, WALL_Y, 1.35), (3.3 - WIN_X1, 0.12, 2.7), wall)
    add_box("wall_back_top", ((WIN_X0 + WIN_X1) / 2, WALL_Y, (WIN_Z1 + 2.7) / 2),
            (WIN_X1 - WIN_X0, 0.12, 2.7 - WIN_Z1), wall)
    add_box("wall_back_bot", ((WIN_X0 + WIN_X1) / 2, WALL_Y, WIN_Z0 / 2),
            (WIN_X1 - WIN_X0, 0.12, WIN_Z0), wall)
    frame = mat("frame_mat", 0.50)
    cx = (WIN_X0 + WIN_X1) / 2
    cz = (WIN_Z0 + WIN_Z1) / 2
    add_box("win_f_l", (WIN_X0, WALL_Y - 0.03, cz), (0.07, 0.08, WIN_Z1 - WIN_Z0), frame)
    add_box("win_f_r", (WIN_X1, WALL_Y - 0.03, cz), (0.07, 0.08, WIN_Z1 - WIN_Z0), frame)
    add_box("win_f_h", (cx, WALL_Y - 0.03, WIN_Z1), (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    add_box("win_f_b", (cx, WALL_Y - 0.03, WIN_Z0), (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    add_box("win_f_m", (cx, WALL_Y - 0.03, cz), (0.05, 0.08, WIN_Z1 - WIN_Z0), frame)
    night = mat("night_mat", 0.14, emission=(0.10, 0.13, 0.20, 1.0))
    add_box("night", (cx, WALL_Y + 3.0, 1.8), (7.0, 0.1, 3.6), night)

    add_box("counter_body", (-1.0, COUNTER_Y, 0.44), (3.0, 0.6, 0.88), mat("cab_mat", 0.58))
    add_box("counter_top", (-1.0, COUNTER_Y, COUNTER_TOP_Z + 0.02), (3.06, 0.66, 0.05),
            mat("top_mat", 0.80))
    add_box("sink_basin", (SINK_X, COUNTER_Y - 0.05, COUNTER_TOP_Z + 0.01), (0.56, 0.40, 0.04),
            mat("sink_mat", 0.30))
    add_cyl("faucet_stem", (SINK_X, COUNTER_Y + 0.22, 1.03), 0.022, 0.32, mat("faucet_mat", 0.55))
    add_cyl("faucet_arm", (SINK_X, COUNTER_Y + 0.10, 1.17), 0.020, 0.26,
            mat("faucet_mat", 0.55), rot=(math.radians(90), 0, 0))
    add_cyl("faucet_tip", (SINK_X, COUNTER_Y - 0.02, 1.14), 0.018, 0.07,
            mat("faucet_mat", 0.55))
    water = add_cyl("water_stream", (SINK_X, COUNTER_Y - 0.02, 1.02), 0.020, 0.22,
                    mat("water_mat", 0.70, emission=(0.65, 0.72, 0.80, 1.0)))

    for i in range(3):
        add_cyl(f"bowl_stack_{i}", (-0.42, COUNTER_Y + 0.05, 0.95 + i * 0.055),
                0.085, 0.05, mat("bowl_mat", 0.78))
    add_cyl("soap_bottle", (-1.55, COUNTER_Y + 0.08, 0.99), 0.035, 0.20, mat("soap_mat", 0.66))
    add_box("rag", (SINK_X + 0.10, COUNTER_Y + 0.22, 1.12), (0.12, 0.02, 0.16),
            mat("rag_mat", 0.84))
    add_cyl("kettle", (0.15, COUNTER_Y, 0.99), 0.075, 0.22, mat("kettle_mat", 0.70))
    add_box("cooker", (0.42, COUNTER_Y, 0.96), (0.26, 0.26, 0.20), mat("cooker_mat", 0.50))

    shelf = mat("shelf_mat", 0.55)
    add_box("shelf_board", (1.15, WALL_Y - 0.18, 1.62), (1.1, 0.30, 0.04), shelf)
    add_box("shelf_l", (0.65, WALL_Y - 0.18, 1.76), (0.04, 0.28, 0.32), shelf)
    add_box("shelf_r", (1.65, WALL_Y - 0.18, 1.76), (0.04, 0.28, 0.32), shelf)
    add_cyl("jar_1", (0.90, WALL_Y - 0.18, 1.76), 0.055, 0.22, mat("jar_mat", 0.62))
    add_cyl("jar_2", (1.10, WALL_Y - 0.18, 1.75), 0.05, 0.20, mat("jar2_mat", 0.58))
    for i in range(2):
        add_cyl(f"shelf_bowl_{i}", (1.38, WALL_Y - 0.18, 1.67 + i * 0.05),
                0.075, 0.045, mat("bowl_mat", 0.78))

    table = mat("table_mat", 0.60)
    tx, ty = TABLE_CENTER
    add_box("table_top", (tx, ty, 0.74), (0.95, 0.80, 0.05), table)
    for dx in (-0.40, 0.40):
        for dy in (-0.32, 0.32):
            add_box(f"table_leg_{dx}_{dy}", (tx + dx, ty + dy, 0.37), (0.05, 0.05, 0.72),
                    mat("leg_mat", 0.45))
    chair = mat("chair_mat", 0.55)
    for name, (px, py), back_dy in (("chair_far", CHAIR_FAR, 0.20),
                                    ("chair_near", CHAIR_NEAR, -0.20)):
        add_box(f"{name}_seat", (px, py, 0.44), (0.45, 0.45, 0.05), chair)
        add_box(f"{name}_back", (px, py + back_dy, 0.75), (0.45, 0.05, 0.6), chair)
        for lx in (-0.18, 0.18):
            for ly in (-0.18, 0.18):
                add_box(f"{name}_leg_{lx}_{ly}", (px + lx, py + ly, 0.22), (0.04, 0.04, 0.44), chair)
    chair_far_parts = [o for o in bpy.context.scene.objects if o.name.startswith("chair_far")]

    add_cyl("bulb_cord", (-2.35, 1.6, 2.35), 0.008, 0.7, mat("cord_mat", 0.30))
    add_cyl("bulb_shade", (-2.35, 1.6, 1.95), 0.10, 0.08, mat("shade_mat", 0.60))
    add_cyl("bulb", (-2.35, 1.6, 1.88), 0.045, 0.07,
            mat("bulb_mat", 0.90, emission=(1.0, 0.82, 0.55, 1.0)))
    return water, chair_far_parts


def add_lighting():
    world = bpy.data.worlds.new("previz_world14")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.22, 0.23, 0.27, 1.0)
            n.inputs[1].default_value = 0.85
    bpy.context.scene.world = world
    bpy.ops.object.light_add(type="AREA", location=((WIN_X0 + WIN_X1) / 2, WALL_Y + 1.6, 2.0))
    key = bpy.context.active_object
    key.data.energy = 260
    key.data.size = 3.2
    key.data.color = (0.55, 0.65, 0.85)
    key.rotation_euler = (math.radians(65), 0, math.radians(180))
    bpy.ops.object.light_add(type="POINT", location=(-2.35, 1.6, 1.80))
    bl = bpy.context.active_object
    bl.data.energy = 220
    bl.data.color = (1.0, 0.80, 0.55)
    bpy.ops.object.light_add(type="AREA", location=(1.15, 1.0, 2.2))
    fill = bpy.context.active_object
    fill.data.energy = 180
    fill.data.size = 2.0
    fill.data.color = (1.0, 0.85, 0.68)
    fill.rotation_euler = (math.radians(40), 0, math.radians(20))


def ease(t):
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def rotate_world(arm_obj, bone_name, world_axis, angle_deg):
    rotate_ops(arm_obj, bone_name, [(world_axis, angle_deg)])


def rotate_ops(arm_obj, bone_name, ops):
    """多段世界轴旋转组合（按顺序左乘），用于姿态叠加。"""
    pb = arm_obj.pose.bones.get(bone_name)
    if pb is None:
        return
    rest_q = pb.bone.matrix_local.to_quaternion()
    qw = Quaternion((1, 0, 0, 0))
    for axis, ang in ops:
        if abs(ang) < 1e-6:
            continue
        qw = Quaternion(Vector(axis).normalized(), math.radians(ang)) @ qw
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = rest_q.inverted() @ qw @ rest_q


def make_loop(act):
    """Blender 5.x 分层 action：从 channelbag 取 fcurves 加 CYCLES 外推。"""
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    if not any(m.type == "CYCLES" for m in fc.modifiers):
                        fc.modifiers.new("CYCLES")


def set_oneshot(ad, act, f0, speed, state, key):
    """一次性动作走 NLA：场景 f0 处从动作首帧开始，speed>1 加速。"""
    if state.get("key") == key:
        return
    ad.action = None
    for tr in list(ad.nla_tracks):
        ad.nla_tracks.remove(tr)
    tr = ad.nla_tracks.new()
    s0, s1 = act.frame_range
    length = max(float(s1 - s0), 1.0)
    strip = tr.strips.new(act.name, int(f0), act)
    strip.action_frame_start = s0
    strip.action_frame_end = s1
    strip.frame_end = f0 + length / speed
    state["key"] = key


def set_loop(ad, act, state, key):
    if state.get("key") == key:
        return
    ad.action = act
    for tr in list(ad.nla_tracks):
        ad.nla_tracks.remove(tr)
    state["key"] = key


def feet_z(arm_obj):
    zs = []
    for bn in ("mixamorig:LeftFoot", "mixamorig:RightFoot"):
        pb = arm_obj.pose.bones.get(bn)
        if pb is not None:
            zs.append((arm_obj.matrix_world @ pb.head).z)
    return min(zs) if zs else 0.0


def arms_down(a):
    """双臂从 T-pose  rest 放回体侧（idle 动作的臂通道已剥，需每帧手动）。"""
    rotate_world(a, "mixamorig:RightArm", (0, 1, 0), -72)
    rotate_world(a, "mixamorig:LeftArm", (0, 1, 0), 72)
    rotate_world(a, "mixamorig:RightForeArm", (0, 1, 0), 8)
    rotate_world(a, "mixamorig:LeftForeArm", (0, 1, 0), -8)


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    water, chair_far_parts = build_kitchen()
    add_lighting()

    zhou, zhou_acts, _ = import_glb(os.path.join(MODELS, "C15", "tex_mesh_animated.glb"))
    zhou_w, zhou_walk, zhou_w_objs = import_glb(os.path.join(MODELS, "C15", "tex_mesh_walk.glb"))
    xu, xu_acts, _ = import_glb(os.path.join(MODELS, "C05", "tex_mesh_v08_anim4.glb"))
    # walk glb 只取 action，删掉它带入的全部对象（骨架+网格），避免重影
    for o in zhou_w_objs:
        bpy.data.objects.remove(o, do_unlink=True)
    for a in (zhou, xu):
        a.rotation_mode = "XYZ"
    print("[previs14] zhou_acts", [a.name for a in zhou_acts], flush=True)
    print("[previs14] xu_acts", [a.name for a in xu_acts], flush=True)

    ACT_ZHOU_IDLE = zhou_acts[0]     # Idle_Loop
    ACT_ZHOU_SIT_E = zhou_acts[1]    # Sitting_Enter
    ACT_ZHOU_SIT_I = zhou_acts[3]    # Sitting_Idle_Loop
    ACT_ZHOU_WALK = zhou_walk[0]     # Walk_Loop
    ACT_XU_WALK = xu_acts[0]         # Walk_Loop
    ACT_XU_IDLE = xu_acts[1]         # Idle_Loop
    ACT_XU_SIT_E = xu_acts[2]        # Sitting_Enter
    ACT_XU_SIT_I = xu_acts[3]        # Sitting_Idle_Loop
    for ac in (ACT_ZHOU_IDLE, ACT_ZHOU_WALK, ACT_XU_WALK, ACT_XU_IDLE,
               ACT_ZHOU_SIT_I, ACT_XU_SIT_I):
        make_loop(ac)
    # 手动覆盖的骨骼通道从 loop 动作里剥掉（idle 阶段叠洗碗/对话姿态）
    MANUAL_BONES = ("mixamorig:RightArm", "mixamorig:LeftArm",
                    "mixamorig:RightForeArm", "mixamorig:LeftForeArm",
                    "mixamorig:Head", "mixamorig:Neck",
                    "mixamorig:Spine", "mixamorig:Spine1")
    removed = strip_channels([ACT_ZHOU_IDLE, ACT_XU_IDLE], MANUAL_BONES)
    print("[previs14] stripped", len(removed), "channels", flush=True)

    zhou_ad = zhou.animation_data
    xu_ad = xu.animation_data

    bpy.context.view_layer.update()
    zhou_dz = -feet_z(zhou) + 0.02
    xu_dz = -feet_z(xu) + 0.02

    matte = make_matte("char_matte14", 0.82)
    keep = ("floor", "wall", "frame", "night", "counter", "sink", "faucet", "water",
            "bowl", "soap", "rag", "kettle", "cooker", "shelf", "jar", "table",
            "leg", "chair", "bulb", "cord", "shade", "ceil", "top")
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        mnames = [m.name for m in o.data.materials] if o.data.materials else []
        if any(any(k in mn for k in keep) for mn in mnames):
            continue
        o.data.materials.clear()
        o.data.materials.append(matte)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = N_FRAMES
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    cam_data = bpy.data.cameras.new("previs_cam14")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.data.objects.new("previs_cam14", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    sp = Vector(CAM_START)
    ep = Vector(CAM_END)
    aim_static = Vector((-0.1, 1.9, 1.0))

    XU_PATH_1 = (XU_ENTER, (0.20, 0.90), XU_STAND)
    XU_PATH_2 = (XU_STAND, (0.30, 1.62), (1.15, 1.70))   # 远椅前站定位
    ZHOU_PATH_1 = (ZHOU_POS, (-0.50, 1.62), (0.55, 1.70), (1.15, 2.30))  # 远椅正后方（拉椅子位）
    ZHOU_PATH_2 = ((1.15, 2.30), (0.62, 1.95), (0.62, 1.30), (1.15, 0.95))  # 沿桌西侧绕到近椅
    XU_STAND2 = (1.15, 1.70)
    XU_SIT_LOC = (1.15, 1.88)                    # 远椅拉出后的座心
    ZHOU_SIT_LOC = (CHAIR_NEAR[0], CHAIR_NEAR[1] + 0.04)

    def lerp_path(pts, k):
        k = max(0.0, min(1.0, k))
        segs = len(pts) - 1
        sk = k * segs
        i = min(int(sk), segs - 1)
        return Vector(pts[i]).lerp(Vector(pts[i + 1]), sk - i)

    def path_facing(pts, k):
        """路径切线朝向（度）：面向 = 本地 -y，rot z 使 -y 转到切线方向。"""
        k = max(0.0, min(1.0, k))
        segs = len(pts) - 1
        sk = k * segs
        i = min(int(sk), segs - 1)
        d = Vector(pts[i + 1]) - Vector(pts[i])
        if d.length < 1e-6:
            return 0.0
        d.normalize()
        return math.degrees(math.atan2(d.x, -d.y))

    def blend_rot(start, end, t):
        """最短路径角度插值，用于起步/到站时的站立转身过渡。"""
        d = (end - start + 180.0) % 360.0 - 180.0
        return start + d * max(0.0, min(1.0, t))

    st_z = {"key": None}
    st_x = {"key": None}

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    if test_mode:
        frames_iter = [1, 30, 50, 75, 100, 130, 145, 155, 165, 175, 190, 192]
    elif os.environ.get("PREVIS_RANGE"):
        a, b = os.environ["PREVIS_RANGE"].split("-")
        frames_iter = range(int(a), int(b) + 1)
    else:
        frames_iter = range(1, N_FRAMES + 1)

    for f in frames_iter:
        t = ease((f - 1) / (N_FRAMES - 1))

        # ================= 周远（对象级）=================
        if f <= 125:
            set_loop(zhou_ad, ACT_ZHOU_IDLE, st_z, "idle")
            zhou.location = (ZHOU_POS[0], ZHOU_POS[1], zhou_dz)
            zhou.rotation_euler = (0, 0, math.radians(180))
        elif f <= 148:
            set_loop(zhou_ad, ACT_ZHOU_WALK, st_z, "walk1")
            k1 = ease((f - 126) / 22)
            p = lerp_path(ZHOU_PATH_1, k1)
            zhou.location = (p.x, p.y, zhou_dz)
            tang = path_facing(ZHOU_PATH_1, k1)
            # 起步前 3 帧从面向水槽(180)转身到路径方向，避免硬切
            rot = blend_rot(180.0, tang, k1 / 0.14) if k1 < 0.14 else tang
            zhou.rotation_euler = (0, 0, math.radians(rot))
        elif f <= 163:
            set_loop(zhou_ad, ACT_ZHOU_IDLE, st_z, "idle2")
            zhou.location = (1.15, 2.30, zhou_dz)
            arrive = path_facing(ZHOU_PATH_1, 1.0)          # 到站朝向（东北）
            rot = blend_rot(arrive, 0.0, (f - 149) / 6.0)   # 站立转身面向椅子
            zhou.rotation_euler = (0, 0, math.radians(rot))
        elif f <= 175:
            set_loop(zhou_ad, ACT_ZHOU_WALK, st_z, "walk2")
            k2 = ease((f - 164) / 11)
            p = lerp_path(ZHOU_PATH_2, k2)
            zhou.location = (p.x, p.y, zhou_dz)
            tang = path_facing(ZHOU_PATH_2, k2)
            if k2 < 0.18:
                rot = blend_rot(0.0, tang, k2 / 0.18)       # 起步转身
            elif k2 > 0.75:
                rot = blend_rot(tang, 180.0, (k2 - 0.75) / 0.25)  # 到站前转向坐姿朝向
            else:
                rot = tang
            zhou.rotation_euler = (0, 0, math.radians(rot))
        elif f <= 190:
            set_oneshot(zhou_ad, ACT_ZHOU_SIT_E, 176, 2.5, st_z, "sit")
            zhou.location = (*ZHOU_SIT_LOC, zhou_dz)
            zhou.rotation_euler = (0, 0, math.radians(180))
        else:
            set_loop(zhou_ad, ACT_ZHOU_SIT_I, st_z, "sitidle")
            zhou.location = (*ZHOU_SIT_LOC, zhou_dz)
            zhou.rotation_euler = (0, 0, math.radians(180))

        # ================= 许宁（对象级）=================
        if f <= 40:
            set_loop(xu_ad, ACT_XU_WALK, st_x, "walk")
            k = ease((f - 1) / 39)
            p = lerp_path(XU_PATH_1, k)
            xu.location = (p.x, p.y, xu_dz)
            xu.rotation_euler = (0, 0, math.radians(195))
        elif f <= 137:
            set_loop(xu_ad, ACT_XU_IDLE, st_x, "idle")
            xu.location = (XU_STAND[0], XU_STAND[1], xu_dz)
            xu.rotation_euler = (0, 0, math.radians(195))
        elif f <= 152:
            set_loop(xu_ad, ACT_XU_WALK, st_x, "walk2")
            km = ease((f - 138) / 14)
            p = lerp_path(XU_PATH_2, km)
            xu.location = (p.x, p.y, xu_dz)
            tang = path_facing(XU_PATH_2, km)
            if km < 0.15:
                rot = blend_rot(195.0, tang, km / 0.15)      # 起步先转身
            elif km > 0.8:
                rot = blend_rot(tang, 0.0, (km - 0.8) / 0.2)  # 到站前转向椅子
            else:
                rot = tang
            xu.rotation_euler = (0, 0, math.radians(rot))
        elif f <= 164:
            set_loop(xu_ad, ACT_XU_IDLE, st_x, "idle2")
            xu.location = (XU_STAND2[0], XU_STAND2[1], xu_dz)
            xu.rotation_euler = (0, 0, 0)
        elif f <= 187:
            set_oneshot(xu_ad, ACT_XU_SIT_E, 165, 1.8, st_x, "sit")
            xu.location = (*XU_SIT_LOC, xu_dz)
            xu.rotation_euler = (0, 0, 0)
        else:
            set_loop(xu_ad, ACT_XU_SIT_I, st_x, "sitidle")
            xu.location = (*XU_SIT_LOC, xu_dz)
            xu.rotation_euler = (0, 0, 0)

        scene.frame_set(f)
        if test_mode:
            print(f"[dbg] f{f} zhou key={st_z['key']} act={zhou_ad.action.name if zhou_ad.action else None} "
                  f"nla={len(zhou_ad.nla_tracks)} xu key={st_x['key']} act={xu_ad.action.name if xu_ad.action else None}",
                  flush=True)

        # ================= 手动姿态（frame_set 之后）=================
        # ---- 周远 ----
        if f <= 60:
            amp = 1.0 - ease((f - 36) / 19)   # f36 起搓洗渐停，手臂保持在水槽上方
            scrub = math.sin(f / 6.0) * 10.0 * amp
            rotate_world(zhou, "mixamorig:Spine", (1, 0, 0), 26 * amp + 3)
            rotate_world(zhou, "mixamorig:Spine1", (1, 0, 0), 13 * amp + 2)
            rotate_ops(zhou, "mixamorig:RightArm", [((0, 1, 0), -20), ((0, 0, 1), 78)])
            rotate_ops(zhou, "mixamorig:LeftArm", [((0, 1, 0), 20), ((0, 0, 1), -71)])
            rotate_world(zhou, "mixamorig:RightForeArm", (0, 1, 0), 60 + scrub)
            rotate_world(zhou, "mixamorig:LeftForeArm", (0, 1, 0), -(55 - scrub))
            rotate_world(zhou, "mixamorig:Head", (1, 0, 0), 12 * amp)
        if 61 <= f <= 90:
            arms_down(zhou)
            k = ease((f - 61) / 24)
            rotate_ops(zhou, "mixamorig:RightArm", [((0, 1, 0), -20 - 5 * k), ((0, 0, 1), 78 - 3 * k)])
            rotate_world(zhou, "mixamorig:RightForeArm", (0, 1, 0), 60 - 85 * k)  # 前臂上抬够龙头
            rotate_world(zhou, "mixamorig:Head", (1, 0, 0), -8 * k)
        if 91 <= f <= 105:
            k = ease((f - 91) / 14)          # 手臂从关水姿态连续放回体侧
            rotate_ops(zhou, "mixamorig:RightArm", [((0, 1, 0), -25 - 47 * k), ((0, 0, 1), 75 * (1 - k))])
            rotate_world(zhou, "mixamorig:RightForeArm", (0, 1, 0), -25 + 33 * k)
            rotate_world(zhou, "mixamorig:LeftArm", (0, 1, 0), 72)
            rotate_world(zhou, "mixamorig:LeftForeArm", (0, 1, 0), -8)
            rotate_world(zhou, "mixamorig:Neck", (0, 0, 1), -20 * k)
            rotate_world(zhou, "mixamorig:Head", (0, 0, 1), -14 * k)
        if 106 <= f <= 125:
            arms_down(zhou)
            rotate_world(zhou, "mixamorig:Neck", (0, 0, 1), -20)
            rotate_world(zhou, "mixamorig:Head", (0, 0, 1), -14)
        if 126 <= f <= 135:
            arms_down(zhou)
            k = 1.0 - ease((f - 126) / 9)    # 起步走路，头回正
            rotate_world(zhou, "mixamorig:Neck", (0, 0, 1), -20 * k)
            rotate_world(zhou, "mixamorig:Head", (0, 0, 1), -14 * k)
        if 149 <= f <= 163:
            arms_down(zhou)
            if 153 <= f <= 158:              # 抬手示意她坐
                k = ease((f - 153) / 4)
                rotate_ops(zhou, "mixamorig:RightArm", [((0, 1, 0), -72), ((0, 0, 1), 55 * k)])
                rotate_ops(zhou, "mixamorig:RightForeArm", [((0, 1, 0), 8 + 12 * k)])

        # ---- 许宁 ----
        if 41 <= f <= 137:
            arms_down(xu)
            k = ease((f - 41) / 20)
            kk = k if f <= 52 else (1.0 - ease((f - 52) / 8) if f <= 60 else 0.0)
            if kk > 1e-6:                    # 道歉时右手微抬（组合在垂臂之上）
                rotate_ops(xu, "mixamorig:RightArm", [((0, 1, 0), -72), ((0, 0, 1), 12 * kk)])
                rotate_ops(xu, "mixamorig:RightForeArm", [((0, 1, 0), 8 + 20 * kk)])
            zk = 1.0 if f <= 125 else 1.0 - ease((f - 125) / 10)   # 侧头渐出
            if f <= 90:
                rotate_world(xu, "mixamorig:Head", (0, 0, 1), 12 * k if f <= 60 else 12.0)
            elif f <= 110:                   # 说爸爸的事：低头
                rotate_world(xu, "mixamorig:Head", (1, 0, 0), 15 * ease((f - 91) / 19))
                rotate_world(xu, "mixamorig:Head", (0, 0, 1), 12 * zk)
            else:                            # 抬头，侧头保持
                rotate_world(xu, "mixamorig:Head", (1, 0, 0), 15 * (1 - ease((f - 111) / 19)))
                rotate_world(xu, "mixamorig:Head", (0, 0, 1), 12 * zk)
        if 153 <= f <= 164:
            arms_down(xu)

        # ================= 道具 =================
        if f <= 84:
            water.scale = (1, 1, 1)
        elif f <= 87:
            k = 1 - (f - 84) / 3.0
            water.scale = (k, k, k)
        else:
            water.scale = (0.001, 0.001, 0.001)
        dy = 0.0 if f <= 149 else -0.12 * ease((f - 149) / 9)   # f149-158 拉椅子
        for o in chair_far_parts:
            o.location.y = dy

        # ================= 相机 =================
        zhou_head = zhou.matrix_world @ zhou.pose.bones["mixamorig:Head"].head
        xu_head = xu.matrix_world @ xu.pose.bones["mixamorig:Head"].head
        aim = aim_static.lerp(zhou_head, 0.18).lerp(xu_head, 0.12)
        cam.location = sp.lerp(ep, t)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs14] frame {f}/{N_FRAMES}", flush=True)

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
              "zhou_pos": ZHOU_POS, "xu_stand": XU_STAND, "table": TABLE_CENTER,
              "chair_far": CHAIR_FAR, "chair_near": CHAIR_NEAR}
    with open(os.path.join(OUT_DIR, "previs14_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS14_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
