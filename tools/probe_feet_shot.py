# -*- coding: utf-8 -*-
"""渲染 C05 走路姿势的脚部特写，直接看滑雪板是什么。"""
import math

import bpy
from mathutils import Vector

path = r"assets/models/C05/tex_mesh_v08_anim4.glb"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)
arm = [x for x in bpy.data.objects if x.type == "ARMATURE"][0]
mesh = [x for x in bpy.data.objects if x.type == "MESH" and "sphere" not in x.name.lower()][0]
for o in bpy.data.objects:
    if o.type == "MESH" and "sphere" in o.name.lower():
        bpy.data.objects.remove(o, do_unlink=True)

walk = [a for a in bpy.data.actions if a.name.startswith("animation_1")][0]
arm.animation_data.action = walk
bpy.context.scene.frame_set(20)
bpy.context.view_layer.update()

mat = bpy.data.materials.new("m")
mat.use_nodes = True
for n in mat.node_tree.nodes:
    if n.bl_idname == "ShaderNodeBsdfPrincipled":
        n.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
        n.inputs["Roughness"].default_value = 0.9
mesh.data.materials.clear()
mesh.data.materials.append(mat)

bpy.ops.object.light_add(type="AREA", location=(1.5, -1.5, 1.0))
bpy.context.active_object.data.energy = 300
bpy.context.active_object.data.size = 2
bpy.ops.object.light_add(type="AREA", location=(-1.5, 1.5, 1.5))
bpy.context.active_object.data.energy = 200

cam_data = bpy.data.cameras.new("c")
cam_data.lens = 50
cam = bpy.data.objects.new("c", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
# 脚部世界坐标：rest 时脚底 z≈-0.82，走路时双脚在 x±0.1, y 0 附近
feet = Vector((0.0, 0.0, -0.78))
cam.location = feet + Vector((1.6, -1.2, 0.35))
d = feet - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 960
scene.render.resolution_y = 720
scene.render.filepath = r"assets/qc/c05_feet_walk.png"
bpy.ops.render.render(write_still=True)
print("FEET_SHOT_DONE")
