# -*- coding: utf-8 -*-
"""探针：C15 周远 骨轴实测（auto-rig 骨架，勿假设与 C05 一致）。
测：手臂 (0,1,0)±90、Spine (1,0,0)±45、Neck (0,0,1)±45 下手/头/胸的位移方向。"""
import math
import os
import bpy
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "assets", "models")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "C15", "tex_mesh_rigged.glb"))
bpy.context.view_layer.update()
arm = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][-1]
print("ARMATURE", arm.name, flush=True)
print("BONES", sorted(b.name for b in arm.pose.bones)[:40], flush=True)


def rot(bone, axis, ang):
    pb = arm.pose.bones.get(bone)
    if pb is None:
        print(bone, "MISSING", flush=True)
        return
    rest_q = pb.bone.matrix_local.to_quaternion()
    q_world = Quaternion(Vector(axis).normalized(), math.radians(ang))
    q_local = rest_q.inverted() @ q_world @ rest_q
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = q_local
    bpy.context.view_layer.update()


def report(tag, bone):
    pb = arm.pose.bones[bone]
    p = arm.matrix_world @ pb.head
    print(f"{tag} {bone}=({p.x:+.3f},{p.y:+.3f},{p.z:+.3f})", flush=True)


# baseline
bpy.context.view_layer.update()
report("base", "mixamorig:RightHand")
report("base", "mixamorig:LeftHand")
report("base", "mixamorig:Head")
report("base", "mixamorig:Spine1")

for ang in (90, -90):
    rot("mixamorig:RightArm", (0, 1, 0), ang)
    report(f"RArmY{ang:+d}", "mixamorig:RightHand")
rot("mixamorig:RightArm", (0, 1, 0), 0)
for ang in (90, -90):
    rot("mixamorig:LeftArm", (0, 1, 0), ang)
    report(f"LArmY{ang:+d}", "mixamorig:LeftHand")
rot("mixamorig:LeftArm", (0, 1, 0), 0)

for ang in (45, -45):
    rot("mixamorig:Spine", (1, 0, 0), ang)
    report(f"SpineX{ang:+d}", "mixamorig:Head")
rot("mixamorig:Spine", (1, 0, 0), 0)

for ang in (45, -45):
    rot("mixamorig:Neck", (0, 0, 1), ang)
    report(f"NeckZ{ang:+d}", "mixamorig:Head")
print("PROBE_C15_DONE", flush=True)
