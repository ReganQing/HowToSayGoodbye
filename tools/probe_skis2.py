# -*- coding: utf-8 -*-
"""在 rest 姿势的 C05 网格里找鞋印轮廓之外的贴地平面片（滑雪板候选）。"""
import bpy

path = r"assets/models/C05/tex_mesh_v08_anim4.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)
mesh = [x for x in bpy.data.objects if x.type == "MESH" and "sphere" not in x.name.lower()][0]
me = mesh.data

cands = []
for f in me.polygons:
    zs = [me.vertices[v].co.z for v in f.vertices]
    if min(zs) < -0.84 or max(zs) > -0.76:
        continue
    if abs(f.normal.z) < 0.85:
        continue
    c = f.center
    # 鞋印范围大约 x±0.13, y -0.15..0.08；超出即候选
    if c.y < -0.16 or c.y > 0.09 or abs(c.x) > 0.135:
        cands.append((round(c.x, 2), round(c.y, 2), round(c.z, 3), round(f.area, 4), list(f.vertices)[:4]))
print("CAND faces:", len(cands))
for c in cands[:20]:
    print("  center", c[0], c[1], c[2], "area", c[3], "idx", c[4])
