import os
from collections import defaultdict
import bpy
from mathutils import Vector
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "assets", "models", "E03", "tex_mesh_scaled.glb"))
bpy.context.view_layer.update()
bins = defaultdict(lambda: [-1e9, 1e9, -1e9, 1e9])
for o in bpy.context.scene.objects:
    if o.type != "MESH":
        continue
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        b = round(w.x, 0)  # 1m bins
        bins[b][0] = max(bins[b][0], w.z)
        bins[b][1] = min(bins[b][1], w.z)
        bins[b][2] = max(bins[b][2], w.y)
        bins[b][3] = min(bins[b][3], w.y)
for b in sorted(bins):
    print(f"x={b:+.0f}  z[{bins[b][1]:+.2f},{bins[b][0]:+.2f}]  y[{bins[b][3]:+.2f},{bins[b][2]:+.2f}]")
