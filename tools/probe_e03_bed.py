import os
from collections import defaultdict
import bpy
from mathutils import Vector
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "assets", "models", "E03", "tex_mesh_scaled.glb"))
bpy.context.view_layer.update()
# 床区 x in [-2.2,-1.2]（平移前），0.2m 分箱 z_max，看床垫面
bins = defaultdict(lambda: -1e9)
for o in bpy.context.scene.objects:
    if o.type != "MESH":
        continue
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        if -2.3 <= w.x <= -1.0:
            b = round(w.x, 1)
            bins[b] = max(bins[b], w.z)
for b in sorted(bins):
    print(f"x={b:+.1f}  z_max={bins[b]:+.2f}")
