# -*- coding: utf-8 -*-
"""白模预演：shot13「两只碗」（第五章，许宁摆第二只碗，周远不出镜）。

剧本（五 L249）：只是他来吃饭的次数多了，许宁买碗时，顺手拿了两只。

机位修正版：许宁站桌子左侧（侧身对镜头），桌面两只碗全程可见；
新碗从近侧椅子上的购物袋取出，动线全在臂展内。

时间轴（192f / 8s），变化三态：
- f1-40    许宁站在小桌左侧，桌上只有一只碗和一双筷（before）
- f40-90   她转身从近侧椅子上的袋子里拿起一只新碗（process）
- f90-140  她把新碗端到桌上，在第一只碗旁放下
- f140-192 她低头看两只并排的碗，停了停（after）

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot13.py
  blender.exe --background --python tools/previs_shot13.py
"""
import json
import math
import os

import bpy
from mathutils import Quaternion, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames13")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720

XU_Z = 0.78
XU_POS = (-0.55, 0.75)        # 桌左侧，rot 65 = 面向桌、微侧脸向镜头
BAG_POS = (0.42, -0.18, 0.60)  # 近侧椅子上的袋子，碗B起点
TABLE_CENTER = (0.4, 0.9)
BOWL_A = (0.25, 0.78, 0.80)
BOWL_B_REST = (0.58, 0.78, 0.80)

WIN_X0, WIN_X1 = -2.7, -1.3
WIN_Z0, WIN_Z1 = 1.05, 2.25
WALL_Y = 3.2

CAM_START = (-2.40, -1.60, 1.52)
CAM_END = (-1.95, -1.10, 1.44)
CAM_LENS = 35


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)


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


def add_cyl(name, loc, radius, depth, mat=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
    c = bpy.context.active_object
    c.name = name
    if mat is not None:
        c.data.materials.append(mat)
    return c


MATS = {}
def mat(key, shade):
    if key not in MATS:
        MATS[key] = make_matte(key, shade)
    return MATS[key]


def build_room():
    """E09 餐桌角：后墙窗/折叠方桌/两把椅/碗柜/单灶锅/暖瓶/碗筷/购物袋。"""
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
    curtain = make_matte("curtain_mat", 0.86)
    add_box("curtain", (cx + 0.55, WALL_Y - 0.10, cz), (0.34, 0.02, WIN_Z1 - WIN_Z0 + 0.1), curtain)
    sky = make_matte("sky_mat", 0.85)
    for n in sky.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Emission Color"].default_value = (0.85, 0.88, 0.93, 1.0)
            n.inputs["Emission Strength"].default_value = 0.8
    add_box("sky", (cx, WALL_Y + 3.0, 1.8), (7.0, 0.1, 3.6), sky)

    # 折叠方桌（中心 0.4,0.9）+ 两把椅（近侧放袋子，远侧空）
    table = mat("table_mat", 0.60)
    tx, ty = TABLE_CENTER
    add_box("table_top", (tx, ty, 0.74), (1.55, 1.0, 0.05), table)
    for dx in (-0.65, 0.65):
        add_box(f"table_leg_{dx}", (tx + dx, ty, 0.37), (0.05, 0.85, 0.72), mat("leg_mat", 0.45))
    chair = mat("chair_mat", 0.55)
    for name, (px, py, rot) in (("chair_a", (0.42, -0.15, 0)), ("chair_b", (0.42, 1.95, 180))):
        add_box(f"{name}_seat", (px, py, 0.44), (0.45, 0.45, 0.05), chair)
        back_y = py - 0.20 if rot == 0 else py + 0.20
        add_box(f"{name}_back", (px, back_y, 0.75), (0.45, 0.05, 0.6), chair)
        for lx in (-0.18, 0.18):
            for ly in (-0.18, 0.18):
                add_box(f"{name}_leg_{lx}_{ly}", (px + lx, py + ly, 0.22), (0.04, 0.04, 0.44), chair)

    # 购物袋（近侧椅子上，开口，碗B 起点在里面）
    bag = mat("bag_mat", 0.68)
    bx, by, bz = BAG_POS
    add_box("bag_body", (bx, by, bz - 0.12), (0.34, 0.26, 0.28), bag)
    add_box("bag_rim", (bx, by, bz + 0.02), (0.36, 0.28, 0.03), mat("bag_rim_mat", 0.55))

    # 桌上 before 道具：暖瓶 + 碗A + 筷
    add_cyl("thermos", (tx - 0.30, ty - 0.15, 0.90), 0.055, 0.32, mat("thermos_mat", 0.50))
    add_cyl("bowl_a", BOWL_A, 0.09, 0.07, mat("bowl_mat", 0.78))
    add_box("chopsticks", (BOWL_A[0], BOWL_A[1] - 0.20, 0.775), (0.02, 0.20, 0.015), mat("chop_mat", 0.40))

    # 碗柜（右后背景）：柜体 + 碗摞 + 单灶锅 + 蒸汽
    cabx, caby = 2.05, 2.35
    cab = mat("cab_mat", 0.58)
    add_box("cabinet", (cabx, caby, 0.5), (1.1, 0.6, 1.0), cab)
    for i in range(4):
        add_cyl(f"stack_bowl_{i}", (cabx - 0.25, caby, 1.06 + i * 0.055),
                0.085, 0.05, mat("bowl_mat", 0.78))
    add_box("stove", (cabx + 0.22, caby, 1.02), (0.35, 0.35, 0.05), mat("stove_mat", 0.35))
    add_cyl("pot", (cabx + 0.22, caby, 1.16), 0.14, 0.20, mat("pot_mat", 0.48))
    steam = make_matte("steam_mat", 0.92)
    for n in steam.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Emission Color"].default_value = (0.95, 0.95, 0.97, 1.0)
            n.inputs["Emission Strength"].default_value = 0.7
    s1 = add_box("steam_1", (cabx + 0.20, caby, 1.45), (0.10, 0.02, 0.35), steam)
    s1.rotation_euler.z = math.radians(12)
    s2 = add_box("steam_2", (cabx + 0.28, caby, 1.75), (0.08, 0.02, 0.30), steam)
    s2.rotation_euler.z = math.radians(-10)
    add_cyl("mug", (cabx + 0.42, caby - 0.05, 1.08), 0.045, 0.10, mat("mug_mat", 0.75))

    # 碗B（新碗，main 驱动）
    bowl_b = add_cyl("bowl_b", BAG_POS, 0.09, 0.07, mat("bowl_mat", 0.78))
    return bowl_b


def add_lighting():
    world = bpy.data.worlds.new("previz_world13")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.30, 0.32, 0.36, 1.0)
            n.inputs[1].default_value = 0.75
    bpy.context.scene.world = world
    bpy.ops.object.light_add(type="AREA", location=((WIN_X0 + WIN_X1) / 2, WALL_Y + 1.6, 2.0))
    key = bpy.context.active_object
    key.data.energy = 650
    key.data.size = 3.2
    key.data.color = (0.85, 0.89, 0.95)
    key.rotation_euler = (math.radians(65), 0, math.radians(180))
    bpy.ops.object.light_add(type="AREA", location=(-1.4, -1.2, 2.1))
    fill = bpy.context.active_object
    fill.data.energy = 150
    fill.data.size = 2.6
    fill.data.color = (1.0, 0.85, 0.68)
    fill.rotation_euler = (math.radians(55), 0, math.radians(-35))


def ease(t):
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def rotate_world(arm_obj, bone_name, world_axis, angle_deg):
    pb = arm_obj.pose.bones.get(bone_name)
    if pb is None:
        return
    rest_q = pb.bone.matrix_local.to_quaternion()
    qw = Quaternion(Vector(world_axis).normalized(), math.radians(angle_deg))
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = rest_q.inverted() @ qw @ rest_q


def pose_xu(xu, f):
    """基础转身：f1-40 面向桌(+x, rot90)；f40-90 转向袋(rot135)；f90-140 回正放碗；
    f140-192 低头看两只碗。"""
    if f <= 40:
        spine, arm, elbow = 0.0, 0.0, 5.0
    elif f <= 90:
        k = ease((f - 40) / 50)
        spine = 8.0 * k
        arm = 45.0 * k
        elbow = 5.0 + 15.0 * k
    elif f <= 140:
        k = ease((f - 90) / 50)
        spine = 8.0 - 6.0 * k
        arm = 45.0 - 5.0 * k
        elbow = 20.0 + 55.0 * k
    else:
        spine, arm, elbow = 2.0, 15.0, 30.0

    for bname, ang in (("mixamorig:Spine", spine * 0.5),
                       ("mixamorig:Spine1", spine * 0.3)):
        rotate_world(xu, bname, (1, 0, 0), ang)
    for bname, sgn, frac in (("mixamorig:RightArm", 1, 1.0), ("mixamorig:LeftArm", -1, 0.35)):
        pb = xu.pose.bones.get(bname)
        if pb is None:
            continue
        rest_q = pb.bone.matrix_local.to_quaternion()
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = rest_q.inverted() @ Quaternion((0, 0, 1), math.radians(arm * sgn * frac)) @ rest_q
    rotate_world(xu, "mixamorig:RightForeArm", (0, 1, 0), elbow)
    rotate_world(xu, "mixamorig:LeftForeArm", (0, 1, 0), -elbow * 0.5)
    if f > 140:
        rotate_world(xu, "mixamorig:Head", (1, 0, 0), 14.0)


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    bowl_b = build_room()
    add_lighting()

    pre = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, "C05", "tex_mesh_v08_animated.glb"))
    new = [o for o in bpy.context.scene.objects if o not in pre]
    doomed, keep_new = set(), []
    for o in new:
        if o.type == "MESH" and "棱角球" in o.name:
            doomed.add(o)
        else:
            keep_new.append(o)
    for o in doomed:
        bpy.data.objects.remove(o, do_unlink=True)
    arms = [o for o in keep_new if o.type == "ARMATURE"] or \
           [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    xu = arms[-1]
    xu.rotation_mode = "XYZ"

    apply_matte = make_matte("char_matte13", 0.82)
    keep = ("floor", "wall", "frame", "curtain", "sky", "table", "leg", "chair", "thermos",
            "bowl", "chop", "stool", "cab", "stove", "pot", "steam", "mug", "ceil", "bag")
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        mnames = [m.name for m in o.data.materials] if o.data.materials else []
        if any(any(k in mn for k in keep) for mn in mnames):
            continue
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

    cam_data = bpy.data.cameras.new("previs_cam13")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.data.objects.new("previs_cam13", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    sp = Vector(CAM_START)
    ep = Vector(CAM_END)
    aim_table = Vector((-0.1, 1.0, 0.9))   # 偏左：把后墙左窗和桌面都带进画

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    frames_iter = [1, 45, 90, 115, 150, 190] if test_mode else range(1, N_FRAMES + 1)
    for f in frames_iter:
        t = ease((f - 1) / (N_FRAMES - 1))
        scene.frame_set(f)
        pose_xu(xu, f)

        # 基础 rot 65 面向桌微侧脸；f40-90 转 45° 面向椅子上的袋子；f90 起回正
        if f < 40:
            rot = 65.0
        elif f <= 90:
            rot = 65.0 + 45.0 * ease((f - 40) / 20) * (1.0 - ease((f - 75) / 15))
        else:
            rot = 65.0
        xu.location = (XU_POS[0], XU_POS[1], XU_Z)
        xu.rotation_euler = (0, 0, math.radians(rot))
        bpy.context.view_layer.update()

        # 碗B：f40 前在袋里；f40-75 移向右手；f75-140 跟手；f140 后落桌
        if f < 40:
            bowl_b.location = BAG_POS
        elif f <= 75:
            k = ease((f - 40) / 35)
            rh = xu.matrix_world @ xu.pose.bones["mixamorig:RightHand"].head
            bowl_b.location = Vector(BAG_POS).lerp(Vector((rh.x, rh.y, rh.z + 0.05)), k)
        elif f <= 140:
            rh = xu.matrix_world @ xu.pose.bones["mixamorig:RightHand"].head
            bowl_b.location = (rh.x, rh.y, rh.z + 0.05)
        else:
            bowl_b.location = BOWL_B_REST

        head = xu.matrix_world @ xu.pose.bones["mixamorig:Head"].head
        aim = head.lerp(aim_table, 0.30)   # 视线偏向桌面，两只碗入画
        cam.location = sp.lerp(ep, t)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs13] frame {f}/{N_FRAMES}", flush=True)

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
              "xu_pos": XU_POS, "bag": BAG_POS, "bowl_b_rest": BOWL_B_REST}
    with open(os.path.join(OUT_DIR, "previs13_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS13_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
