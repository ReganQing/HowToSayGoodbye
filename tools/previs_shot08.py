# -*- coding: utf-8 -*-
"""白模预演：南方街道 shot08「老照片」（叔叔掏手机给许宁看）。

剧本（四 L235）：他掏出手机，翻出一张老照片。几个人围着矮桌吃饭，
爸爸坐在边上，笑得眼睛眯起来。

走位时间轴（192f / 8s，紧接 shot07 结尾站位：叔叔 x=1.45、许宁 x=0.55，y=1.0）：
- f1-15   叔叔右臂从身侧向前下方探（进口袋掏手机），f15-35 收回，手持手机于腹前
- f35-65  叔叔抬前臂把手机举到胸前，屏幕转向许宁，头微低看屏幕
- f45-95  许宁向叔叔侧迈半步（x 0.55→0.95），上身前倾凑近看屏幕
- f95-192 两人保持同看屏幕的姿势（轻微呼吸），镜头缓推
- 叔叔身体微转向许宁（rot 180→192），许宁身体微转（rot 180→170）

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot08.py   (构图测试)
  blender.exe --background --python tools/previs_shot08.py                          (192 帧全量)
"""
import json
import math
import os

import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames08")

FPS = 24
DURATION_S = 8
N_FRAMES = FPS * DURATION_S
RES_X, RES_Y = 1280, 720

ARM_Z = 0.78

# ---- 时间轴 ----
F_POCKET = 8                 # 开始探手进口袋
F_POCKET_END = 20            # 掏到，手持机于腹前
F_RAISE = 35                 # 开始举手机到胸前
F_RAISE_END = 65             # 举到位
F_XU_STEP = 45               # 许宁开始迈步靠近
F_XU_STEP_END = 95           # 靠近到位
F_END = N_FRAMES

STAND_Y = 1.0
UNCLE_X = 1.45
XU_X0 = 0.55
XU_X1 = 0.95                 # 靠近后的站位（仍在叔叔右侧，留出看屏幕的距离）
UNCLE_ROT0 = 180.0
UNCLE_ROT1 = 192.0           # 微转向许宁一侧
XU_ROT0 = 180.0
XU_ROT1 = 170.0

CAM_START_POS = (0.0, 3.5, 1.52)
CAM_END_POS = (0.3, 2.85, 1.44)
CAM_LENS = 40                # 比 shot07 更近的中景
TGT_OFFSET = (0.55, 0.0, -0.05)   # 取景偏右，把快餐店带进画面右侧


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def make_matte(name="previz_matte08", shade=0.78):
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


def build_street():
    """与 shot07 同一条街（简化版：人行道 + 店面 + 树 + 电动车），延续空间感。"""
    road_mat = make_matte("road_matte", 0.38)
    walk_mat = make_matte("walk_matte", 0.74)
    wall = make_matte("shop_matte", 0.80)
    add_box("road", (-4.9, 0, -0.11), (8.2, 30.0, 0.2), road_mat)
    add_box("sidewalk", (1.5, 0, -0.06), (4.6, 30.0, 0.12), walk_mat)
    add_box("shop_a", (5.2, -5.0, 1.7), (2.4, 6.0, 3.4), wall)
    add_box("shop_b", (5.2, 7.0, 1.7), (2.4, 6.0, 3.4), wall)
    add_box("awning_a", (3.9, -5.0, 2.6), (0.9, 6.0, 0.08), wall)
    add_box("awning_b", (3.9, 7.0, 2.6), (0.9, 6.0, 0.08), wall)

    pre = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, "E05", "tex_mesh.glb"))
    for o in [o for o in bpy.context.scene.objects if o not in pre]:
        if o.type == "MESH":
            o.scale = (3.2, 2.0, 3.4)
            o.location = (6.68, 1.0, 1.80)
    bpy.context.view_layer.update()

    trunk_mat = make_matte("trunk_matte", 0.5)
    leaf_mat = make_matte("leaf_matte", 0.62)
    for i, (tx, ty) in enumerate(((2.8, -3.5), (2.6, 5.8))):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.13, depth=2.6, location=(tx, ty, 1.3))
        t = bpy.context.active_object
        t.name = f"trunk_{i}"
        t.data.materials.append(trunk_mat)
        for j, (dz, r) in enumerate(((2.9, 1.05), (3.5, 0.75))):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(tx + 0.2 * j, ty, dz))
            s = bpy.context.active_object
            s.name = f"canopy_{i}_{j}"
            s.scale = (1.0, 1.0, 0.75)
            bpy.ops.object.transform_apply(scale=True)
            s.data.materials.append(leaf_mat)

    bike_mat = make_matte("bike_matte", 0.45)
    for i, by in enumerate((-2.5, 4.2)):
        bx = -0.35
        add_box(f"scooter_body_{i}", (bx, by, 0.5), (0.28, 1.15, 0.45), bike_mat)
        add_box(f"scooter_post_{i}", (bx, by - 0.45, 0.95), (0.08, 0.08, 0.6), bike_mat)
        for wy in (by - 0.5, by + 0.5):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.08,
                                                location=(bx, wy, 0.22),
                                                rotation=(0, math.radians(90), 0))
            w = bpy.context.active_object
            w.name = f"scooter_wheel_{i}_{wy:.1f}"
            w.data.materials.append(bike_mat)


def add_lighting():
    world = bpy.data.worlds.new("previz_world08")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.52, 0.47, 0.38, 1.0)
            n.inputs[1].default_value = 0.55
    bpy.context.scene.world = world
    bpy.ops.object.light_add(type="AREA", location=(-5.0, 2.0, 8.0))
    key = bpy.context.active_object
    key.data.energy = 1600
    key.data.size = 6.0
    key.data.color = (1.0, 0.83, 0.60)
    key.rotation_euler = (math.radians(20), math.radians(-25), math.radians(-40))
    bpy.ops.object.light_add(type="AREA", location=(3.0, 6.0, 5.0))
    fill = bpy.context.active_object
    fill.data.energy = 700
    fill.data.size = 5.0
    fill.data.color = (0.75, 0.85, 1.0)
    fill.rotation_euler = (math.radians(55), 0, math.radians(160))


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


def uncle_arm_pose(arm_obj, t):
    """叔叔右臂三段：0=垂放 → 0.5=腹前持机 → 1=胸前举起给许宁看。
    轴向（探针实测）：RightArm 绕 (0,1,0) -90=垂放/0=侧平举；绕 (0,0,1)+=前摆。"""
    pb = arm_obj.pose.bones.get("mixamorig:RightArm")
    if pb is None:
        return
    rest_q = pb.bone.matrix_local.to_quaternion()
    inv = rest_q.inverted()

    if t <= 0.5:
        k = ease(t / 0.5)
        y_ang = -90.0 + 45.0 * k        # -90 → -45（从垂放到抬离体侧）
        z_ang = 30.0 * k                # 0 → +30（向前探）
        elbow = 8.0 + 52.0 * k          # 8 → 60（屈肘，手落腹前）
    else:
        k = ease((t - 0.5) / 0.5)
        y_ang = -45.0 + 25.0 * k        # -45 → -20
        z_ang = 30.0 + 15.0 * k         # +30 → +45（举到胸前）
        elbow = 60.0 + 15.0 * k         # 60 → 75

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


def uncle_arm_t(f):
    """f1-15 垂放（探手前），f15-35 腹前，f35-65 举起，之后保持。"""
    if f < F_POCKET_END:
        return 0.0
    if f < F_RAISE:
        return 0.5
    if f < F_RAISE_END:
        return 0.5 + 0.5 * ease((f - F_RAISE) / (F_RAISE_END - F_RAISE))
    return 1.0


def strip_arm_channels(acts):
    targets = (
        'pose.bones["mixamorig:RightArm"].rotation_quaternion',
        'pose.bones["mixamorig:RightForeArm"].rotation_quaternion',
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


def import_character(cid, glb, pos, rot_z):
    pre = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, cid, glb))
    new = [o for o in bpy.context.scene.objects if o not in pre]
    for o in new:
        if o.type == "MESH" and "棱角球" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE" and o in new] or \
           [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    arm_obj = arms[-1]
    arm_obj.rotation_mode = "XYZ"
    arm_obj.location = pos
    arm_obj.rotation_euler = (0, 0, math.radians(rot_z))
    bpy.context.view_layer.update()
    return arm_obj


def find_actions():
    acts = {}
    walk = idle = None
    for ac in bpy.data.actions:
        if ac.name.lower() == "animation_1":
            walk = ac
        elif ac.name.lower() == "animation_2":
            idle = ac
    if walk and idle and (idle.frame_range[1] - idle.frame_range[0]) < \
            (walk.frame_range[1] - walk.frame_range[0]):
        walk, idle = idle, walk
    if walk:
        acts["walk"] = walk
    if idle:
        acts["idle"] = idle
    return acts


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    build_street()
    add_lighting()

    uncle = import_character("C14", "tex_mesh_v08_animated.glb",
                             (UNCLE_X, STAND_Y, ARM_Z), UNCLE_ROT0)
    xu = import_character("C05", "tex_mesh_v08_animated.glb",
                          (XU_X0, STAND_Y, ARM_Z), XU_ROT0)
    acts_u = find_actions()
    print(f"[previs08] actions: {list(acts_u.keys())}", flush=True)
    removed = strip_arm_channels(acts_u)
    print(f"[previs08] stripped arm channels: {removed}", flush=True)

    apply_matte = make_matte("char_matte08", 0.82)
    for o in mesh_objects():
        if o.name.startswith(("scooter_", "trunk_", "canopy_")):
            continue
        if "road_matte" not in o.name and "walk_matte" not in o.name:
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

    cam_data = bpy.data.cameras.new("previs_cam08")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.data.objects.new("previs_cam08", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    sp = Vector(CAM_START_POS)
    ep = Vector(CAM_END_POS)

    st_u = {"key": None}
    st_x = {"key": None}

    def set_idle(obj, state):
        if state.get("key") != "idle":
            obj.animation_data.action = acts_u["idle"]
            state["key"] = "idle"

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    frames_iter = [1, 12, 28, 50, 80, 130, 190] if test_mode else range(1, N_FRAMES + 1)
    for f in frames_iter:
        t = ease((f - 1) / (N_FRAMES - 1))

        # 叔叔：全程 idle，身体微转向许宁
        if f < F_RAISE:
            r = UNCLE_ROT0
        else:
            r = UNCLE_ROT0 + (UNCLE_ROT1 - UNCLE_ROT0) * ease((f - F_RAISE) / (F_RAISE_END - F_RAISE))
        uncle.rotation_euler.z = math.radians(r)
        set_idle(uncle, st_u)

        # 许宁：f45-95 侧迈半步靠近
        if f < F_XU_STEP:
            xu_x, r_x = XU_X0, XU_ROT0
        elif f <= F_XU_STEP_END:
            k = ease((f - F_XU_STEP) / (F_XU_STEP_END - F_XU_STEP))
            xu_x = XU_X0 + (XU_X1 - XU_X0) * k
            r_x = XU_ROT0 + (XU_ROT1 - XU_ROT0) * k
        else:
            xu_x, r_x = XU_X1, XU_ROT1
        xu.location.x = xu_x
        xu.rotation_euler.z = math.radians(r_x)
        set_idle(xu, st_x)

        scene.frame_set(f)

        # frame_set 之后覆盖手动姿态（通道已剥）
        uncle_arm_pose(uncle, uncle_arm_t(f))
        # 两人低头看屏幕（举机后）
        if f >= F_RAISE_END:
            rotate_pose_bone_world(uncle, "mixamorig:Head", (1, 0, 0), -14)
            rotate_pose_bone_world(xu, "mixamorig:Head", (1, 0, 0), -12)
        elif f >= F_XU_STEP_END:
            rotate_pose_bone_world(xu, "mixamorig:Head", (1, 0, 0), -8)

        u_head = uncle.matrix_world @ uncle.pose.bones["mixamorig:Head"].head
        x_head = xu.matrix_world @ xu.pose.bones["mixamorig:Head"].head
        tgt = (u_head + x_head) * 0.5 + Vector(TGT_OFFSET)
        cam.location = sp.lerp(ep, t)
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs08] frame {f}/{N_FRAMES} arm_t={uncle_arm_t(f):.2f} "
                  f"xu_x={xu.location.x:.2f}", flush=True)

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS}
    with open(os.path.join(OUT_DIR, "previs08_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS08_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
