"""探针：许宁坐姿，头部分别转 +28 / -28 度，对比哪边朝向车窗（+x）。"""
import bpy, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(ROOT, "tools", "previs_shot10.py"), encoding="utf-8").read().split("def main()")[0])

clean_scene()
build_bus_interior()
add_lighting()

pre = set(bpy.context.scene.objects)
import_glb(os.path.join(MODELS, "C05", "tex_mesh_v08_sitting.glb"))
new = [o for o in bpy.context.scene.objects if o not in pre]
for o in new:
    if o.type == "MESH" and "棱角球" in o.name:
        bpy.data.objects.remove(o, do_unlink=True)
arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE" and o in new] or \
       [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
xu = arms[-1]
xu.rotation_mode = "XYZ"
xu.location = (SEAT_X - 0.1, SEAT_Y, 0.78)
xu.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
acts = find_actions()
xu.animation_data_create()
xu.animation_data.action = acts["sit"]
removed = strip_arm_channels(acts)
print("stripped:", removed)

scene = bpy.context.scene
scene.frame_set(140)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 640
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

cam_data = bpy.data.cameras.new("c")
cam_data.lens = 35
cam = bpy.data.objects.new("c", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = (1.40, -2.15, 1.46)
scene.camera = cam

for label, turn in (("pos", 28.0), ("neg", -28.0)):
    # 重置头部：重新评估 action 后再加旋转
    scene.frame_set(140)
    rotate_pose_bone_world(xu, "mixamorig:Head", (1, 0, 0), -5.0)
    rotate_pose_bone_world(xu, "mixamorig:Head", (0, 0, 1), turn)
    bpy.context.view_layer.update()
    h = xu.matrix_world @ xu.pose.bones["mixamorig:Head"].head
    cam.rotation_euler = (h - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(ROOT, "assets", "previs", f"probe_turn_{label}.png")
    bpy.ops.render.render(write_still=True)
    # 打印鼻尖近似：头部世界矩阵的 -Y? 用 head 的 +Y? 打印矩阵各轴
    m = xu.pose.bones["mixamorig:Head"].matrix
    print(label, "head local Y axis world:", tuple(round(v, 2) for v in (xu.matrix_world.to_3x3() @ m.to_3x3().col[1])))
print("done")
