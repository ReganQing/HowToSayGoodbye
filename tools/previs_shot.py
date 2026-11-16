# -*- coding: utf-8 -*-
"""白模预演：老厂区楼道口 · 结尾幻觉镜头（Blender 相机调度）。

Run:
  blender.exe --background --python tools/previs_shot.py

Renders a 1280x720 24fps 192-frame previz sequence to assets/previs/frames/,
with matte white-gray overrides (classic previz look) and a red accent
strip for the hair ribbon. Camera does a slow eased push-in.

Staging config is in PLACEMENTS below; tweak and re-run.
"""
import json
import math
import os

import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames")

FPS = 24
DURATION_S = 8
N_FRAMES = FPS * DURATION_S
RES_X, RES_Y = 1280, 720

# ---- staging: (x, y, z, facing_deg_about_Z, ...) ----
# E01 scaled 1.5x about its base: ground z=-1.35, landing ~-0.225, mid-stair ~-0.72.
PLACEMENTS = {
    "C08": {"file": "tex_mesh_v04_rigged.glb", "pos": (0.60, 0.62, -0.18), "rot_z": 155,
            "raise_right": True},
    "C09": {"file": "tex_mesh_v04_rigged.glb", "pos": (-0.95, 0.45, -0.20), "rot_z": 200,
            "raise_right": False},
    "C12": {"file": "tex_mesh_v04_rigged.glb", "pos": (1.10, -0.66, -1.30), "rot_z": 140,
            "raise_right": False, "point_at_bike": True},
    "C01": {"file": "tex_mesh_v04_rigged.glb", "pos": (-0.18, -0.02, -0.72), "rot_z": 185,
            "raise_right": False},
}
E01_FILE = "tex_mesh.glb"
E01_SCALE = 1.5  # model is undersized (1.8m tall); scale about its centered origin
P14_FILE = "tex_mesh.glb"
P14_TARGET = (1.45, -0.68, -1.28)  # bike center next to dad
P14_SCALE = 0.32                   # model is ~3.1x oversized vs real bicycle

# camera: (start_pos, start_target) -> (end_pos, end_target), eased
CAM_START_POS = (4.0, -6.6, 2.60)
CAM_START_TGT = (0.10, 0.15, 0.50)
CAM_END_POS = (2.5, -3.8, 2.10)
CAM_END_TGT = (0.35, 0.30, 0.55)


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def make_matte():
    mat = bpy.data.materials.new("previz_matte")
    mat.use_nodes = True
    bsdf = None
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            bsdf = n
            break
    bsdf.inputs["Base Color"].default_value = (0.78, 0.78, 0.78, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Metallic"].default_value = 0.0
    return mat


def apply_matte(objs):
    mat = make_matte()
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(mat)


def world_bbox(objs):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for corner in o.bound_box:
            w = o.matrix_world @ Vector(corner)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
    return mn, mx


def rotate_pose_bone_world(arm_obj, bone_name, world_axis, angle_deg):
    """Rotate a pose bone by angle about a world-space axis."""
    pb = arm_obj.pose.bones.get(bone_name)
    if pb is None:
        return False
    rest_q = pb.bone.matrix_local.to_quaternion()
    q_world = Quaternion(Vector(world_axis).normalized(), math.radians(angle_deg))
    q_local = rest_q.inverted() @ q_world @ rest_q
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = q_local
    return True


def pose_character(cid, cfg):
    path = os.path.join(MODELS, cid, cfg["file"])
    import_glb(path)
    # remove rig gizmo spheres that come with the Lux3D rigged GLB
    # (transparent control icospheres; must not be matte-overridden)
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH" and "棱角球" in o.name]:
        bpy.data.objects.remove(o, do_unlink=True)
    arm = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    meshes = mesh_objects()
    # the glTF mesh is parented to the armature: move/rotate the armature only
    if arm:
        arm_obj = arm[-1]  # the armature just imported (scene accumulates)
        arm_obj.location = cfg["pos"]
        arm_obj.rotation_euler = (0, 0, math.radians(cfg["rot_z"]))
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="POSE")
        if cfg.get("raise_right"):
            # right arm up and slightly forward, elbow bent -> holding ribbon
            rotate_pose_bone_world(arm_obj, "mixamorig:RightArm", (0, 1, 0), 108)
            rotate_pose_bone_world(arm_obj, "mixamorig:RightForeArm", (1, 0, 0), -70)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftArm", (0, 1, 0), -78)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftForeArm", (1, 0, 0), -22)
        elif cfg.get("point_at_bike"):
            # right arm forward-down toward the bike handlebar
            rotate_pose_bone_world(arm_obj, "mixamorig:RightArm", (0, 1, 0), 150)
            rotate_pose_bone_world(arm_obj, "mixamorig:RightForeArm", (1, 0, 0), -35)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftArm", (0, 1, 0), -80)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftForeArm", (1, 0, 0), -20)
        else:
            # natural standing: arms down, slight elbow bend
            rotate_pose_bone_world(arm_obj, "mixamorig:RightArm", (0, 1, 0), -76)
            rotate_pose_bone_world(arm_obj, "mixamorig:RightForeArm", (1, 0, 0), -25)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftArm", (0, 1, 0), 76)
            rotate_pose_bone_world(arm_obj, "mixamorig:LeftForeArm", (1, 0, 0), -25)
        bpy.ops.object.mode_set(mode="OBJECT")
    return arm[-1] if arm else None


def add_ribbon(arm_obj):
    """Small red strip held in granny's raised right hand (dynamic attach)."""
    pb = arm_obj.pose.bones.get("mixamorig:RightHand")
    if pb is None:
        return None
    hand_world = arm_obj.matrix_world @ pb.head
    bpy.ops.mesh.primitive_cube_add(size=0.035)
    strip = bpy.context.active_object
    strip.scale = (0.7, 0.3, 11.0)  # long thin vertical ribbon
    bpy.ops.object.transform_apply(scale=True)
    strip.location = (hand_world.x, hand_world.y, hand_world.z - 0.24)
    mat = bpy.data.materials.new("ribbon_red")
    mat.use_nodes = True
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (0.72, 0.10, 0.12, 1.0)
            n.inputs["Roughness"].default_value = 0.6
    strip.data.materials.append(mat)
    return strip


def add_lighting():
    world = bpy.data.worlds.new("previz_world")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.42, 0.44, 0.48, 1.0)
            n.inputs[1].default_value = 0.55
    bpy.context.scene.world = world
    # key light (warm, from front-left like late afternoon sun)
    bpy.ops.object.light_add(type="AREA", location=(2.5, -3.5, 3.2))
    key = bpy.context.active_object
    key.data.energy = 900
    key.data.size = 2.5
    # fill
    bpy.ops.object.light_add(type="AREA", location=(-2.0, 1.5, 2.5))
    fill = bpy.context.active_object
    fill.data.energy = 350
    fill.data.size = 3.0


def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    add_lighting()

    # environment (scaled up: the generated model is undersized vs characters)
    import_glb(os.path.join(MODELS, "E01", E01_FILE))
    env_meshes = mesh_objects()
    for o in env_meshes:
        o.scale = (E01_SCALE, E01_SCALE, E01_SCALE)  # centered origin -> base stays proportional
    bpy.context.view_layer.update()
    # bicycle (model is oversized ~3.1x; scale down and rest it on the ground)
    import_glb(os.path.join(MODELS, "P14", P14_FILE))
    bike_meshes = [o for o in mesh_objects() if o not in env_meshes]
    for o in bike_meshes:
        o.scale = (P14_SCALE, P14_SCALE, P14_SCALE)
    bpy.context.view_layer.update()
    for o in bike_meshes:
        o.rotation_euler = (0, 0, math.radians(90))
    bpy.context.view_layer.update()
    bmn, bmx = world_bbox(bike_meshes)
    shift = Vector(P14_TARGET) - Vector(((bmn.x + bmx.x) / 2, (bmn.y + bmx.y) / 2, bmn.z))
    for o in bike_meshes:
        o.location += shift
    bpy.context.view_layer.update()

    # characters
    granny_arm = None
    for cid, cfg in PLACEMENTS.items():
        arm_obj = pose_character(cid, cfg)
        if cid == "C08":
            granny_arm = arm_obj
    if granny_arm is not None:
        add_ribbon(granny_arm)

    # matte override for everything except the red ribbon (previz look + accent)
    apply_matte([o for o in mesh_objects() if not o.name.startswith("Cube")])

    # render settings
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

    # camera with per-frame eased move (no keyframes needed)
    cam_data = bpy.data.cameras.new("previs_cam")
    cam_data.type = "PERSP"
    cam_data.lens = 35
    cam = bpy.data.objects.new("previs_cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    sp = Vector(CAM_START_POS)
    st = Vector(CAM_START_TGT)
    ep = Vector(CAM_END_POS)
    et = Vector(CAM_END_TGT)

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y], "views": {}}
    test_mode = os.environ.get("PREVIS_TEST") == "1"
    frames_iter = [1, 48, 96, 144, 192] if test_mode else range(1, N_FRAMES + 1)
    for f in frames_iter:
        t = ease_in_out((f - 1) / (N_FRAMES - 1))
        pos = sp.lerp(ep, t)
        tgt = st.lerp(et, t)
        cam.location = pos
        direction = tgt - pos
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if f in (1, N_FRAMES // 2, N_FRAMES):
            report["views"][str(f)] = scene.render.filepath
        if f % 48 == 0:
            print(f"[previs] frame {f}/{N_FRAMES}", flush=True)

    with open(os.path.join(OUT_DIR, "previs_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
