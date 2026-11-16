# -*- coding: utf-8 -*-
"""定位 C05 模型里绑在脚骨上的碎部件（走路时甩到脚下的板条）。"""
import collections

import bmesh
import bpy

path = r"assets/models/C05/tex_mesh_v08_anim4.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)
o = [x for x in bpy.data.objects if x.type == "MESH" and "sphere" not in x.name.lower()][0]
vgs = [g.name for g in o.vertex_groups]

bm = bmesh.new()
bm.from_mesh(o.data)
bm.verts.ensure_lookup_table()

dom = {}
me_verts = o.data.vertices
for v in bm.verts:
    best, bw = None, 0.0
    for g in me_verts[v.index].groups:
        if g.weight > bw:
            bw = g.weight
            best = vgs[g.group] if g.group < len(vgs) else "?"
    dom[v.index] = best

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
    cnt = collections.Counter(dom[v.index] for v in comp)
    top, topn = cnt.most_common(1)[0]
    if top and ("Foot" in top or "Toe" in top) and len(comp) < 3000:
        xs = [v.co.x for v in comp]
        ys = [v.co.y for v in comp]
        zs = [v.co.z for v in comp]
        print("PART verts", len(comp), "top", top, topn,
              "bbox x", round(min(xs), 2), round(max(xs), 2),
              "y", round(min(ys), 2), round(max(ys), 2),
              "z", round(min(zs), 2), round(max(zs), 2))
bm.free()
