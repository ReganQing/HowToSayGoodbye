# -*- coding: utf-8 -*-
"""白模预演：南方街道 shot07「找爸爸的工友」（Blender 相机调度 + 走动/指向动画）。

剧本（四 L223-233）：大二暑假，她去找爸爸原来的工友。旧宿舍已经拆了，
沿街换了几家店。他带她慢慢走，指着一家快餐店，说爸爸以前常来这里吃饭。

走位时间轴（192f / 8s）：
- f1-48   两人并肩沿 +y 慢走（叔叔靠店侧 x=1.45，许宁靠路侧 x=0.55，Walk_Loop + root 平移）
- f49-60  停步（切 Idle），叔叔身体缓转向店铺方向（rot 180→112）
- f61-85  叔叔右臂从身侧抬起，指向 +x 的快餐店（f86-150 保持）
- f63-90  许宁身体缓转看向店铺（rot 180→150），保持到结束
- f151-170 叔叔手臂放下，回到自然站姿
- 镜头缓推，夏日午后暖光

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot07.py   (构图测试)
  blender.exe --background --python tools/previs_shot07.py                          (192 帧全量)
"""
import json
import math
import os

import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames07")

FPS = 24
DURATION_S = 8
N_FRAMES = FPS * DURATION_S
RES_X, RES_Y = 1280, 720

ARM_Z = 0.78               # 绑骨骨架原点离地高（C05/C10 实测；C14 同管线假定相同，测试渲染验证贴地）

# ---- 走位时间轴 ----
F_WALK_END = 48            # 并肩走结束
F_STOP = 49                # 停步切 idle
F_TURN_BODY = 50           # 叔叔身体转向店铺
F_TURN_BODY_END = 64
F_POINT = 61               # 叔叔开始抬臂
F_POINT_END = 85           # 指向到位
F_HOLD_END = 150           # 保持指向
F_LOWER_END = 170          # 手臂放下
XU_LOOK = 63               # 许宁开始转向看店
XU_LOOK_END = 90

WALK_Y0 = -1.8
WALK_Y1 = 1.0              # f1-48 走完，停在快餐店正前方
UNCLE_X = 1.45
XU_X = 0.55
UNCLE_ROT_POINT = 175.0    # 几乎不转身（纯 +x 横向最可见）；侧举略高于肩线越过轮廓
XU_ROT_LOOK = 150.0        # 许宁看店时的身体朝向

CAM_START_POS = (-0.6, 5.2, 1.55)
CAM_END_POS = (-0.3, 4.4, 1.45)
CAM_LENS = 35

# E05 快餐店摆件：原始 span 1.8x1.8x1.05（仅店面+树冠浮雕），放大到门面宽 ~5.8m
SHOP_SCALE = (3.2, 2.0, 3.4)
SHOP_LOC = (6.68, 1.0, 1.80)   # 正面在 x=3.8，落地


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def make_matte(name="previz_matte07", shade=0.78):
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
    """程序化南方街道：马路 + 人行道 + 沿街店面 + E05 快餐店 + 树 + 电动车。"""
    road_mat = make_matte("road_matte", 0.38)
    walk_mat = make_matte("walk_matte", 0.74)
    wall = make_matte("shop_matte", 0.80)
    # 马路（x -9 ~ -0.8）
    add_box("road", (-4.9, 0, -0.11), (8.2, 30.0, 0.2), road_mat)
    # 人行道（x -0.8 ~ 3.8，略高于马路）
    add_box("sidewalk", (1.5, 0, -0.06), (4.6, 30.0, 0.12), walk_mat)
    # 沿街程序化店面（快餐店两侧）
    add_box("shop_a", (5.2, -5.0, 1.7), (2.4, 6.0, 3.4), wall)
    add_box("shop_b", (5.2, 7.0, 1.7), (2.4, 6.0, 3.4), wall)
    # 遮阳板
    add_box("awning_a", (3.9, -5.0, 2.6), (0.9, 6.0, 0.08), wall)
    add_box("awning_b", (3.9, 7.0, 2.6), (0.9, 6.0, 0.08), wall)

    # E05 快餐店（重建出的店面+树浮雕）
    pre = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, "E05", "tex_mesh.glb"))
    for o in [o for o in bpy.context.scene.objects if o not in pre]:
        if o.type == "MESH":
            o.scale = SHOP_SCALE
            o.location = SHOP_LOC
    bpy.context.view_layer.update()

    # 行道树 2 棵（程序化）
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

    # 电动车 2 辆（车身 + 车轮，极简）
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
    world = bpy.data.worlds.new("previz_world07")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.52, 0.47, 0.38, 1.0)   # 暖白天空
            n.inputs[1].default_value = 0.55
    bpy.context.scene.world = world
    # 夏日午后暖阳（偏西，低角度）
    bpy.ops.object.light_add(type="AREA", location=(-5.0, 2.0, 8.0))
    key = bpy.context.active_object
    key.data.energy = 1600
    key.data.size = 6.0
    key.data.color = (1.0, 0.83, 0.60)
    key.rotation_euler = (math.radians(20), math.radians(-25), math.radians(-40))
    # 冷色天光补
    bpy.ops.object.light_add(type="AREA", location=(3.0, 6.0, 5.0))
    fill = bpy.context.active_object
    fill.data.energy = 700
    fill.data.size = 5.0
    fill.data.color = (0.75, 0.85, 1.0)
    fill.rotation_euler = (math.radians(55), 0, math.radians(160))


def rotate_pose_bone_world(arm_obj, bone_name, world_axis, angle_deg):
    pb = arm_obj.pose.bones.get(bone_name)
    if pb is None:
        return None
    rest_q = pb.bone.matrix_local.to_quaternion()
    q_world = Quaternion(Vector(world_axis).normalized(), math.radians(angle_deg))
    q_local = rest_q.inverted() @ q_world @ rest_q
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = q_local
    return q_local


def uncle_arm_pose(arm_obj, raise_t, swing_deg=0.0, elbow_deg=None):
    """叔叔右臂：raise_t 0=垂放 → 1=侧举指向 +x（世界；rot≈155-180 时右臂侧举≈世界 +x，
    正面机位下横向可见）。swing_deg：走路段前后摆臂叠加。
    探针实测（animated glb）：RightArm (0,1,0)-90=垂放, 0=rest 侧平举, (0,0,1)+90=前摆。"""
    pb = arm_obj.pose.bones.get("mixamorig:RightArm")
    if pb is None:
        return
    rest_q = pb.bone.matrix_local.to_quaternion()
    inv = rest_q.inverted()
    # 终点 +10°（略高于肩线，越过肩部轮廓可见）；0=rest 侧平举
    ang = -90.0 + 100.0 * max(0.0, min(1.0, raise_t))
    q = inv @ Quaternion((0, 1, 0), math.radians(ang)) @ rest_q
    if abs(swing_deg) > 0.01:
        q = q @ (inv @ Quaternion((0, 0, 1), math.radians(swing_deg)) @ rest_q)
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = q
    if elbow_deg is None:
        elbow_deg = 8.0 - 3.0 * raise_t   # 垂放微屈 → 侧举接近伸直
    pf = arm_obj.pose.bones.get("mixamorig:RightForeArm")
    if pf is not None:
        rest_f = pf.bone.matrix_local.to_quaternion()
        inv_f = rest_f.inverted()
        q_f = (inv_f @ Quaternion((0, 1, 0), math.radians(elbow_deg)) @ rest_f)
        if abs(swing_deg) > 0.01:
            q_f = q_f @ (inv_f @ Quaternion((0, 0, 1), math.radians(swing_deg * 0.5)) @ rest_f)
        pf.rotation_mode = "QUATERNION"
        pf.rotation_quaternion = q_f


def strip_arm_channels(acts):
    """从 Lux3D 动作里移除右臂/右前臂旋转通道，改为每帧手动赋值（防止 action 评估覆盖）。
    Blender 5.x 分层 action：从 channelbag 直接删 fcurve。"""
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


def uncle_arm_state(f):
    """返回 (raise_t, swing_deg)：走段摆臂，f61 起抬臂侧举指向，f151 放下。"""
    if f <= F_WALK_END:
        swing = 22.0 * math.sin(2.0 * math.pi * (f - 1) / 32.0)   # Walk_Loop 32f 周期
        return 0.0, swing
    if f < F_POINT:
        return 0.0, 0.0
    if f <= F_POINT_END:
        t = ease((f - F_POINT) / (F_POINT_END - F_POINT))
        return t, 0.0
    if f <= F_HOLD_END:
        return 1.0, 0.0
    if f <= F_LOWER_END:
        t = ease((f - F_HOLD_END) / (F_LOWER_END - F_HOLD_END))
        return 1.0 - t, 0.0
    return 0.0, 0.0


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
    """Lux3D 重定向 glb 动作名是 animation_1/2；按帧数辅助判断（walk 周期短）。"""
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


def ease(t):
    t = max(0.0, min(1.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def y_pos(f):
    if f <= F_WALK_END:
        t = (f - 1) / (F_WALK_END - 1)
        return WALK_Y0 + (WALK_Y1 - WALK_Y0) * t
    return WALK_Y1


def uncle_rot(f):
    if f < F_TURN_BODY:
        return 180.0
    if f <= F_TURN_BODY_END:
        t = ease((f - F_TURN_BODY) / (F_TURN_BODY_END - F_TURN_BODY))
        return 180.0 + (UNCLE_ROT_POINT - 180.0) * t
    return UNCLE_ROT_POINT


def xu_rot(f):
    if f < XU_LOOK:
        return 180.0
    if f <= XU_LOOK_END:
        t = ease((f - XU_LOOK) / (XU_LOOK_END - XU_LOOK))
        return 180.0 + (XU_ROT_LOOK - 180.0) * t
    return XU_ROT_LOOK


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    build_street()
    add_lighting()

    # 叔叔 C14（带 Walk/Idle 动画）
    uncle = import_character("C14", "tex_mesh_v08_animated.glb",
                             (UNCLE_X, WALK_Y0, ARM_Z), 180.0)
    # 许宁 C05（带 Walk/Idle 动画）
    xu = import_character("C05", "tex_mesh_v08_animated.glb",
                          (XU_X, WALK_Y0, ARM_Z), 180.0)
    acts_u = find_actions()
    print(f"[previs07] actions: {list(acts_u.keys())}", flush=True)
    removed = strip_arm_channels(acts_u)
    print(f"[previs07] stripped arm channels: {removed}", flush=True)

    apply_matte = make_matte("char_matte07", 0.82)
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

    cam_data = bpy.data.cameras.new("previs_cam07")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.data.objects.new("previs_cam07", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    sp = Vector(CAM_START_POS)
    ep = Vector(CAM_END_POS)

    def set_action(obj, key, state):
        if key in acts_u and state.get("key") != key:
            obj.animation_data.action = acts_u[key]
            state["key"] = key

    st_u = {"key": None}
    st_x = {"key": None}

    test_mode = os.environ.get("PREVIS_TEST") == "1"
    frames_iter = [1, 32, 55, 75, 120, 160, 190] if test_mode else range(1, N_FRAMES + 1)
    for f in frames_iter:
        t = ease((f - 1) / (N_FRAMES - 1))
        y = y_pos(f)
        key = "walk" if f <= F_WALK_END else "idle"

        # 叔叔
        uncle.location.y = y
        uncle.rotation_euler.z = math.radians(uncle_rot(f))
        set_action(uncle, key, st_u)
        # 许宁
        xu.location.y = y
        xu.rotation_euler.z = math.radians(xu_rot(f))
        set_action(xu, key, st_x)

        scene.frame_set(f)

        # frame_set 之后覆盖叔叔右臂（已从 action 移除通道，不会被评估覆盖）
        raise_t, swing = uncle_arm_state(f)
        uncle_arm_pose(uncle, raise_t, swing)

        # 相机：目标 = 两人头部中点
        u_head = uncle.matrix_world @ uncle.pose.bones["mixamorig:Head"].head
        x_head = xu.matrix_world @ xu.pose.bones["mixamorig:Head"].head
        tgt = (u_head + x_head) * 0.5
        cam.location = sp.lerp(ep, t)
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f % 48 == 0 or f == 1:
            print(f"[previs07] frame {f}/{N_FRAMES} y={y:.2f} rot_u={uncle_rot(f):.0f} "
                  f"rot_x={xu_rot(f):.0f} raise={raise_t:.2f} swing={swing:.0f}", flush=True)

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "lens": CAM_LENS}
    with open(os.path.join(OUT_DIR, "previs07_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS07_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
