# -*- coding: utf-8 -*-
"""QC animated GLB files: sample frames across each clip and render them.

Run:
  blender.exe --background --python tools/anim_qc.py

For each GLB in ANIMS: reports clip name/length/fps, then renders
front three-quarter views at ~0%, ~35% and ~70% of the clip into assets/qc/.
"""
import os

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QC_DIR = os.path.join(ROOT, "assets", "qc")
ANIMS = [
    os.path.join(ROOT, "assets", "models", "C01", "anim", "Idle_Loop.glb"),
    os.path.join(ROOT, "assets", "models", "C01", "anim", "Walk_Loop.glb"),
    os.path.join(ROOT, "assets", "models", "C01", "anim", "Sitting_Idle_Loop.glb"),
]


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


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


def main():
    os.makedirs(QC_DIR, exist_ok=True)
    add_lighting()
    engine = set_engine()
    scene = bpy.context.scene
    scene.render.resolution_x = 560
    scene.render.resolution_y = 840
    scene.render.image_settings.file_format = "PNG"
    scene.render.fps = 30

    for path in ANIMS:
        name = os.path.splitext(os.path.basename(path))[0]
        clean_scene()
        bpy.ops.import_scene.gltf(filepath=path)
        objs = mesh_objects()
        clips = [(a.name if hasattr(a, "name") else "clip", a) for a in bpy.data.actions]
        print(f"[{name}] actions: {[c[0] for c in clips]}", flush=True)
        if not clips:
            print(f"[{name}] NO ACTIONS FOUND", flush=True)
            continue
        act = clips[0][1]
        scene.frame_start = max(1, int(act.frame_range[0]))
        scene.frame_end = int(act.frame_range[1])
        span = scene.frame_end - scene.frame_start
        print(f"[{name}] clip frames {scene.frame_start}..{scene.frame_end} (span {span})", flush=True)

        samples = [0.02, 0.37, 0.72]
        for i, frac in enumerate(samples):
            frame = scene.frame_start + int(span * frac)
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            mn, mx = world_bbox(objs)
            center = (mn + mx) / 2
            cam = add_camera(f"cam_{name}_{i}", center, (0.55, -0.85, 0.12))
            fit_ortho(cam, objs)
            out = os.path.join(QC_DIR, f"C01_anim_{name}_f{i}.png")
            scene.render.filepath = out
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(cam, do_unlink=True)
            print(f"[{name}] frame {frame} -> {out}", flush=True)
    print("RENDER_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
