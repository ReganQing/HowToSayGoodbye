# -*- coding: utf-8 -*-
"""探针：C05 手臂绕 (0,1,0) ±90 后的手部位世界坐标，判定收臂/抬臂符号。"""
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


def rot(bone, axis, ang):
    pb = arm.pose.bones.get(bone)
    rest_q = pb.bone.matrix_local.to_quaternion()
    q_world = Quaternion(Vector(axis).normalized(), math.radians(ang))
    q_local = rest_q.inverted() @ q_world @ rest_q
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = q_local
    bpy.context.view_layer.update()
    hand = arm.matrix_world @ arm.pose.bones[bone.replace("Arm", "Hand")].head
    d = (arm.pose.bones[bone].tail - arm.pose.bones[bone].head)
    dW = (arm.matrix_world.to_3x3() @ d).normalized()
    print(f"{bone} axis={axis} ang={ang:+4d}  hand=({hand.x:+.2f},{hand.y:+.2f},{hand.z:+.2f}) "
          f"bonedir=({dW.x:+.2f},{dW.y:+.2f},{dW.z:+.2f})")


for bone in ("mixamorig:RightArm", "mixamorig:LeftArm"):
    for ang in (0, 90, -90):
        rot(bone, (0, 1, 0), ang)
print("PROBE_ARM_DONE", flush=True)
