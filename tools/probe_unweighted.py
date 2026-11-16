# -*- coding: utf-8 -*-
"""查 C05/C15 网格里零权重（未绑骨）的面——rest 姿势原地不动、脚一动就拖地的碎片。"""
import bpy

for path in [r"assets/models/C05/tex_mesh_v08_anim4.glb",
             r"assets/models/C15/tex_mesh_animated.glb"]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    print("===", path.split("\\")[-2])
    for o in bpy.data.objects:
        if o.type != "MESH" or "sphere" in o.name.lower():
            continue
        me = o.data
        unw = [i for i, v in enumerate(me.vertices) if len(v.groups) == 0]
        print("  unweighted verts:", len(unw), "/", len(me.vertices))
        if unw:
            us = set(unw)
            faces = [f for f in me.polygons if all(v in us for v in f.vertices)]
            print("  fully-unweighted faces:", len(faces))
            if faces:
                xs = [me.vertices[v].co.x for f in faces for v in f.vertices]
                ys = [me.vertices[v].co.y for f in faces for v in f.vertices]
                zs = [me.vertices[v].co.z for f in faces for v in f.vertices]
                print("  bbox x", round(min(xs), 2), round(max(xs), 2),
                      "y", round(min(ys), 2), round(max(ys), 2),
                      "z", round(min(zs), 2), round(max(zs), 2))
