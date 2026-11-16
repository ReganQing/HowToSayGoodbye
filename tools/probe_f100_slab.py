# -*- coding: utf-8 -*-
"""在 previs_shot14 的 f100 场景里定位许宁脚下残留的贴地面片。"""
import importlib.util

import bpy

spec = importlib.util.spec_from_file_location("p14", r"tools/previs_shot14.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# 手动复刻 main() 到 f100 之前的场景搭建（借 main 的环境变量控制在 f100 单帧）
import os
os.environ["PREVIS_TEST"] = "1"
# 直接把测试帧改成只有 100，减少干扰
src = open(r"tools/previs_shot14.py", encoding="utf-8").read()
src = src.replace("frames_iter = [1, 30, 50, 75, 100, 130, 145, 155, 165, 175, 190, 192]",
                  "frames_iter = [100]")
ns = {"__name__": "__main__", "__file__": r"tools/previs_shot14.py"}
exec(compile(src, "previs_shot14_probe", "exec"), ns)

# main() 跑完后场景停在 f100
import bmesh
from mathutils import Vector

dg = bpy.context.evaluated_depsgraph_get()
for o in bpy.context.scene.objects:
    if o.type != "MESH" or not o.name.startswith("geometry"):
        continue
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    mw = o.matrix_world
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
        ws = [mw @ v.co for v in comp]
        zs = [p.z for p in ws]
        xs = [p.x for p in ws]
        ys = [p.y for p in ws]
        dx, dy = max(xs) - min(xs), max(ys) - min(ys)
        if max(zs) < 0.08 and len(comp) > 8 and dx > 0.12 and dy > 0.08:
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            print(o.name, "COMP verts", len(comp), "dx", round(dx, 2), "dy", round(dy, 2),
                  "z", round(min(zs), 3), round(max(zs), 3), "center", round(cx, 2), round(cy, 2))
            # 追溯 rest 姿势位置与权重（求值网格顶点序号与原始网格一致）
            vgs = [g.name for g in o.vertex_groups]
            rest = [o.data.vertices[v.index].co for v in comp]
            rzs = [p.z for p in rest]
            cnt = {}
            for v in comp:
                for g in o.data.vertices[v.index].groups:
                    if g.weight > 0.25:
                        cnt[vgs[g.group]] = cnt.get(vgs[g.group], 0) + 1
            top = sorted(cnt, key=cnt.get, reverse=True)[:3]
            print("   rest z", round(min(rzs), 2), round(max(rzs), 2),
                  "rest center", round(sum(p.x for p in rest) / len(rest), 2),
                  round(sum(p.y for p in rest) / len(rest), 2),
                  "groups", top)
    bm.free()
    ev.to_mesh_clear()
print("PROBE_DONE")
