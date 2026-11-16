# -*- coding: utf-8 -*-
"""探针：E05 原始尺寸 bbox 打印 + 顶视/正视渲染，判断重建出了哪些结构。"""
import math
import os
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT_TOP = os.path.join(ROOT, "assets", "previs", "e05_topview.png")
OUT_FRONT = os.path.join(ROOT, "assets", "previs", "e05_frontview.png")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "E05", "tex_mesh.glb"))
bpy.context.view_layer.update()

mins = [1e9] * 3
maxs = [-1e9] * 3
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                mins[i] = min(mins[i], w[i])
                maxs[i] = max(maxs[i], w[i])
span = [maxs[i] - mins[i] for i in range(3)]
print(f"E05 bbox min=({mins[0]:.2f},{mins[1]:.2f},{mins[2]:.2f}) "
      f"max=({maxs[0]:.2f},{maxs[1]:.2f},{maxs[2]:.2f}) span=({span[0]:.2f},{span[1]:.2f},{span[2]:.2f})", flush=True)

# 统一哑光材质
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

# 1.7m 人形参考柱
mark_mat = bpy.data.materials.new("mark")
mark_mat.use_nodes = True
for n in mark_mat.node_tree.nodes:
    if n.bl_idname == "ShaderNodeBsdfPrincipled":
        n.inputs["Base Color"].default_value = (0.9, 0.2, 0.2, 1.0)
        n.inputs["Emission Color"].default_value = (0.9, 0.2, 0.2, 1.0)
        n.inputs["Emission Strength"].default_value = 2.0
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.85))
ref = bpy.context.active_object
ref.dimensions = (0.4, 0.25, 1.7)
ref.data.materials.append(mark_mat)

bpy.ops.object.light_add(type="AREA", location=(0, 0, 12))
key = bpy.context.active_object
key.data.energy = 2000
key.data.size = 8

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 960
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

# 顶视（相机在原点上方）
bpy.ops.object.camera_add(location=(0, 0, maxs[2] + 8))
cam = bpy.context.active_object
cam.rotation_euler = (0, 0, 0)
scene.camera = cam
scene.render.filepath = OUT_TOP
bpy.ops.render.render(write_still=True)

# 正视（沿 -y 看）
mid_x = (mins[0] + maxs[0]) / 2
mid_z = (mins[2] + maxs[2]) / 2
depth = (maxs[1] - mins[1]) + 10
cam.location = (mid_x, mins[1] - depth * 0.4, mid_z)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.render.filepath = OUT_FRONT
bpy.ops.render.render(write_still=True)
print("PROBE_E05_DONE", flush=True)
