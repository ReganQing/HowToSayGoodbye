# -*- coding: utf-8 -*-
"""QC rigged GLB models: rest-pose renders + a skinning deformation test.

Run:
  blender.exe --background --python tools/rig_qc.py

For each model in RIGGED: renders front/back in rest pose.
Then performs an elbow-bend test on the first model: rotates the left
forearm 90 degrees about world Z and renders again. If skinning is valid,
the forearm visibly bends; if broken, the mesh stays rigid.
"""
import os

import bpy
from mathutils import Vector, Quaternion
from math import radians

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QC_DIR = os.path.join(ROOT, "assets", "qc")
RIGGED = [
    {"id": "C01", "glb": os.path.join(ROOT, "assets", "models", "C01", "tex_mesh_v04_rigged.glb"), "tag": "rig"},
    {"id": "C08", "glb": os.path.join(ROOT, "assets", "models", "C08", "tex_mesh_v04_rigged.glb"), "tag": "rig"},
    {"id": "C09", "glb": os.path.join(ROOT, "assets", "models", "C09", "tex_mesh_v04_rigged_scaled16.glb"), "tag": "rig"},
    {"id": "C12", "glb": os.path.join(ROOT, "assets", "models", "C12", "tex_mesh_v04_rigged.glb"), "tag": "rig"},
]
VIEWS = [("front", (0.0, -1.0, 0.0)), ("back", (0.0, 1.0, 0.0))]
ASPECT = 560.0 / 840.0


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


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


def add_lighting():
    world = bpy.data.worlds.new("qc_world")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.64, 0.64, 0.64, 1.0)
            n.inputs[1].default_value = 0.8
    bpy.context.scene.world = world


def set_engine():
    scene = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
        try:
            scene.render.engine = eng
            return eng
        except Exception:
            continue
    return scene.render.engine


def fit_ortho(cam, objs, margin=1.10):
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    cam.data.ortho_scale = 1.0
    max_u = max_v = 0.0
    for o in objs:
        for corner in o.bound_box:
            ndc = world_to_camera_view(scene, cam, o.matrix_world @ Vector(corner))
            max_u = max(max_u, abs(ndc.x - 0.5))
            max_v = max(max_v, abs(ndc.y - 0.5))
    cam.data.ortho_scale = max(2.0 * max_u, 2.0 * max_v) * margin
    return cam.data.ortho_scale


def add_camera(name, center, direction):
    cam_data = bpy.data.cameras.new(name)
    cam_data.type = "ORTHO"
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    d = Vector(direction).normalized()
    cam.location = center + d * 10.0
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    bpy.context.scene.camera = cam
    return cam


def render_view(scene, cfg, name, direction, center, suffix=""):
    cam = add_camera(f"cam_{cfg['id']}_{name}{suffix}", center, direction)
    fit_ortho(cam, mesh_objects())
    out = os.path.join(QC_DIR, f"{cfg['id']}_{cfg['tag']}_{name}{suffix}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    return out


def main():
    os.makedirs(QC_DIR, exist_ok=True)
    add_lighting()
    set_engine()
    scene = bpy.context.scene
    scene.render.resolution_x = 560
    scene.render.resolution_y = 840
    scene.render.image_settings.file_format = "PNG"

    for cfg in RIGGED:
        clean_scene()
        import_glb(cfg["glb"])
        objs = mesh_objects()
        mn, mx = world_bbox(objs)
        center = (mn + mx) / 2
        for name, direction in VIEWS:
            out = render_view(scene, cfg, name, direction, center)
            print(f"[{cfg['id']}] rest {name} -> {out}", flush=True)

    # ---- skinning deformation test on the first model ----
    cfg = RIGGED[0]
    clean_scene()
    import_glb(cfg["glb"])
    objs = mesh_objects()
    mn, mx = world_bbox(objs)
    center = (mn + mx) / 2
    arm = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    pb = arm.pose.bones.get("mixamorig:LeftForeArm")
    if pb is None:
        print("BEND_TEST: bone mixamorig:LeftForeArm not found", flush=True)
        return
    # rotate 90 deg about world Z, expressed in bone-local space
    rest_quat = pb.bone.matrix_local.to_quaternion()
    q_world = Quaternion(Vector((0, 0, 1)), radians(90))
    q_local = rest_quat.inverted() @ q_world @ rest_quat
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = q_local
    bpy.context.view_layer.update()
    out = render_view(scene, cfg, "front", VIEWS[0][1], center, suffix="_bend")
    print(f"[{cfg['id']}] bend test -> {out}", flush=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    print("RENDER_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
