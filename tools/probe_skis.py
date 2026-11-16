# -*- coding: utf-8 -*-
"""在动画姿势下找贴地大面片：求值后的网格里，世界 z<0.06 且面积>0.015 的面。"""
import bpy

path = r"assets/models/C05/tex_mesh_v08_anim4.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)
arm = [x for x in bpy.data.objects if x.type == "ARMATURE"][0]
mesh = [x for x in bpy.data.objects if x.type == "MESH" and "sphere" not in x.name.lower()][0]

# 绑 walk 动作并跳到走路中段
acts = [a for a in bpy.data.actions]
walk = None
for a in acts:
    if a.name.startswith("animation_1"):
        walk = a
arm.animation_data.action = walk
bpy.context.scene.frame_set(20)
bpy.context.view_layer.update()

dg = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(dg)
me = ev.to_mesh()
mw = mesh.matrix_world
big = []
allmin = 99.0
for f in me.polygons:
    zs = [(mw @ me.vertices[v].co).z for v in f.vertices]
    allmin = min(allmin, min(zs))
    if max(zs) < -0.70 and f.area > 0.008:
        c = mw @ f.center
        big.append((f.area, len(f.vertices), round(c.x, 2), round(c.y, 2), round(c.z, 3),
                    [v for v in f.vertices][:6]))
big.sort(reverse=True)
print("BIG_FLAT faces:", len(big), "min z in mesh:", round(allmin, 3))
for b in big[:15]:
    print("  area", round(b[0], 3), "verts", b[1], "center", b[2], b[3], b[4], "idx", b[5])
ev.to_mesh_clear()
