# -*- coding: utf-8 -*-
"""探针：C05/C10 v08 rigged 骨架结构（骨骼命名、髋/头世界坐标、动画列表）。"""
import math
import os
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")

for cid in ("C05", "C10"):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, cid, "tex_mesh_v08_rigged.glb"))
    bpy.context.view_layer.update()
    print(f"--- {cid} ---")
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    print("armatures:", [a.name for a in arms])
    for a in arms:
        names = [b.name for b in a.data.bones]
        print("bones:", len(names), "first 12:", names[:12])
        for probe in ("mixamorig:Hips", "Hips", "mixamorig:Head", "Head"):
            pb = a.pose.bones.get(probe)
            if pb:
                w = a.matrix_world @ pb.head
                print(f"  {probe}: world=({w.x:.3f},{w.y:.3f},{w.z:.3f})")
        break
    acts = [ac.name for ac in bpy.data.actions]
    print("actions:", acts)
print("PROBE_RIG_DONE", flush=True)
