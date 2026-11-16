# -*- coding: utf-8 -*-
"""探针：C05 tex_mesh_v08_animated 手臂/脊柱世界轴实测。
对候选旋转打印左右手世界坐标（z 抬高=举起，|y| 前移=前摆）。"""
import math, os, sys
import bpy
from mathutils import Quaternion, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLB = os.path.join(ROOT, "assets", "models", "C05", "tex_mesh_v08_animated.glb")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
pre = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
arm = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][-1]
arm.rotation_mode = "XYZ"
arm.location = (0, 0, 0.78)
bpy.context.view_layer.update()

def hand_pos():
    bpy.context.view_layer.update()
    r = arm.matrix_world @ arm.pose.bones["mixamorig:RightHand"].head
    l = arm.matrix_world @ arm.pose.bones["mixamorig:LeftHand"].head
    h = arm.matrix_world @ arm.pose.bones["mixamorig:Head"].head
    return (round(r.x,2), round(r.y,2), round(r.z,2)), (round(l.x,2), round(l.y,2), round(l.z,2)), (round(h.x,2), round(h.y,2), round(h.z,2))

def reset():
    for bn in ("RightArm","LeftArm","RightForeArm","LeftForeArm","Spine","Spine1","Spine2","Head"):
        pb = arm.pose.bones.get(f"mixamorig:{bn}")
        if pb:
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = Quaternion((1,0,0,0))

def rot(bn, axis, ang):
    pb = arm.pose.bones.get(f"mixamorig:{bn}")
    rest = pb.bone.matrix_local.to_quaternion()
    q = Quaternion(Vector(axis).normalized(), math.radians(ang))
    pb.rotation_quaternion = rest.inverted() @ q @ rest

print("rest R,L,Head:", hand_pos())
for bn in ("RightArm", "LeftArm"):
    for axis, ang in (((0,1,0), 45), ((0,1,0), -45), ((0,0,1), 45), ((0,0,1), -45), ((1,0,0), 30)):
        reset(); rot(bn, axis, ang)
        print(f"{bn} {axis}+{ang}:", hand_pos()[0 if bn=='RightArm' else 1])
# 肘
reset(); rot("RightArm",(0,0,1),45); rot("RightForeArm",(0,1,0),90)
print("R arm z45 + elbow y90 R:", hand_pos()[0])
# 脊柱
for ang in (20, 40):
    reset(); rot("Spine",(1,0,0),ang)
    print(f"Spine x+{ang} Head:", hand_pos()[2])
print("PROBE_DONE")
