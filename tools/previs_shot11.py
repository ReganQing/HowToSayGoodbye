# -*- coding: utf-8 -*-
"""白模预演：shot11「夜里的电话」（宿舍夜戏，许宁贴窗站着打电话）。

剧本（四 L243）：晚上，她给妈妈打电话，说了很久。她说起宿舍楼下的猫，
又把白天走过的路细细描述了一遍，连照片里那半瓶汽水也没有漏掉。

时间轴（192f / 8s）：
- 全程 Idle_TalkingPhone_Loop（站姿打电话：手机贴右耳，伴随轻微说话手势）
- 许宁站在窗前桌边，面向镜头偏侧，台灯暖光，窗外深蓝夜色
- 镜头缓推 + 轻微手持晃动

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot11.py   (构图测试)
  blender.exe --background --python tools/previs_shot11.py                          (192 帧全量)
"""
import json
import math
import os

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames11")

FPS = 24
DURATION_S = 8
N_FRAMES = FPS * DURATION_S
RES_X, RES_Y = 1280, 720

XU_POS = (0.55, 2.0, 0.78)    # 站姿动画 glb 骨架原点在脚上方 0.78（与走/站版一致）
XU_ROT = -12.0                # 身体微侧向桌/窗

CAM_START_POS = (-0.25, -1.7, 1.50)
CAM_END_POS = (0.15, -1.15, 1.42)
CAM_LENS = 35

WALL_Y = 3.2
WIN_X0, WIN_X1 = -0.8, 0.8
WIN_Z0, WIN_Z1 = 1.0, 2.2


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


MATS = {}
def mat(key, shade):
    if key not in MATS:
        MATS[key] = make_matte(key, shade)
    return MATS[key]


def build_dorm():
    """程序化宿舍：地板/带窗洞后墙/右墙/双层床/书架/书桌台灯/脸盆/窗外夜色。"""
    wall = mat("wall_mat", 0.62)
    add_box("floor", (0, 0, -0.05), (7.0, 8.0, 0.1), mat("floor_mat", 0.40))
    add_box("ceiling", (0, 0, 2.6), (7.0, 8.0, 0.1), mat("ceil_mat", 0.55))
    add_box("left_wall", (-3.2, 0, 1.3), (0.12, 8.0, 2.6), wall)
    add_box("right_wall", (3.2, 0, 1.3), (0.12, 8.0, 2.6), wall)

    # 后墙（带窗洞）：窗 x -0.8~0.8，z 1.0~2.2
    add_box("wall_back_l", (-2.0, WALL_Y, 1.3), (2.4, 0.12, 2.6), wall)
    add_box("wall_back_r", (2.0, WALL_Y, 1.3), (2.4, 0.12, 2.6), wall)
    add_box("wall_back_top", (0, WALL_Y, (WIN_Z1 + 2.6) / 2), (1.6, 0.12, 2.6 - WIN_Z1), wall)
    add_box("wall_back_bot", (0, WALL_Y, WIN_Z0 / 2), (1.6, 0.12, WIN_Z0), wall)
    # 窗框 + 十字
    frame = mat("frame_mat", 0.50)
    add_box("win_f_l", (WIN_X0, WALL_Y - 0.03, (WIN_Z0 + WIN_Z1) / 2), (0.07, 0.08, WIN_Z1 - WIN_Z0), frame)
    add_box("win_f_r", (WIN_X1, WALL_Y - 0.03, (WIN_Z0 + WIN_Z1) / 2), (0.07, 0.08, WIN_Z1 - WIN_Z0), frame)
    add_box("win_f_h", (0, WALL_Y - 0.03, WIN_Z1), (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    add_box("win_f_b", (0, WALL_Y - 0.03, WIN_Z0), (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    add_box("win_f_m", (0, WALL_Y - 0.03, (WIN_Z0 + WIN_Z1) / 2), (0.05, 0.08, WIN_Z1 - WIN_Z0), frame)

    # 窗外夜色：深蓝发光平面 + 树影球 + 远处教学楼剪影块
    night = make_matte("night_mat", 0.10)
    for n in night.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Emission Color"].default_value = (0.10, 0.16, 0.38, 1.0)
            n.inputs["Emission Strength"].default_value = 0.55
    add_box("night_sky", (0, WALL_Y + 3.0, 1.8), (7.0, 0.1, 3.6), night)
    tree_mat = mat("sil_tree_mat", 0.16)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.85, location=(-0.2, WALL_Y + 1.2, 2.1))
    t = bpy.context.active_object
    t.name = "night_tree"
    t.scale = (0.45, 0.6, 1.1)
    bpy.ops.object.transform_apply(scale=True)
    t.data.materials.append(tree_mat)
    add_box("night_bld", (1.8, WALL_Y + 2.0, 1.3), (1.6, 0.3, 1.8), mat("sil_bld_mat", 0.20))

    # 双层床（右墙）
    bed = mat("bed_mat", 0.66)
    metal = mat("metal_mat", 0.48)
    for px in (1.9, 3.0):
        for py in (0.8, 2.8):
            add_box(f"bed_post_{px}_{py}", (px, py, 1.15), (0.07, 0.07, 2.3), metal)
    add_box("bed_lower", (2.45, 1.8, 0.55), (1.2, 2.2, 0.18), bed)
    add_box("bed_upper", (2.45, 1.8, 1.65), (1.2, 2.2, 0.14), bed)
    add_box("bed_pillow", (2.45, 2.6, 0.68), (0.8, 0.4, 0.12), mat("pillow_mat", 0.78))
    # 书架 + 书（右墙上方）
    add_box("shelf", (3.05, 1.8, 2.05), (0.25, 1.6, 0.06), mat("shelf_mat", 0.58))
    for i in range(8):
        add_box(f"book_{i}", (3.02, 1.15 + i * 0.16, 2.22), (0.18, 0.09, 0.28 + 0.04 * (i % 3)),
                mat(f"book_mat_{i % 3}", 0.40 + 0.12 * (i % 3)))

    # 书桌（窗下偏左）+ 台灯 + 书堆 + 保温杯
    desk = mat("desk_mat", 0.60)
    add_box("desk_top", (-0.1, 2.85, 0.78), (1.7, 0.62, 0.06), desk)
    for dx in (-0.8, 0.6):
        add_box(f"desk_leg_{dx}", (dx, 2.85, 0.39), (0.06, 0.5, 0.78), desk)
    add_box("desk_drawer", (-0.1, 2.9, 0.62), (1.5, 0.45, 0.3), desk)
    # 台灯：底座 + 杆 + 发光灯罩（暖光源在 add_lighting 里）
    add_box("lamp_base", (-0.45, 2.85, 0.83), (0.16, 0.16, 0.04), metal)
    add_box("lamp_arm", (-0.45, 2.85, 1.02), (0.035, 0.035, 0.36), metal)
    shade_mat = make_matte("lamp_shade_mat", 0.85)
    for n in shade_mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Emission Color"].default_value = (1.0, 0.75, 0.42, 1.0)
            n.inputs["Emission Strength"].default_value = 1.6
    add_box("lamp_shade", (-0.45, 2.80, 1.24), (0.20, 0.20, 0.13), shade_mat)
    # 书堆
    for i in range(4):
        add_box(f"stack_a_{i}", (0.28, 2.85, 0.83 + i * 0.045), (0.34, 0.24, 0.04),
                mat(f"stack_mat_{i % 2}", 0.50 + 0.14 * (i % 2)))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.22, location=(0.62, 2.85, 0.92))
    cup = bpy.context.active_object
    cup.name = "thermos"
    cup.data.materials.append(mat("cup_mat", 0.35))

    # 脸盆架（左前角）
    add_box("basin_stand", (-2.5, 1.5, 0.45), (0.4, 0.4, 0.9), metal)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.10, location=(-2.5, 1.5, 0.95))
    basin = bpy.context.active_object
    basin.name = "basin"
    basin.data.materials.append(mat("basin_mat", 0.72))


def add_lighting():
    world = bpy.data.worlds.new("previz_world11")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.10, 0.11, 0.16, 1.0)   # 夜环境
            n.inputs[1].default_value = 0.55
    bpy.context.scene.world = world
    # 台灯主光源（暖黄，小范围）
    bpy.ops.object.light_add(type="POINT", location=(-0.45, 2.72, 1.22))
    lamp = bpy.context.active_object
    lamp.data.energy = 260
    lamp.data.color = (1.0, 0.72, 0.40)
    lamp.data.shadow_soft_size = 0.35
    # 台灯引向人物的暖色主光
    bpy.ops.object.light_add(type="AREA", location=(0.7, 1.6, 1.9))
    key = bpy.context.active_object
    key.data.energy = 500
    key.data.size = 2.2
    key.data.color = (1.0, 0.78, 0.52)
    key.rotation_euler = (math.radians(60), math.radians(-15), math.radians(140))
    # 窗外冷蓝月光/路灯光
    bpy.ops.object.light_add(type="AREA", location=(0, 4.6, 2.2))
    moon = bpy.context.active_object
    moon.data.energy = 450
    moon.data.size = 3.0
    moon.data.color = (0.45, 0.55, 0.90)
    moon.rotation_euler = (math.radians(75), 0, math.radians(180))


def ease(t):
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def find_actions():
    acts = {}
    for ac in bpy.data.actions:
        if ac.name.lower() == "animation_1":
            acts["phone"] = ac
    return acts


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    build_dorm()
    add_lighting()

    pre = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, "C05", "tex_mesh_v08_phone.glb"))
    new = [o for o in bpy.context.scene.objects if o not in pre]
    for o in new:
        if o.type == "MESH" and "棱角球" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE" and o in new] or \
           [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    xu = arms[-1]
    xu.rotation_mode = "XYZ"
    xu.location = XU_POS
    xu.rotation_euler = (0, 0, math.radians(XU_ROT))
    bpy.context.view_layer.update()

    acts = find_actions()
    print(f"[previs11] actions: {list(acts.keys())}", flush=True)

    apply_matte = make_matte("char_matte11", 0.82)
    keep = ("floor_mat", "wall_mat", "frame_mat", "night_mat", "sil_", "bed_mat", "metal_mat",
            "pillow_mat", "shelf_mat", "book_mat", "desk_mat", "lamp_", "stack_mat", "cup_mat",
            "basin_mat", "ceil_mat")
    for o in mesh_objects():
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

    cam_data = bpy.data.cameras.new("previs_cam11")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.data.objects.new("previs_cam11", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    sp = Vector(CAM_START_POS)
    ep = Vector(CAM_END_POS)

    st = {"key": None}

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    frames_iter = [1, 60, 120, 190] if test_mode else range(1, N_FRAMES + 1)
    for f in frames_iter:
        t = ease((f - 1) / (N_FRAMES - 1))
        if "phone" in acts and st.get("key") != "phone":
            xu.animation_data.action = acts["phone"]
            st["key"] = "phone"

        scene.frame_set(f)
        head = xu.matrix_world @ xu.pose.bones["mixamorig:Head"].head
        cam.location = sp.lerp(ep, t)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (head - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs11] frame {f}/{N_FRAMES}", flush=True)

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS}
    with open(os.path.join(OUT_DIR, "previs11_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS11_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
