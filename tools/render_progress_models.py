# -*- coding: utf-8 -*-
"""为比赛过程资料补渲染缺失的 Lux3D 模型四视图，直接输出到 progress/ 目录。
Run: blender.exe --background --python tools/render_progress_models.py
"""
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from blender_render import (VIEWS, add_camera, add_lighting, clean_scene,
                            fit_ortho, import_glb, mesh_objects, set_engine,
                            world_bbox)

MODELS = [
    {"id": "C05_v08", "glb": os.path.join(ROOT, "assets", "models", "C05", "tex_mesh_v08.glb"),
     "outdir": os.path.join(ROOT, "progress", "02_角色建模", "C05_许宁·大学")},
    {"id": "C10_v08", "glb": os.path.join(ROOT, "assets", "models", "C10", "tex_mesh_v08.glb"),
     "outdir": os.path.join(ROOT, "progress", "02_角色建模", "C10_妈妈·中年")},
    {"id": "C14_v08", "glb": os.path.join(ROOT, "assets", "models", "C14", "tex_mesh_v08.glb"),
     "outdir": os.path.join(ROOT, "progress", "02_角色建模", "C14_工友叔叔")},
    {"id": "E04", "glb": os.path.join(ROOT, "assets", "models", "E04", "tex_mesh.glb"),
     "outdir": os.path.join(ROOT, "progress", "03_场景建模", "E04_火车站台")},
]


def render_one(cfg):
    clean_scene()
    import_glb(cfg["glb"])
    objs = mesh_objects()
    mn, mx = world_bbox(objs)
    center = (mn + mx) / 2
    add_lighting()
    set_engine()
    scene = bpy.context.scene
    scene.render.resolution_x = 560
    scene.render.resolution_y = 840
    scene.render.image_settings.file_format = "PNG"
    os.makedirs(cfg["outdir"], exist_ok=True)
    for name, direction in VIEWS:
        cam = add_camera(f"cam_{name}", center, direction, 1.0)
        fit_ortho(cam, objs)
        scene.render.filepath = os.path.join(cfg["outdir"], f'{cfg["id"]}_{name}.png')
        bpy.ops.render.render(write_still=True)
        print(f'[{cfg["id"]}] {name} done', flush=True)


for cfg in MODELS:
    render_one(cfg)
print("RENDER_ALL_DONE", flush=True)
