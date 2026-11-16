# -*- coding: utf-8 -*-
"""探针：导入 C01/C09，分别套用 shot05 / shot04 姿态，打印关键骨骼世界坐标。
目的：诊断 shot05 坐姿轴向错误，对比 shot04（已定稿）的骨骼朝向。"""
import math
import os

import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")

POSE05_G = [
    ("mixamorig:RightUpLeg",  (1, 0, 0), -88),
    ("mixamorig:RightLeg",    (1, 0, 0), 85),
    ("mixamorig:Spine",       (1, 0, 0), 4),
    ("mixamorig:Neck",        (1, 0, 0), 6),
    ("mixamorig:Head",        (1, 0, 0), 4),
    ("mixamorig:LeftArm",     (0, 0, 1), -52),
    ("mixamorig:LeftForeArm", (0, 0, 1), -20),
    ("mixamorig:RightForeArm",(0, 0, 1), 12),
]
POSE05_M = [
    ("mixamorig:RightUpLeg",  (1, 0, 0), -88),
    ("mixamorig:RightLeg",    (1, 0, 0), 85),
    ("mixamorig:Spine",       (1, 0, 0), 10),
    ("mixamorig:Neck",        (1, 0, 0), 18),
    ("mixamorig:Head",        (1, 0, 0), 12),
    ("mixamorig:RightArm",    (0, 0, 1), 52),
    ("mixamorig:RightForeArm",(0, 0, 1), 20),
    ("mixamorig:LeftForeArm", (0, 0, 1), -12),
]


def clean():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)


def bend_axis(rot_z_deg):
    t = math.radians(rot_z_deg)
    return (-math.cos(t), -math.sin(t), 0.0)


def rotate_pose_bone_world(arm_obj, bone_name, world_axis, angle_deg):
    pb = arm_obj.pose.bones.get(bone_name)
    if pb is None:
        print("  !! missing bone", bone_name)
        return False
    rest_q = pb.bone.matrix_local.to_quaternion()
    q_world = Quaternion(Vector(world_axis).normalized(), math.radians(angle_deg))
    q_local = rest_q.inverted() @ q_world @ rest_q
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = q_local
    return True


def report(arm_obj, tag):
    bpy.context.view_layer.update()
    M = arm_obj.matrix_world
    names = ["mixamorig:Hips", "mixamorig:Spine", "mixamorig:Head",
             "mixamorig:RightUpLeg", "mixamorig:RightLeg", "mixamorig:RightFoot",
             "mixamorig:RightArm", "mixamorig:RightForeArm", "mixamorig:RightHand",
             "mixamorig:LeftArm", "mixamorig:LeftForeArm", "mixamorig:LeftHand"]
    print(f"--- {tag} ---")
    for n in names:
        pb = arm_obj.pose.bones.get(n)
        if pb is None:
            print(f"  {n}: MISSING")
            continue
        p = M @ pb.head
        # 骨骼朝向（世界系）
        tail = M @ pb.tail
        d = (tail - p).normalized()
        print(f"  {n}: head=({p.x:.2f},{p.y:.2f},{p.z:.2f}) dir=({d.x:.2f},{d.y:.2f},{d.z:.2f})")


def run_case(glb, pos, rot_z, pose, tag):
    pre = set(bpy.context.scene.objects)
    import_glb(os.path.join(MODELS, glb.split("/")[0], glb.split("/")[1]))
    new = [o for o in bpy.context.scene.objects if o not in pre]
    for o in new:
        if o.type == "MESH" and "棱角球" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
    arm_obj = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][-1]
    arm_obj.location = pos
    arm_obj.rotation_euler = (0, 0, math.radians(rot_z))
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")
    lean = bend_axis(rot_z)
    for bone, axis, angle in pose:
        ax = lean if axis == "lean" else axis
        rotate_pose_bone_world(arm_obj, bone, ax, angle)
    bpy.ops.object.mode_set(mode="OBJECT")
    report(arm_obj, tag)
    return arm_obj


def main():
    clean()
    # 姿态前：T-pose 参考（rot=0 与 rot=180 各看一眼朝向）
    run_case("C01/tex_mesh_v04_rigged.glb", (0, 0, 0.10), 0, [], "C01 T-pose rot=0")
    run_case("C01/tex_mesh_v04_rigged.glb", (0.55, -1.25, 0.10), 0, POSE05_G, "C01 许宁 POSE05 rot=0")
    run_case("C09/tex_mesh_v04_rigged_scaled16.glb", (1.05, -1.22, 0.10), 0, POSE05_M, "C09 妈妈 POSE05 rot=0")
    print("PROBE_DONE", flush=True)


main()
