# -*- coding: utf-8 -*-
"""探针：E03 顶视 + 正视正交渲染，标出角色坐姿参考点，校准床沿。"""
import math
import os
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")
OUT = os.path.join(ROOT, "assets", "previs", "e03_topview.png")
OUT_FRONT = os.path.join(ROOT, "assets", "previs", "e03_frontview.png")
E03_SHIFT_X = 1.2

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

pre = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "E03", "tex_mesh_scaled.glb"))
for o in [o for o in bpy.context.scene.objects if o not in pre]:
    o.location.x += E03_SHIFT_X
bpy.context.view_layer.update()

# 哑光材质
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

# 标记：许宁/妈妈髋部、膝、脚尖（按探针姿态实测值）
marks = [
    ("girl_hip",  (0.55, -1.25, 0.12), (0.9, 0.2, 0.2)),
    ("girl_knee", (0.49, -1.47, 0.09), (0.9, 0.2, 0.2)),
    ("girl_foot", (0.48, -1.47, -0.11), (0.9, 0.5, 0.5)),
    ("mom_hip",   (1.05, -1.22, 0.19), (0.2, 0.2, 0.9)),
    ("mom_knee",  (0.98, -1.60, 0.13), (0.2, 0.2, 0.9)),
    ("mom_foot",  (1.00, -1.59, -0.17), (0.5, 0.5, 0.9)),
]
for name, loc, col in marks:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=loc)
    s = bpy.context.active_object
    s.name = name
    m2 = bpy.data.materials.new(name)
    m2.use_nodes = True
    for n in m2.node_tree.nodes:
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            n.inputs["Base Color"].default_value = (*col, 1.0)
            n.inputs["Emission Color"].default_value = (*col, 1.0)
            n.inputs["Emission Strength"].default_value = 2.0
    s.data.materials.append(m2)

# 灯光
bpy.ops.object.light_add(type="AREA", location=(0.8, -1.0, 4.5))
key = bpy.context.active_object
key.data.energy = 1500
key.data.size = 5.0
key.rotation_euler = (0, 0, 0)
bpy.ops.object.light_add(type="AREA", location=(0.8, -4.0, 1.5))
fill = bpy.context.active_object
fill.data.energy = 800
fill.data.size = 4.0
fill.rotation_euler = (math.radians(90), 0, 0)

world = bpy.data.worlds.new("w")
world.use_nodes = True
for n in world.node_tree.nodes:
    if n.bl_idname == "ShaderNodeBackground":
        n.inputs[0].default_value = (0.4, 0.4, 0.45, 1.0)
bpy.context.scene.world = world

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

# 顶视
cam_data = bpy.data.cameras.new("top")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 7.0
cam = bpy.data.objects.new("top", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = (0.8, 0.0, 5.0)
cam.rotation_euler = (0, 0, 0)
scene.camera = cam
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("TOP_DONE", flush=True)

# 正视（从 -y 看，和 shot05 机位同向）
cam.location = (0.8, -5.0, 0.6)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.render.filepath = OUT_FRONT
bpy.ops.render.render(write_still=True)
print("FRONT_DONE", flush=True)
