# -*- coding: utf-8 -*-
"""诊断 shot02 预演布局：打印各对象 world bbox + 从 shot01 机位渲染全局定位图。

Run:
  blender.exe --background --python tools/diag_shot02.py
"""
import math
import os

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_DIR = os.path.join(ROOT, "assets", "previs")


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)


def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def report_bbox(name, objs):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for corner in o.bound_box:
            w = o.matrix_world @ Vector(corner)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
    print(f"{name}: min=({mn.x:.2f},{mn.y:.2f},{mn.z:.2f}) max=({mx.x:.2f},{mx.y:.2f},{mx.z:.2f})", flush=True)
    return mn, mx


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # world
    world = bpy.data.worlds.new("diag_world")
    world.use_nodes = True
    for n in world.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBackground":
            n.inputs[0].default_value = (0.42, 0.44, 0.48, 1.0)
            n.inputs[1].default_value = 0.55
    bpy.context.scene.world = world
    bpy.ops.object.light_add(type="AREA", location=(4, -6, 4))
    key = bpy.context.active_object
    key.data.energy = 1200
    key.data.size = 3.0

    # E01 x1.5
    import_glb(os.path.join(MODELS, "E01", "tex_mesh.glb"))
    env = mesh_objects()
    for o in env:
        o.scale = (1.5, 1.5, 1.5)
    bpy.context.view_layer.update()
    report_bbox("E01", env)

    # characters at shot02 staging, unposed (just T-pose rest)
    for cid, pos in (("C08", (0.55, 0.55, -0.20)), ("C01", (0.00, -0.20, -0.28))):
        import_glb(os.path.join(MODELS, cid, "tex_mesh_v04_rigged.glb"))
        for o in [o for o in bpy.context.scene.objects if o.type == "MESH" and "棱角球" in o.name]:
            bpy.data.objects.remove(o, do_unlink=True)
        arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
        arm = arms[-1]
        arm.location = pos
        bpy.context.view_layer.update()
        report_bbox(cid, [o for o in mesh_objects() if o.name not in [e.name for e in env]])

    # matte everything for clean look
    mat = bpy.data.materials.new("diag_matte")
    mat.use_nodes = True
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
    for o in mesh_objects():
        o.data.materials.clear()
        o.data.materials.append(mat)

    # camera: wide establishing view from shot01 direction
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.fps = 24
    cam_data = bpy.data.cameras.new("diag_cam")
    cam_data.type = "PERSP"
    cam_data.lens = 24
    cam = bpy.data.objects.new("diag_cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    scene.camera = cam
    cam.location = (4.0, -6.6, 2.6)
    tgt = Vector((0.1, 0.15, 0.4))
    cam.rotation_euler = (tgt - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()

    # project character head positions into the camera view
    for label, pos in (("C08", (0.55, 0.55, -0.20)), ("C01", (0.00, -0.20, -0.28))):
        for zoff, tag in ((1.35, "face"), (1.55, "top")):
            p = Vector((pos[0], pos[1], pos[2] + zoff))
            ndc = bpy.context.scene.camera.matrix_world.inverted() @ p
            co = bpy_ext = bpy.context.scene.camera.matrix_world.normalized()
            from bpy_extras.object_utils import world_to_camera_view
            ndc = world_to_camera_view(scene, cam, p)
            print(f"{label} {tag}: world=({p.x:.2f},{p.y:.2f},{p.z:.2f}) ndc=({ndc.x:.2f},{ndc.y:.2f},{ndc.z:.2f})", flush=True)

    scene.render.filepath = os.path.join(OUT_DIR, "diag_shot02_wide.png")
    bpy.ops.render.render(write_still=True)
    print("DIAG_DONE", flush=True)


if __name__ == "__main__":
    main()
