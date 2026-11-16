# -*- coding: utf-8 -*-
"""探针：实测 E04 站台 / C05 / C10 v08 的包围盒与关键尺寸。"""
import os
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")

TARGETS = [
    ("E04", "tex_mesh.glb"),
    ("C05", "tex_mesh_v08.glb"),
    ("C10", "tex_mesh_v08.glb"),
]

for cid, glb in TARGETS:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, cid, glb))
    bpy.context.view_layer.update()
    print(f"--- {cid}/{glb} ---")
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        pts = [o.matrix_world @ v.co for v in o.data.vertices]
        if not pts:
            continue
        xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
        print(f"  {o.name}: n={len(pts)} x[{min(xs):.2f},{max(xs):.2f}] "
              f"y[{min(ys):.2f},{max(ys):.2f}] z[{min(zs):.2f},{max(zs):.2f}]")
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    for a in arms:
        print(f"  ARMATURE {a.name}: bones={len(a.data.bones)}")
print("PROBE_ASSET_DONE", flush=True)
