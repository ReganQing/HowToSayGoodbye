# -*- coding: utf-8 -*-
"""C15 动画 QC：分别截取 4 个动画的中段帧渲染。"""
import math, os, sys
import bpy

ROOT = r"."
GLB = os.path.join(ROOT, "assets", "models", "C15", "tex_mesh_animated.glb")
OUT = os.path.join(ROOT, "assets", "qc")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
ad = arm.animation_data
names = [a.name for a in bpy.data.actions]

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 560
scene.render.resolution_y = 840

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (0, -5.2, 1.0)
cam.rotation_euler = (math.radians(85), 0, 0)

sun_data = bpy.data.lights.new("sun", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(30))

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.9, 0.9, 1)

for i, act in enumerate(names, 1):
    ad.action = bpy.data.actions[act]
    f0, f1 = ad.action.frame_range
    mid = int((f0 + f1) / 2)
    scene.frame_set(mid)
    scene.render.filepath = os.path.join(OUT, f"C15_anim_{i}_{act}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", act, "frame", mid)
print("QC_DONE")
