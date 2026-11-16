# -*- coding: utf-8 -*-
"""白模预演：shot10「返校的车上」（大巴车内，许宁看照片又望窗外）。

剧本（四 L237-241）：返校的车上，她看了又看。窗外有人拎着菜走过，电动车在路口停下等灯。
她试着把爸爸放回这条街。

走位时间轴（192f / 8s）：
- f1-50   许宁靠窗坐姿，低头看手机（右手持机于胸前），车窗外街景流动
- f50-85  缓缓抬头，视线从手机移向窗外；同时右手把手机放回到腿上（变化过程写明）
- f85-120 头转向窗外（向左转），微仰
- f120-192 保持望向窗外，车身轻微晃动
- 镜头在过道一侧，轻微手持晃动 + 缓推

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot10.py   (构图测试)
  blender.exe --background --python tools/previs_shot10.py                          (192 帧全量)
"""
import json
import math
import os

import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames10")

FPS = 24
DURATION_S = 8
N_FRAMES = FPS * DURATION_S
RES_X, RES_Y = 1280, 720

# ---- 时间轴 ----
F_LOOK_PHONE_END = 50       # 低头看手机的结束
F_RAISE_END = 85            # 抬头+放手机到腿上的结束
F_TURN_END = 120            # 头转向窗外到位
F_END = N_FRAMES

SEAT_X = 2.2                # 许宁的靠窗座位中心
SEAT_Y = 0.0
XU_ROT = 0.0                # 面向 -y（镜头方向）

CAM_START_POS = (1.30, -2.35, 1.50)
CAM_END_POS = (1.50, -1.90, 1.42)
CAM_LENS = 35


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def make_matte(name, shade):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (shade, shade, shade, 1.0)
            n.inputs["Roughness"].default_value = 0.95
            n.inputs["Metallic"].default_value = 0.0
    return mat


def add_box(name, loc, dims, mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    box = bpy.context.active_object
    box.name = name
    box.location = loc
    box.dimensions = dims
    if mat is not None:
        box.data.materials.append(mat)
    return box


# ---- 材质 ----
MATS = {}
def mat(key, shade):
    if key not in MATS:
        MATS[key] = make_matte(key, shade)
    return MATS[key]


WINDOW_Z0, WINDOW_Z1 = 0.95, 2.05
WALL_X = 4.0


def build_bus_interior():
    """程序化大巴内饰：地板/天花板/右侧带窗洞的墙/行李架/座椅/窗外流动街景。"""
    add_box("floor", (1.0, 0, -0.05), (7.0, 11.0, 0.1), mat("floor_mat", 0.42))
    add_box("ceiling", (1.0, 0, 2.35), (7.0, 11.0, 0.1), mat("ceil_mat", 0.80))

    # 右墙（带 3 个窗洞，窗中心 y = -2.5 / 0 / 2.5，宽 1.9）
    wall = mat("wall_mat", 0.76)
    spans_above = [(1.0, WINDOW_Z1 + (2.35 - WINDOW_Z1) / 2, 2.35 - WINDOW_Z1)]
    add_box("wall_top", (WALL_X, 0, (WINDOW_Z1 + 2.35) / 2), (0.12, 11.0, 2.35 - WINDOW_Z1), wall)
    add_box("wall_bottom", (WALL_X, 0, WINDOW_Z0 / 2), (0.12, 11.0, WINDOW_Z0), wall)
    strips = [(-5.0, -3.45), (-1.55, -0.95), (0.95, 1.55), (3.45, 5.0)]
    for i, (y0, y1) in enumerate(strips):
        add_box(f"wall_strip_{i}", (WALL_X, (y0 + y1) / 2, (WINDOW_Z0 + WINDOW_Z1) / 2),
                (0.12, y1 - y0, WINDOW_Z1 - WINDOW_Z0), wall)
    # 窗框（细条）
    frame_mat = mat("frame_mat", 0.55)
    for i, cy in enumerate((-2.5, 0.0, 2.5)):
        add_box(f"win_frame_v_{i}", (WALL_X - 0.02, cy - 0.95, (WINDOW_Z0 + WINDOW_Z1) / 2),
                (0.06, 0.06, WINDOW_Z1 - WINDOW_Z0), frame_mat)
        add_box(f"win_frame_h_{i}", (WALL_X - 0.02, cy, (WINDOW_Z0 + WINDOW_Z1) / 2),
                (0.06, 1.9, 0.06), frame_mat)

    # 行李架（沿右墙上方一条）
    add_box("rack", (3.55, 0, 2.12), (0.7, 10.5, 0.08), mat("rack_mat", 0.68))

    # 座椅（蓝灰织物）：许宁的座位 + 前后排空座 + 过道侧座位
    seat_mat = mat("seat_mat", 0.58)
    def seat(name, sx, sy, back_h=1.15):
        add_box(f"{name}_pan", (sx, sy, 0.42), (0.95, 0.52, 0.12), seat_mat)
        add_box(f"{name}_back", (sx + 0.42, sy, 0.49 + back_h / 2 - 0.1), (0.14, 0.52, back_h - 0.55 + 0.35), seat_mat)
    # 许宁的靠窗座（窗侧一排 x~2.2）与前、后空座
    seat("seat_xu", SEAT_X, SEAT_Y)
    seat("seat_front", SEAT_X, SEAT_Y - 1.6)
    seat("seat_back", SEAT_X, SEAT_Y + 1.6)
    # 过道侧座位（前景遮挡层）
    seat("seat_aisle0", 0.75, SEAT_Y - 1.2)
    seat("seat_aisle1", 0.75, SEAT_Y + 1.0)

    # 窗外：明亮天幕 + 流动的树/街景块（整体向 -y 移动循环）
    sky_mat = make_matte("sky_mat", 0.97)
    for n in sky_mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Emission Color"].default_value = (0.72, 0.82, 0.72, 1.0)
            n.inputs["Emission Strength"].default_value = 0.7
    add_box("sky", (8.0, 0, 2.0), (0.1, 30.0, 6.0), sky_mat)

    tree_mat = mat("tree_mat", 0.52)
    bld_mat = mat("bld_mat", 0.66)
    movers = []
    # 树球 + 街景块，均匀分布在 20m 带上
    items = [(6.2, -8.0, "tree"), (6.8, -5.0, "bld"), (6.2, -2.0, "tree"),
             (7.0, 1.0, "bld"), (6.2, 4.0, "tree"), (6.8, 7.0, "tree"), (7.0, 10.0, "bld")]
    for i, (bx, by, kind) in enumerate(items):
        if kind == "tree":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.9, location=(bx, by, 1.6))
            s = bpy.context.active_object
            s.name = f"out_tree_{i}"
            s.scale = (0.5, 1.0, 1.0)
            bpy.ops.object.transform_apply(scale=True)
            s.data.materials.append(tree_mat)
        else:
            add_box(f"out_bld_{i}", (bx, by, 1.5), (0.5, 2.2, 3.0), bld_mat)
        movers.append(bpy.context.scene.objects.get(f"out_tree_{i}") or bpy.context.scene.objects.get(f"out_bld_{i}"))
    return movers


def add_lighting():
    world = bpy.data.worlds.new("previz_world10")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.55, 0.52, 0.45, 1.0)
            n.inputs[1].default_value = 0.5
    bpy.context.scene.world = world
    # 窗外暖阳（从 +x 高角度射入，穿过窗户）
    bpy.ops.object.light_add(type="AREA", location=(7.0, -1.0, 4.5))
    key = bpy.context.active_object
    key.data.energy = 1000
    key.data.size = 5.0
    key.data.color = (1.0, 0.85, 0.62)
    key.rotation_euler = (math.radians(55), math.radians(-20), math.radians(115))
    # 车内柔光补
    bpy.ops.object.light_add(type="AREA", location=(0.0, -1.0, 2.2))
    fill = bpy.context.active_object
    fill.data.energy = 400
    fill.data.size = 4.0
    fill.data.color = (0.85, 0.88, 0.95)


def ease(t):
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def rotate_pose_bone_world(arm_obj, bone_name, world_axis, angle_deg):
    pb = arm_obj.pose.bones.get(bone_name)
    if pb is None:
        return
    rest_q = pb.bone.matrix_local.to_quaternion()
    q_world = Quaternion(Vector(world_axis).normalized(), math.radians(angle_deg))
    q_local = rest_q.inverted() @ q_world @ rest_q
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = q_local


def strip_arm_channels(acts):
    targets = (
        'pose.bones["mixamorig:RightArm"].rotation_quaternion',
        'pose.bones["mixamorig:RightForeArm"].rotation_quaternion',
        'pose.bones["mixamorig:Head"].rotation_quaternion',
    )
    removed = []
    for ac in acts.values():
        for layer in ac.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in list(bag.fcurves):
                        if fc.data_path in targets:
                            bone = fc.data_path.split(chr(34))[1]
                            bag.fcurves.remove(fc)
                            removed.append(f"{ac.name}:{bone}")
    return removed


def xu_arm_and_head(arm_obj, f):
    """右臂：f1-60 持机于胸前 → f60-100 放到腿上；头：f50-85 从俯到抬 → f85-120 转向窗。"""
    pb = arm_obj.pose.bones.get("mixamorig:RightArm")
    if pb is not None:
        rest_q = pb.bone.matrix_local.to_quaternion()
        inv = rest_q.inverted()
        if f < 60:
            k = 1.0
        elif f <= 100:
            k = 1.0 - ease((f - 60) / 40)
        else:
            k = 0.0
        # k=1 持机胸前：y-20/z+45/elbow75；k=0 放手到腿：y-65/z+25/elbow40
        y_ang = -65.0 + 45.0 * k
        z_ang = 25.0 + 20.0 * k
        elbow = 40.0 + 35.0 * k
        q = inv @ Quaternion((0, 1, 0), math.radians(y_ang)) @ rest_q
        q = q @ (inv @ Quaternion((0, 0, 1), math.radians(z_ang)) @ rest_q)
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = q
        pf = arm_obj.pose.bones.get("mixamorig:RightForeArm")
        if pf is not None:
            rest_f = pf.bone.matrix_local.to_quaternion()
            inv_f = rest_f.inverted()
            pf.rotation_mode = "QUATERNION"
            pf.rotation_quaternion = inv_f @ Quaternion((0, 1, 0), math.radians(elbow)) @ rest_f

    # 头：面向 -y 时，低头 = 绕 (1,0,0) 正角度；转向窗（+x，她左侧）= 绕 (0,0,1) 正角度
    if f <= F_LOOK_PHONE_END:
        pitch = 25.0
    elif f <= F_RAISE_END:
        pitch = 25.0 - 30.0 * ease((f - F_LOOK_PHONE_END) / (F_RAISE_END - F_LOOK_PHONE_END))
    else:
        pitch = -12.0
    if f <= F_RAISE_END:
        turn = 0.0
    elif f <= F_TURN_END:
        turn = 28.0 * ease((f - F_RAISE_END) / (F_TURN_END - F_RAISE_END))
    else:
        turn = 28.0
    if abs(pitch) > 0.01:
        rotate_pose_bone_world(arm_obj, "mixamorig:Head", (1, 0, 0), pitch)
    if abs(turn) > 0.01:
        rotate_pose_bone_world(arm_obj, "mixamorig:Head", (0, 0, 1), turn)


def find_actions():
    acts = {}
    for ac in bpy.data.actions:
        if ac.name.lower() == "animation_1":
            acts["sit"] = ac
    return acts


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    movers = build_bus_interior()
    add_lighting()

    # 许宁 C05（坐姿动画）
    pre = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, "C05", "tex_mesh_v08_sitting.glb"))
    new = [o for o in bpy.context.scene.objects if o not in pre]
    for o in new:
        if o.type == "MESH" and "棱角球" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE" and o in new] or \
           [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    xu = arms[-1]
    xu.rotation_mode = "XYZ"
    xu.location = (SEAT_X - 0.1, SEAT_Y, 0.78)   # 坐姿 glb 原点在脚上方 0.74（探针实测）
    xu.rotation_euler = (0, 0, math.radians(XU_ROT))
    bpy.context.view_layer.update()

    acts = find_actions()
    print(f"[previs10] actions: {list(acts.keys())}", flush=True)
    removed = strip_arm_channels(acts)
    print(f"[previs10] stripped: {removed}", flush=True)

    apply_matte = make_matte("char_matte10", 0.82)
    for o in mesh_objects():
        if o.name.startswith(("out_", "sky")):
            continue
        key = next((k for k in ("floor_mat", "seat_mat", "wall_mat", "frame_mat", "sky_mat",
                                "tree_mat", "bld_mat", "ceil_mat", "rack_mat") if k in [m.name for m in o.data.materials] if o.data.materials), None)
        if key is None:
            o.data.materials.clear()
            o.data.materials.append(apply_matte)

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

    cam_data = bpy.data.cameras.new("previs_cam10")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.data.objects.new("previs_cam10", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    sp = Vector(CAM_START_POS)
    ep = Vector(CAM_END_POS)

    st = {"key": None}

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    frames_iter = [1, 40, 70, 100, 140, 190] if test_mode else range(1, N_FRAMES + 1)
    for f in frames_iter:
        t = ease((f - 1) / (N_FRAMES - 1))

        if "sit" in acts and st.get("key") != "sit":
            xu.animation_data.action = acts["sit"]
            st["key"] = "sit"

        # 窗外街景流动：整体向 -y，循环带长 15m（items 分布在 -8..10）
        shift = -((f - 1) * 0.055) % 15.0
        base = {"out_tree_0": -8.0, "out_bld_1": -5.0, "out_tree_2": -2.0, "out_bld_3": 1.0,
                "out_tree_4": 4.0, "out_tree_5": 7.0, "out_bld_6": 10.0}
        for name, y0 in base.items():
            o = bpy.context.scene.objects.get(name)
            if o is not None:
                o.location.y = ((y0 + shift + 8.0) % 15.0) - 8.0

        scene.frame_set(f)
        xu_arm_and_head(xu, f)

        head = xu.matrix_world @ xu.pose.bones["mixamorig:Head"].head
        cam.location = sp.lerp(ep, t)
        # 轻微手持晃动
        cam.location.x += 0.012 * math.sin(2.0 * math.pi * f / 47.0)
        cam.location.z += 0.010 * math.sin(2.0 * math.pi * f / 39.0)
        cam.rotation_euler = (head - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs10] frame {f}/{N_FRAMES}", flush=True)

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS}
    with open(os.path.join(OUT_DIR, "previs10_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS10_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
