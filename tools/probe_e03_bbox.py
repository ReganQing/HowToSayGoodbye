# -*- coding: utf-8 -*-
"""探针：打印 E03 卧室各网格的世界包围盒，校准床沿坐标。"""
import os
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
E03_SHIFT_X = 1.2

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

pre = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "E03", "tex_mesh_scaled.glb"))
for o in [o for o in bpy.context.scene.objects if o not in pre]:
    o.location.x += E03_SHIFT_X
bpy.context.view_layer.update()

for o in bpy.context.scene.objects:
    if o.type != "MESH":
        continue
    pts = [o.matrix_world @ v.co for v in o.data.vertices]  # noqa: E501
    if not pts:
        continue
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    print(f"[E03] {o.name}: x[{min(xs):.2f},{max(xs):.2f}] "
          f"y[{min(ys):.2f},{max(ys):.2f}] z[{min(zs):.2f},{max(zs):.2f}]")
print("E03_PROBE_DONE", flush=True)
