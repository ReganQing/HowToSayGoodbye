# -*- coding: utf-8 -*-
"""Render QC views of Lux3D GLB models with local Blender (headless).

Run:
  blender.exe --background --python tools/blender_render.py

Config: MODELS list below. For each model renders 4 orthographic views
(front/right/back/left) into assets/qc/. If scale != 1, also exports a
baked-scaled GLB next to the original.
"""
import json
import math
import os

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = [
    {"id": "E02", "glb": os.path.join(ROOT, "assets", "models", "E02", "tex_mesh.glb"), "scale": 2.5, "tag": "v01"},
]
QC_DIR = os.path.join(ROOT, "assets", "qc")
VIEWS = [("front", (0.0, -1.0, 0.0)), ("right", (1.0, 0.0, 0.0)),
         ("back", (0.0, 1.0, 0.0)), ("left", (-1.0, 0.0, 0.0))]
ASPECT = 560.0 / 840.0


def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        pass  # orphan cleanup is optional in --background runs


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
    bg = next((n for n in world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground"), None)
    if bg is not None:
        bg.inputs[0].default_value = (0.62, 0.62, 0.62, 1.0)
        bg.inputs[1].default_value = 0.7
    bpy.context.scene.world = world

    sun_data = bpy.data.lights.new("qc_sun", type="SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("qc_sun", sun_data)
    sun.rotation_euler = (math.radians(50), math.radians(-15), math.radians(30))
    bpy.context.scene.collection.objects.link(sun)

    area_data = bpy.data.lights.new("qc_area", type="AREA")
    area_data.energy = 60.0
    area_data.shape = "DISK"
    area_data.size = 4.0
    area = bpy.data.objects.new("qc_area", area_data)
    area.location = (1.5, -2.5, 2.0)
    bpy.context.scene.collection.objects.link(area)


def add_camera(name, center, direction, ortho):
    cam_data = bpy.data.cameras.new(name)
    cam_data.type = "ORTHO"
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    d = Vector(direction).normalized()
    cam.location = center + d * 10.0
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def fit_ortho(cam, objs, margin=1.18):
    """Set ortho_scale so the model fills 1/margin of the frame, measured by
    actual projection (robust to sensor_fit semantics)."""
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    cam.data.ortho_scale = 1.0
    bpy.context.view_layer.update()  # flush camera matrix before projecting
    max_u = max_v = 0.0
    for o in objs:
        for corner in o.bound_box:
            ndc = world_to_camera_view(scene, cam, o.matrix_world @ Vector(corner))
            max_u = max(max_u, abs(ndc.x - 0.5))
            max_v = max(max_v, abs(ndc.y - 0.5))
    cam.data.ortho_scale = max(2.0 * max_u, 2.0 * max_v) * margin
    return cam.data.ortho_scale


def set_engine():
    scene = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
        try:
            scene.render.engine = eng
            return eng
        except Exception:
            continue
    return scene.render.engine


def render_model(cfg):
    clean_scene()
    import_glb(cfg["glb"])
    objs = mesh_objects()
    if not objs:
        raise RuntimeError(f"no mesh imported from {cfg['glb']}")
    s = cfg["scale"]
    for o in objs:
        o.scale = (s, s, s)
    bpy.context.view_layer.update()
    mn, mx = world_bbox(objs)
    center = (mn + mx) / 2
    size = mx - mn
    ortho = 1.0  # fitted per-view by fit_ortho()

    add_lighting()
    engine = set_engine()
    scene = bpy.context.scene
    scene.render.resolution_x = 560
    scene.render.resolution_y = 840
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False

    report = {"id": cfg["id"], "engine": engine, "bbox": [round(v, 3) for v in size],
              "dims_m": [round(v, 3) for v in size], "views": {}}
    for name, direction in VIEWS:
        cam = add_camera(f"cam_{cfg['id']}_{name}", center, direction, 1.0)
        scale_used = fit_ortho(cam, objs)
        out = os.path.join(QC_DIR, f"{cfg['id']}_{cfg.get('tag', 'v01')}_{name}.png")
        scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        report["views"][name] = out
        report.setdefault("ortho", {})[name] = round(scale_used, 3)
        print(f"[{cfg['id']}] rendered {name} (ortho={scale_used:.2f}) -> {out}", flush=True)

    if abs(s - 1.0) > 1e-6:
        dst = cfg["glb"].replace(".glb", "_scaled.glb")
        bpy.ops.object.select_all(action="SELECT")
        try:
            bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB",
                                      use_selection=True, export_apply=True)
        except TypeError:
            bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", use_selection=True)
        report["scaled_export"] = dst
        print(f"[{cfg['id']}] exported scaled -> {dst}", flush=True)
    return report


def main():
    os.makedirs(QC_DIR, exist_ok=True)
    reports = []
    for cfg in MODELS:
        reports.append(render_model(cfg))
    with open(os.path.join(QC_DIR, "render_report.json"), "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)
    print("RENDER_ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
