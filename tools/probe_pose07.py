# -*- coding: utf-8 -*-
"""探针：预演循环复现——animated glb + 切 idle + 剥通道 + frame_set + 手动赋值，打印手部位置。"""
import math
import os
import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "C14", "tex_mesh_v08_animated.glb"))
bpy.context.view_layer.update()
arm = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][-1]
arm.rotation_mode = "XYZ"
arm.rotation_euler = (0, 0, math.radians(155))
arm.location = (1.45, 1.0, 0.78)

acts = {}
for ac in bpy.data.actions:
    if ac.name.lower() == "animation_1":
        acts["a1"] = ac
    elif ac.name.lower() == "animation_2":
        acts["a2"] = ac
print("actions:", [a.name for a in bpy.data.actions], flush=True)
print("nla tracks:", [t.name for t in arm.animation_data.nla_tracks] if arm.animation_data else None,
      "active action:", arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None, flush=True)

targets = (
    'pose.bones["mixamorig:RightArm"].rotation_quaternion',
    'pose.bones["mixamorig:RightForeArm"].rotation_quaternion',
)
for ac in acts.values():
    for layer in ac.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in list(bag.fcurves):
                    if fc.data_path in targets:
                        bag.fcurves.remove(fc)

arm.animation_data.action = acts["a2"]   # idle
bpy.context.scene.frame_set(120)
bpy.context.view_layer.update()

pb = arm.pose.bones["mixamorig:RightArm"]
rest_q = pb.bone.matrix_local.to_quaternion()
inv = rest_q.inverted()
q = inv @ Quaternion((0, 1, 0), math.radians(-10.0)) @ rest_q
pb.rotation_mode = "QUATERNION"
pb.rotation_quaternion = q

hand = arm.matrix_world @ arm.pose.bones["mixamorig:RightHand"].head
print(f"after assign (no update yet): hand=({hand.x:+.2f},{hand.y:+.2f},{hand.z:+.2f})", flush=True)
bpy.context.view_layer.update()
hand = arm.matrix_world @ arm.pose.bones["mixamorig:RightHand"].head
print(f"after update: hand=({hand.x:+.2f},{hand.y:+.2f},{hand.z:+.2f})", flush=True)
pb_rot = arm.pose.bones["mixamorig:RightArm"].rotation_quaternion
print(f"pb.rotation_quaternion kept: {tuple(round(v,3) for v in pb_rot)}", flush=True)
print("PROBE_POSE_DONE", flush=True)
