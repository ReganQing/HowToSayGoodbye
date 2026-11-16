# -*- coding: utf-8 -*-
"""探针2：复现预演场景——C05 rot=180 + setup_xu 关键帧，frame_set 后看手部是否被覆盖。"""
import math
import os
import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "C05", "tex_mesh_v08_rigged.glb"))
bpy.context.view_layer.update()
arm = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][-1]
print("actions:", [a.name for a in bpy.data.actions])
print("anim_data:", arm.animation_data, "action:", arm.animation_data.action if arm.animation_data else None)
arm.rotation_euler = (0, 0, math.radians(180))
bpy.context.view_layer.update()


def rot(bone, axis, ang):
    pb = arm.pose.bones.get(bone)
    rest_q = pb.bone.matrix_local.to_quaternion()
    q_world = Quaternion(Vector(axis).normalized(), math.radians(ang))
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = rest_q.inverted() @ q_world @ rest_q


def hand_z(bone):
    h = arm.matrix_world @ arm.pose.bones[bone.replace("Arm", "Hand")].head
    return h.z


# 模拟 setup_xu：f1 双臂放下；f55 -90→f70 +90（右臂）
rot("mixamorig:RightArm", (0, 1, 0), -90)
rot("mixamorig:LeftArm", (0, 1, 0), 90)
arm.pose.bones["mixamorig:RightArm"].keyframe_insert("rotation_quaternion", frame=1)
arm.pose.bones["mixamorig:LeftArm"].keyframe_insert("rotation_quaternion", frame=1)
rot("mixamorig:RightArm", (0, 1, 0), 90)
arm.pose.bones["mixamorig:RightArm"].keyframe_insert("rotation_quaternion", frame=70)
print("after key action:", arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None)

for f in (1, 32, 70):
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    print(f"f{f}: RightHand z={hand_z('mixamorig:RightArm'):.3f}  LeftHand z={hand_z('mixamorig:LeftArm'):.3f}")
print("PROBE_XU_DONE", flush=True)
