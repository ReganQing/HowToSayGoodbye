# -*- coding: utf-8 -*-
"""探针：E04 缩放后顶视/侧视渲染，确定站台面高度、列车门、雨棚位置。"""
import math
import os
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_TOP = os.path.join(ROOT, "assets", "previs", "e04_topview.png")
OUT_SIDE = os.path.join(ROOT, "assets", "previs", "e04_sideview.png")
SCALE = 0.35

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "E04", "tex_mesh.glb"))
bpy.context.view_layer.update()
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        o.scale = (SCALE, SCALE, SCALE)
bpy.context.view_layer.update()

# 参考刻度：每 2m 一个 0.5m 高的小方块沿 x 排列，原点处放个红色大方块
mat = bpy.data.materials.new("m")
mat.use_nodes = True
for n in mat.node_tree.nodes:
    if n.bl_idname == "ShaderNodeBsdfPrincipled":
        n.inputs["Base Color"].default_value = (0.75, 0.75, 0.75, 1.0)
        n.inputs["Roughness"].default_value = 0.95
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        o.data.materials.clear()
        o.data.materials.append(mat)

mark_mat = bpy.data.materials.new("mark")
mark_mat.use_nodes = True
for n in mark_mat.node_tree.nodes:
    if n.bl_idname == "ShaderNodeBsdfPrincipled":
        n.inputs["Base Color"].default_value = (0.9, 0.2, 0.2, 1.0)
        n.inputs["Emission Color"].default_value = (0.9, 0.2, 0.2, 1.0)
        n.inputs["Emission Strength"].default_value = 2.0

# 1.7m 高的人形参考柱（代表角色）
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.85))
ref = bpy.context.active_object
ref.dimensions = (0.4, 0.25, 1.7)
ref.data.materials.append(mark_mat)

bpy.ops.object.light_add(type="AREA", location=(0, 0, 12))
key = bpy.context.active_object
key.data.energy = 3000
key.data.size = 10.0
key.rotation_euler = (0, 0, 0)

world = bpy.data.worlds.new("w")
world.use_nodes = True
for n in world.node_tree.nodes:
    if n.bl_idname == "ShaderNodeBackground":
        n.inputs[0].default_value = (0.4, 0.4, 0.45, 1.0)
bpy.context.scene.world = world

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1400
scene.render.resolution_y = 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

cam_data = bpy.data.cameras.new("top")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 42.0
cam = bpy.data.objects.new("top", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = (0, 0, 14)
cam.rotation_euler = (0, 0, 0)
scene.camera = cam
scene.render.filepath = OUT_TOP
bpy.ops.render.render(write_still=True)
print("TOP_DONE", flush=True)

cam.rotation_euler = (math.radians(90), 0, 0)
cam.location = (0, -22, 1.0)
scene.render.filepath = OUT_SIDE
bpy.ops.render.render(write_still=True)
print("SIDE_DONE", flush=True)
