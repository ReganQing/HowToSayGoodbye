# -*- coding: utf-8 -*-
"""列 C05 rest 姿势脚部高度（local z<-0.6）的全部松散部件。"""
import bpy
import bmesh

path = r"assets/models/C05/tex_mesh_v08_anim4.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)
o = [x for x in bpy.data.objects if x.type == "MESH" and "sphere" not in x.name.lower()][0]
me = o.data
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
visited = set()
for s in list(bm.verts):
    if s.index in visited:
        continue
    stack, comp = [s], []
    visited.add(s.index)
    while stack:
        v = stack.pop()
        comp.append(v)
        for e in v.link_edges:
            ov = e.other_vert(v)
            if ov.index not in visited:
                visited.add(ov.index)
                stack.append(ov)
    zs = [v.co.z for v in comp]
    if min(zs) < -0.6 and len(comp) > 8:
        xs = [v.co.x for v in comp]
        ys = [v.co.y for v in comp]
        print("COMP verts", len(comp),
              "x", round(min(xs), 2), round(max(xs), 2),
              "y", round(min(ys), 2), round(max(ys), 2),
              "z", round(min(zs), 2), round(max(zs), 2))
bm.free()
