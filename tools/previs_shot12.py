# -*- coding: utf-8 -*-
"""白模预演：shot12「晒书的人」（第五章定场，朝北小屋，许宁抱书到窗前）。

剧本（五 L247）：下雨时墙角返潮，她把书垫高，周末再拎到有阳光的地方晒。
傍晚抱回来，书页里存着一层薄薄的暖，贴在她胸前。

时间轴（192f / 8s），按"变化前→过程→变化后"写清：
- f1-40   弯腰从地板书堆抱起一摞书（书堆在脚前，双手下探）
- f40-65  直起身，书抱在胸前
- f65-110 走向窗边书桌（root 平移 + 转向 180°，两三步）
- f110-155 把书放到窗台上（俯身放下，f150 书落在台面）
- f155-192 转身面向镜头方向，拿起一本书贴在胸前，抬头望窗光

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot12.py   (构图测试)
  blender.exe --background --python tools/previs_shot12.py                          (192 帧全量)
"""
import json
import math
import os

import bpy
from mathutils import Quaternion, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames12")

FPS = 24
N_FRAMES = 192
RES_X, RES_Y = 1280, 720

# 许宁走位（面向 -y 为 rot 0）
XU_START = (-0.7, 0.7)     # 地板书堆旁
XU_END = (0.55, 2.30)      # 窗前台前
XU_Z = 0.78                # 走/站版骨架原点高度（探针实测）

WALL_Y = 3.2
WIN_X0, WIN_X1 = 0.05, 1.55
WIN_Z0, WIN_Z1 = 1.05, 2.25

CAM_START = (-2.35, -2.10, 1.48)
CAM_END = (-1.90, -1.55, 1.42)
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


MATS = {}
def mat(key, shade):
    if key not in MATS:
        MATS[key] = make_matte(key, shade)
    return MATS[key]


def build_room():
    """E08 朝北小屋：床靠左墙、后墙带北窗、窗下书桌、地板书堆、墙角返潮。"""
    wall = mat("wall_mat", 0.62)
    add_box("floor", (0, 0, -0.05), (7.0, 8.0, 0.1), mat("floor_mat", 0.42))
    add_box("ceiling", (0, 0, 2.7), (7.0, 8.0, 0.1), mat("ceil_mat", 0.55))
    add_box("left_wall", (-3.2, 0, 1.35), (0.12, 8.0, 2.7), wall)
    add_box("right_wall", (3.2, 0, 1.35), (0.12, 8.0, 2.7), wall)

    # 后墙（带窗洞）
    add_box("wall_back_l", (-1.575, WALL_Y, 1.35), (3.25, 0.12, 2.7), wall)
    add_box("wall_back_r", (2.375, WALL_Y, 1.35), (1.65, 0.12, 2.7), wall)
    add_box("wall_back_top", ((WIN_X0 + WIN_X1) / 2, WALL_Y, (WIN_Z1 + 2.7) / 2),
            (WIN_X1 - WIN_X0, 0.12, 2.7 - WIN_Z1), wall)
    add_box("wall_back_bot", ((WIN_X0 + WIN_X1) / 2, WALL_Y, WIN_Z0 / 2),
            (WIN_X1 - WIN_X0, 0.12, WIN_Z0), wall)
    # 窗框 + 十字 + 薄白纱窗（半透）
    frame = mat("frame_mat", 0.50)
    cx = (WIN_X0 + WIN_X1) / 2
    cz = (WIN_Z0 + WIN_Z1) / 2
    add_box("win_f_l", (WIN_X0, WALL_Y - 0.03, cz), (0.07, 0.08, WIN_Z1 - WIN_Z0), frame)
    add_box("win_f_r", (WIN_X1, WALL_Y - 0.03, cz), (0.07, 0.08, WIN_Z1 - WIN_Z0), frame)
    add_box("win_f_h", (cx, WALL_Y - 0.03, WIN_Z1), (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    add_box("win_f_b", (cx, WALL_Y - 0.03, WIN_Z0), (WIN_X1 - WIN_X0 + 0.1, 0.08, 0.07), frame)
    add_box("win_f_m", (cx, WALL_Y - 0.03, cz), (0.05, 0.08, WIN_Z1 - WIN_Z0), frame)
    curtain = make_matte("curtain_mat", 0.86)
    add_box("curtain", (cx - (WIN_X1 - WIN_X0) * 0.32, WALL_Y - 0.10, cz),
            (0.34, 0.02, WIN_Z1 - WIN_Z0 + 0.1), curtain)

    # 窗外：阴天柔光板 + 对面楼剪影
    sky = make_matte("sky_mat", 0.85)
    for n in sky.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Emission Color"].default_value = (0.82, 0.86, 0.92, 1.0)
            n.inputs["Emission Strength"].default_value = 0.8
    add_box("sky", (cx, WALL_Y + 3.0, 1.8), (7.0, 0.1, 3.6), sky)
    add_box("bld_out", (cx + 1.2, WALL_Y + 1.6, 1.6), (1.8, 0.3, 1.6), mat("sil_mat", 0.55))

    # 窗下书桌 + 台灯 + 水杯 + 电热水壶
    desk = mat("desk_mat", 0.58)
    add_box("desk_top", (cx, WALL_Y - 0.45, 0.78), (1.7, 0.65, 0.06), desk)
    for dx in (-0.75, 0.75):
        add_box(f"desk_leg_{dx}", (cx + dx, WALL_Y - 0.45, 0.39), (0.06, 0.5, 0.78), desk)
    add_box("desk_drawer", (cx, WALL_Y - 0.40, 0.62), (1.5, 0.45, 0.3), desk)
    add_box("lamp_base", (cx + 0.55, WALL_Y - 0.5, 0.83), (0.16, 0.16, 0.04), mat("metal_mat", 0.48))
    add_box("lamp_arm", (cx + 0.55, WALL_Y - 0.5, 1.02), (0.035, 0.035, 0.36), mat("metal_mat", 0.48))
    add_box("lamp_head", (cx + 0.50, WALL_Y - 0.55, 1.22), (0.18, 0.18, 0.12), mat("metal_mat", 0.48))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.10, location=(cx - 0.45, WALL_Y - 0.45, 0.86))
    mug = bpy.context.active_object
    mug.name = "mug"
    mug.data.materials.append(mat("mug_mat", 0.75))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.075, depth=0.24, location=(cx - 0.65, WALL_Y - 0.45, 0.93))
    kettle = bpy.context.active_object
    kettle.name = "kettle"
    kettle.data.materials.append(mat("kettle_mat", 0.35))

    # 床（左墙，单人）
    bed = mat("bed_mat", 0.66)
    add_box("bed_frame", (-2.55, 0.8, 0.35), (1.15, 2.1, 0.25), mat("bedframe_mat", 0.50))
    add_box("bed_mattress", (-2.55, 0.8, 0.55), (1.1, 2.05, 0.18), bed)
    add_box("bed_quilt", (-2.55, 0.55, 0.68), (1.08, 1.5, 0.12), mat("quilt_mat", 0.74))
    add_box("bed_pillow", (-2.55, 1.65, 0.68), (0.7, 0.4, 0.12), mat("pillow_mat", 0.80))
    add_box("bed_head", (-2.55, 1.92, 0.85), (1.15, 0.08, 0.9), mat("bedframe_mat", 0.50))

    # 地板书堆（许宁脚前，垫砖木板）
    add_box("brick_a", (-0.95, 1.05, 0.06), (0.18, 0.12, 0.12), mat("brick_mat", 0.45))
    add_box("brick_b", (-0.35, 1.05, 0.06), (0.18, 0.12, 0.12), mat("brick_mat", 0.45))
    add_box("raise_board", (-0.65, 1.05, 0.14), (0.85, 0.45, 0.04), mat("board_mat", 0.52))
    for i in range(5):
        add_box(f"pile_book_{i}", (-0.65, 1.05, 0.19 + i * 0.055),
                (0.62 - 0.04 * (i % 2), 0.36, 0.05), mat(f"pile_mat_{i % 3}", 0.42 + 0.11 * (i % 3)))
    # 桌腿旁再一小摞
    for i in range(3):
        add_box(f"side_book_{i}", (1.75, WALL_Y - 0.55, 0.03 + i * 0.055),
                (0.4, 0.28, 0.05), mat(f"pile_mat_{(i + 1) % 3}", 0.42 + 0.11 * ((i + 1) % 3)))

    # 墙角返潮痕（右后墙脚深色块）
    damp = make_matte("damp_mat", 0.30)
    add_box("damp_patch", (2.45, WALL_Y - 0.065, 0.22), (1.1, 0.02, 0.42), damp)


def add_lighting():
    world = bpy.data.worlds.new("previz_world12")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.30, 0.32, 0.36, 1.0)   # 阴天柔环境
            n.inputs[1].default_value = 0.75
    bpy.context.scene.world = world
    # 窗外主光：冷白柔光（北向天光）
    bpy.ops.object.light_add(type="AREA", location=((WIN_X0 + WIN_X1) / 2, WALL_Y + 1.6, 2.0))
    key = bpy.context.active_object
    key.data.energy = 700
    key.data.size = 3.2
    key.data.color = (0.82, 0.87, 0.95)
    key.rotation_euler = (math.radians(65), 0, math.radians(180))
    # 镜头侧暖色补光（很弱，拉开冷暖层次）
    bpy.ops.object.light_add(type="AREA", location=(-1.6, -1.2, 2.1))
    fill = bpy.context.active_object
    fill.data.energy = 160
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


STRIP_TARGETS = (
    'pose.bones["mixamorig:RightArm"].rotation_quaternion',
    'pose.bones["mixamorig:RightForeArm"].rotation_quaternion',
    'pose.bones["mixamorig:LeftArm"].rotation_quaternion',
    'pose.bones["mixamorig:LeftForeArm"].rotation_quaternion',
    'pose.bones["mixamorig:Head"].rotation_quaternion',
    'pose.bones["mixamorig:Spine"].rotation_quaternion',
    'pose.bones["mixamorig:Spine1"].rotation_quaternion',
    'pose.bones["mixamorig:Spine2"].rotation_quaternion',
)


def strip_channels():
    removed = []
    for ac in bpy.data.actions:
        for layer in ac.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in list(bag.fcurves):
                        if fc.data_path in STRIP_TARGETS:
                            bone = fc.data_path.split('"')[1]
                            bag.fcurves.remove(fc)
                            removed.append(f"{ac.name}:{bone}")
    return removed


def pose_xu(xu, f):
    """时间轴姿态（探针实测 C05：右臂前摆 (0,0,z)+、左臂前摆 (0,0,z)-、
    肘部内收右臂 (0,y,0)+ 左臂 (0,y,0)-、俯身 Spine (x,0,0)+）。"""
    if f <= 40:                      # 弯腰下探
        k = ease(f / 40)
        spine = 30.0 * k
        arm = 25.0 * k               # 手臂向前下伸
        elbow = 10.0 * k
    elif f <= 65:                    # 直身抱起
        k = ease((f - 40) / 25)
        spine = 30.0 - 24.0 * k      # 30→6
        arm = 25.0 + 27.0 * k        # 25→52 抱至胸前
        elbow = 10.0 + 25.0 * k      # 10→35 小屈肘（大了手会翻到脸前）
    elif f <= 110:                   # 行走：书贴胸前
        spine, arm, elbow = 6.0, 52.0, 35.0
    elif f <= 155:                   # 俯身放书到窗台
        k = ease((f - 110) / 45)
        spine = 6.0 + 20.0 * math.sin(math.pi * k)   # 6→26→6
        arm = 52.0 + 8.0 * k
        elbow = 35.0 - 20.0 * k
    else:                            # 窗前拿一本书贴在胸前（背影，手臂回收贴体）
        spine, arm, elbow = 4.0, 30.0, 30.0

    for bname, ang in (("mixamorig:Spine", spine * 0.4),
                       ("mixamorig:Spine1", spine * 0.35),
                       ("mixamorig:Spine2", spine * 0.25)):
        rotate_world(xu, bname, (1, 0, 0), ang)
    # 双臂前摆（右 z+ / 左 z-）
    for bname, sgn in (("mixamorig:RightArm", 1), ("mixamorig:LeftArm", -1)):
        pb = xu.pose.bones.get(bname)
        if pb is None:
            continue
        rest_q = pb.bone.matrix_local.to_quaternion()
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = rest_q.inverted() @ Quaternion((0, 0, 1), math.radians(arm * sgn)) @ rest_q
    # 肘部内收（右 y+ / 左 y-，镜像）
    for bname, sgn in (("mixamorig:RightForeArm", 1), ("mixamorig:LeftForeArm", -1)):
        rotate_world(xu, bname, (0, 1, 0), elbow * sgn)
    # 头部（面向 +y 窗前）：f155-170 低头看书，f171-192 抬眼望窗光
    # 世界 x 轴旋转对 +y 面向：-x=低头（头顶向 +y），+x=抬头
    if 155 < f <= 170:
        rotate_world(xu, "mixamorig:Head", (1, 0, 0), -12.0)
    elif f > 170:
        rotate_world(xu, "mixamorig:Head", (1, 0, 0), 8.0)


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    build_room()
    add_lighting()

    pre = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, "C05", "tex_mesh_v08_animated.glb"))
    new = [o for o in bpy.context.scene.objects if o not in pre]
    doomed = set()
    keep_new = []
    for o in new:
        if o.type == "MESH" and "棱角球" in o.name:
            doomed.add(o)
        else:
            keep_new.append(o)
    for o in doomed:
        bpy.data.objects.remove(o, do_unlink=True)
    new = keep_new
    arms = [o for o in new if o.type == "ARMATURE"] or \
           [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    xu = arms[-1]
    xu.rotation_mode = "XYZ"

    print("[previs12] actions:", [ac.name for ac in bpy.data.actions], flush=True)
    removed = strip_channels()
    print("[previs12] stripped:", removed, flush=True)

    # 书摞道具：f30 出现在手间；f150 落窗台变成台面书摞；f160 起一本单书贴胸
    bundle = add_box("book_bundle", (0, 0, -1), (0.34, 0.22, 0.16), mat("bundle_mat", 0.55))
    single = add_box("single_book", (0, 0, -1), (0.20, 0.14, 0.035), mat("single_mat", 0.50))

    apply_matte = make_matte("char_matte12", 0.82)
    keep = ("floor_mat", "wall_mat", "frame_mat", "curtain_mat", "sky_mat", "sil_mat",
            "desk_mat", "metal_mat", "mug_mat", "kettle_mat", "bed", "quilt", "pillow",
            "brick", "board", "pile_mat", "damp_mat", "ceil_mat", "bundle_mat", "single_mat")
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

    cam_data = bpy.data.cameras.new("previs_cam12")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.context.objects.new if False else bpy.data.objects.new("previs_cam12", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    sp = Vector(CAM_START)
    ep = Vector(CAM_END)

    # 不挂任何 action：全程手动姿态（挂走循环会让静立阶段腿部持续踏步）

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    frames_iter = [1, 30, 55, 90, 130, 160, 190] if test_mode else range(1, N_FRAMES + 1)
    for f in frames_iter:
        t = ease((f - 1) / (N_FRAMES - 1))
        scene.frame_set(f)
        pose_xu(xu, f)

        # root 走位：f65-110 走到窗前；f155-175 转回身
        if f < 65:
            pos = Vector((XU_START[0], XU_START[1], XU_Z))
            rot = 0.0
        elif f <= 110:
            k = ease((f - 65) / 45)
            pos = Vector((XU_START[0], XU_START[1], XU_Z)).lerp(
                Vector((XU_END[0], XU_END[1], XU_Z)), k)
            rot = 180.0 * ease((f - 65) / 15)   # 前几步内转身
        elif f <= 155:
            pos = Vector((XU_END[0], XU_END[1], XU_Z))
            rot = 180.0
        else:
            # 不转身：留在窗前，背影 3/4 对镜头，拿一本书贴胸望窗光
            pos = Vector((XU_END[0], XU_END[1], XU_Z))
            rot = 180.0
        # 行走小起伏
        if 65 < f <= 110:
            pos.z += 0.015 * abs(math.sin(2 * math.pi * (f - 65) / 16.0))
        xu.location = pos
        xu.rotation_euler = (0, 0, math.radians(rot))
        bpy.context.view_layer.update()   # 刷新矩阵后再读骨点

        # 书摞跟随双手中点
        rh = xu.matrix_world @ xu.pose.bones["mixamorig:RightHand"].head
        lh = xu.matrix_world @ xu.pose.bones["mixamorig:LeftHand"].head
        mid = (rh + lh) / 2
        if 30 <= f < 150:
            bundle.location = (mid.x, mid.y - 0.12 if rot % 360 < 90 else mid.y + 0.12, mid.z + 0.02)
            single.location = (0, 0, -1)
        elif f >= 160:
            # 一摞留在窗台，单书贴胸
            bundle.location = (XU_END[0] + 0.15, WALL_Y - 0.48, 0.87)
            single.location = (mid.x, mid.y, mid.z - 0.04)
        else:
            bundle.location = (0, 0, -1)
            single.location = (0, 0, -1)

        head = xu.matrix_world @ xu.pose.bones["mixamorig:Head"].head
        cam.location = sp.lerp(ep, t)
        cam.location.x += 0.010 * math.sin(2.0 * math.pi * f / 53.0)
        cam.location.z += 0.008 * math.sin(2.0 * math.pi * f / 41.0)
        cam.rotation_euler = (head - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs12] frame {f}/{N_FRAMES}", flush=True)

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS,
              "xu_start": XU_START, "xu_end": XU_END, "cam": [CAM_START, CAM_END]}
    with open(os.path.join(OUT_DIR, "previs12_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS12_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
