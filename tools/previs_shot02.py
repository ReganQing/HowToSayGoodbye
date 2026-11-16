# -*- coding: utf-8 -*-
"""白模预演：老厂区楼道口 · shot02「姥姥给许宁别上红发带」双人近景（Blender 相机调度）。

与 shot01（幻觉全景）对照：本镜是现实线"因"——红发带第一次戴上，
双人近景构图，人物占画面主体，为 H3 ref2v 提供清晰面容所需的构图基础
（面容像素级锚定另由 ref_images 图片参考通道完成，见 tools/h3_r2v_workflow_shot02.json）。

Run:
  set PREVIS_TEST=1 && blender.exe --background --python tools/previs_shot02.py   (5 帧构图测试)
  blender.exe --background --python tools/previs_shot02.py                        (192 帧全量)

Staging: 姥姥(C08) 在 landing 俯身，右手持红发带伸向许宁；许宁(C01) 仰头抬手摸辫子。
角色保持静态瞬间（本镜为"预备瞬间"，动态交给 H3 生成），只有相机缓推。
"""
import json
import math
import os

import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")
FRAMES_DIR = os.path.join(OUT_DIR, "frames02")

FPS = 24
DURATION_S = 8
N_FRAMES = FPS * DURATION_S
RES_X, RES_Y = 1280, 720

# E01 scaled 1.5x about its base: ground z=-1.35, landing ~-0.225, mid-stair ~-0.72.
E01_FILE = "tex_mesh.glb"
E01_SCALE = 1.5

# IMPORTANT: rigged GLB armature origin is at the HIPS, not the feet.
# Measured: C08 (1.6m) feet sit at local z=-0.80, so armature z must be
# ground_z + hip_height. C01 (1.1m) hip height ~0.55.
GROUND_Z = -1.35
HIP_C08, HIP_C01 = 0.80, 0.55

# ---- staging ----
# Pair stands side-by-side facing each other on the open ground in front of the
# stairwell shell (no wall occlusion); the building is the backdrop.
# Line between them is roughly perpendicular to the camera axis -> symmetric two-shot.
C08_POS = (-0.15, -2.75, GROUND_Z + HIP_C08)   # granny, left of frame
C01_POS = (0.75, -2.95, GROUND_Z + HIP_C01)    # girl, right of frame


def face_rot_z(src, dst):
    """rotation about Z so the object's local +Y points from src to dst (XZ plane)."""
    dx, dy = dst[0] - src[0], dst[1] - src[1]
    return math.degrees(math.atan2(-dx, dy)) % 360


def bend_axis(rot_z_deg):
    """World axis for 'lean forward' of a character rotated by rot_z about Z.

    Local +Y (facing) rotated forward (-Z dip) == rotation about (-cos, -sin, 0).
    Positive angle leans forward; negative leans back.
    """
    t = math.radians(rot_z_deg)
    return (-math.cos(t), -math.sin(t), 0.0)


# pose config: list of (bone, axis_spec, angle_deg)
# axis_spec: "lean" -> bend_axis(rot_z); or explicit world axis tuple.
POSE_C08 = [
    ("mixamorig:Spine",   "lean", 26),
    ("mixamorig:Spine1",  "lean", 14),
    ("mixamorig:Spine2",  "lean", 8),
    ("mixamorig:Neck",    "lean", -16),   # counter-tilt so she still looks at the girl
    ("mixamorig:Head",    "lean", -8),
    ("mixamorig:RightArm",  (0, 1, 0), 96),   # right arm reaching out toward the girl
    ("mixamorig:RightForeArm", (1, 0, 0), -55),
    ("mixamorig:LeftArm",  (0, 1, 0), -58),
    ("mixamorig:LeftForeArm", (1, 0, 0), -35),
]
POSE_C01 = [
    ("mixamorig:Neck",    "lean", -16),   # tilt head back to look up at granny
    ("mixamorig:Head",    "lean", -8),
    ("mixamorig:RightArm",  (0, 1, 0), 108),  # right hand up touching her braid
    ("mixamorig:RightForeArm", (1, 0, 0), -85),
    ("mixamorig:LeftArm",  (0, 1, 0), -70),
    ("mixamorig:LeftForeArm", (1, 0, 0), -25),
]

# camera: 3/4 side medium close-up on the pair, slow eased push-in.
# Start/end targets are computed at runtime from the actual head bone positions
# (see main()); these are fallbacks.
CAM_START_POS = (1.70, -4.70, 0.90)
CAM_END_POS = (1.30, -4.10, 0.75)
CAM_LENS = 35


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def make_matte():
    mat = bpy.data.materials.new("previz_matte02")
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


def place_character(cid, pos, rot_z, pose):
    path = os.path.join(MODELS, cid, "tex_mesh_v04_rigged.glb")
    import_glb(path)
    # remove rig gizmo spheres (transparent control icospheres) from Lux3D rigged GLB
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH" and "棱角球" in o.name]:
        bpy.data.objects.remove(o, do_unlink=True)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    arm_obj = arms[-1]  # the armature just imported (scene accumulates)
    arm_obj.location = pos
    arm_obj.rotation_euler = (0, 0, math.radians(rot_z))
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")
    lean = bend_axis(rot_z)
    for bone, axis, angle in pose:
        ax = lean if axis == "lean" else axis
        rotate_pose_bone_world(arm_obj, bone, ax, angle)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def head_world(arm_obj):
    """World position of the character's head bone (camera target anchor)."""
    pb = arm_obj.pose.bones.get("mixamorig:Head")
    if pb is None:
        return arm_obj.matrix_world.translation
    return arm_obj.matrix_world @ pb.head


def add_ribbon(arm_obj, girl_arm_obj):
    """Red hair ribbon held between granny's reaching hand and the girl's braid.

    Sized to read clearly at 1280x720 (the ribbon is the emotional anchor prop
    of this shot and must stay visible through the H3 reference pass).
    """
    pb = arm_obj.pose.bones.get("mixamorig:RightHand")
    if pb is None:
        return None
    hand_world = arm_obj.matrix_world @ pb.head
    girl_head = head_world(girl_arm_obj)
    # place the ribbon on the line between granny's hand and the girl's head,
    # biased toward the girl's braid (top-side of her head)
    anchor = girl_head + Vector((0.0, 0.0, 0.10))
    direction = anchor - hand_world
    direction.z *= 0.35  # keep it near horizontal
    direction.normalize()
    center = hand_world + direction * 0.22
    bpy.ops.mesh.primitive_cube_add(size=0.02)
    strip = bpy.context.active_object
    # set dimensions directly (no transform_apply: it would hit ALL selected
    # objects, including the just-imported rigged characters)
    strip.dimensions = (0.022, 0.52, 0.045)  # long along Y, points toward the girl
    strip.location = (center.x, center.y, center.z)
    flat = Vector((direction.x, direction.y, 0.0)).normalized()
    strip.rotation_mode = "QUATERNION"
    strip.rotation_quaternion = flat.to_track_quat("Y", "Z")
    print(f"[previs02] ribbon center=({center.x:.2f},{center.y:.2f},{center.z:.2f}) strip={strip.name}", flush=True)
    mat = bpy.data.materials.new("ribbon_red02")
    mat.use_nodes = True
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (0.85, 0.05, 0.10, 1.0)
            n.inputs["Roughness"].default_value = 0.5
            if "Emission Color" in n.inputs:
                n.inputs["Emission Color"].default_value = (0.85, 0.05, 0.10, 1.0)
                n.inputs["Emission Strength"].default_value = 0.35
    strip.data.materials.append(mat)
    strip.name = "ribbon_strip"
    return strip


def add_lighting():
    world = bpy.data.worlds.new("previz_world02")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.42, 0.44, 0.48, 1.0)
            n.inputs[1].default_value = 0.55
    bpy.context.scene.world = world
    # warm key from front-left of the camera side
    bpy.ops.object.light_add(type="AREA", location=(2.2, -2.6, 2.6))
    key = bpy.context.active_object
    key.data.energy = 1100
    key.data.size = 2.0
    # softer fill so faces keep detail
    bpy.ops.object.light_add(type="AREA", location=(-1.2, 0.8, 2.2))
    fill = bpy.context.active_object
    fill.data.energy = 420
    fill.data.size = 3.0


def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def main():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    clean_scene()
    add_lighting()

    # environment (same scaling fix as shot01: generated model is undersized)
    import_glb(os.path.join(MODELS, "E01", E01_FILE))
    env_meshes = mesh_objects()
    for o in env_meshes:
        o.scale = (E01_SCALE, E01_SCALE, E01_SCALE)
    bpy.context.view_layer.update()

    # characters
    c08_rot = face_rot_z(C08_POS, C01_POS)
    c01_rot = face_rot_z(C01_POS, C08_POS)
    print(f"[previs02] C08 rot_z={c08_rot:.1f}  C01 rot_z={c01_rot:.1f}", flush=True)
    granny = place_character("C08", C08_POS, c08_rot, POSE_C08)
    girl = place_character("C01", C01_POS, c01_rot, POSE_C01)
    add_ribbon(granny, girl)

    # camera target: weighted toward the girl (she is smaller and needs more
    # frame presence; the granny's leaning mass anchors the left side)
    h8 = head_world(granny)
    h1 = head_world(girl)
    tgt_mid = h8 * 0.35 + h1 * 0.65
    print(f"[previs02] head C08=({h8.x:.2f},{h8.y:.2f},{h8.z:.2f}) C01=({h1.x:.2f},{h1.y:.2f},{h1.z:.2f}) tgt=({tgt_mid.x:.2f},{tgt_mid.y:.2f},{tgt_mid.z:.2f})", flush=True)
    cam_start_tgt = Vector((tgt_mid.x, tgt_mid.y, tgt_mid.z - 0.10))
    cam_end_tgt = Vector((tgt_mid.x, tgt_mid.y, tgt_mid.z - 0.06))

    # matte override for everything except the red ribbon (keep its name check
    # in sync with add_ribbon: the strip is renamed to ribbon_strip)
    apply_matte([o for o in mesh_objects() if o.name != "ribbon_strip"])

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

    cam_data = bpy.data.cameras.new("previs_cam02")
    cam_data.type = "PERSP"
    cam_data.lens = CAM_LENS
    cam = bpy.data.objects.new("previs_cam02", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam

    sp = Vector(CAM_START_POS)
    st = cam_start_tgt
    ep = Vector(CAM_END_POS)
    et = cam_end_tgt

    report = {"frames": N_FRAMES, "fps": FPS, "res": [RES_X, RES_Y],
              "lens": CAM_LENS, "views": {}}
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
            print(f"[previs02] frame {f}/{N_FRAMES}", flush=True)

    with open(os.path.join(OUT_DIR, "previs02_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("PREVIS02_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
