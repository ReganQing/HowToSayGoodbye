# -*- coding: utf-8 -*-
"""Probe E02: vertex z (up) binned stats to locate mattress surface."""
import os
from collections import defaultdict
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLB = os.path.join(ROOT, "assets", "models", "E02", "tex_mesh_scaled.glb")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=GLB)
bpy.context.view_layer.update()

bins = defaultdict(lambda: [-1e9, 1e9])
mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
for o in bpy.context.scene.objects:
    if o.type != "MESH":
        continue
    for corner in o.bound_box:
        w = o.matrix_world @ Vector(corner)
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        b = round(w.x, 1)
        bins[b][0] = max(bins[b][0], w.z)
        bins[b][1] = min(bins[b][1], w.z)
print("bbox min", [round(v,2) for v in mn], "max", [round(v,2) for v in mx])
for b in sorted(bins):
    print(f"x={b:+.1f}  z_max={bins[b][0]:+.2f}  z_min={bins[b][1]:+.2f}")
