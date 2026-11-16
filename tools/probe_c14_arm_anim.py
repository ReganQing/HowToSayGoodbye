# -*- coding: utf-8 -*-
"""探针：C14 手臂轴向实测（抬臂/前伸/侧举的世界轴与符号）。"""
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
print("bones sample:", [b.name for b in arm.pose.bones][:8], flush=True)


def rot(bone, axis, ang):
    pb = arm.pose.bones.get(bone)
    if pb is None:
        print(f"{bone} MISSING", flush=True)
        return
    rest_q = pb.bone.matrix_local.to_quaternion()
    q_world = Quaternion(Vector(axis).normalized(), math.radians(ang))
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = rest_q.inverted() @ q_world @ rest_q
    bpy.context.view_layer.update()
    hand = arm.matrix_world @ arm.pose.bones[bone.replace("Arm", "Hand")].head
    d = (arm.pose.bones[bone].tail - arm.pose.bones[bone].head)
    dW = (arm.matrix_world.to_3x3() @ d).normalized()
    print(f"{bone} axis={axis} ang={ang:+4d}  hand=({hand.x:+.2f},{hand.y:+.2f},{hand.z:+.2f}) "
          f"bonedir=({dW.x:+.2f},{dW.y:+.2f},{dW.z:+.2f})", flush=True)


for bone in ("mixamorig:RightArm", "mixamorig:LeftArm"):
    rot(bone, (0, 0, 0), 0)
    for axis in ((0, 1, 0), (0, 0, 1)):
        for ang in (90, -90):
            rot(bone, axis, ang)
    print("---", flush=True)
print("PROBE_C14_DONE", flush=True)
