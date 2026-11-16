"""探针：导入 shot10 场景 + C05 坐姿，从高处俯瞰渲染一张，打印关键坐标。"""
import bpy, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

exec(open(os.path.join(ROOT, "tools", "previs_shot10.py"), encoding="utf-8").read().split("def main()")[0])

clean_scene()
movers = build_bus_interior()
add_lighting()

pre = set(bpy.context.scene.objects)
import_glb(os.path.join(MODELS, "C05", "tex_mesh_v08_sitting.glb"))
new = [o for o in bpy.context.scene.objects if o not in pre]
print("imported objects:", [(o.name, o.type) for o in new][:10])
for o in new:
    if o.type == "MESH" and "棱角球" in o.name:
        bpy.data.objects.remove(o, do_unlink=True)
arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE" and o in new] or \
       [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
xu = arms[-1]
xu.rotation_mode = "XYZ"
xu.location = (SEAT_X - 0.1, SEAT_Y, 0.0)
xu.rotation_euler = (0, 0, math.radians(XU_ROT))
bpy.context.view_layer.update()

acts = find_actions()
if "sit" in acts and xu.animation_data is None:
    xu.animation_data_create()
xu.animation_data.action = acts.get("sit")

scene = bpy.context.scene
scene.frame_set(40)
bpy.context.view_layer.update()

if xu.pose.bones.get("mixamorig:Head"):
    h = xu.matrix_world @ xu.pose.bones["mixamorig:Head"].head
    print("XU head world:", tuple(round(v, 2) for v in h))
    print("XU root world:", tuple(round(v, 2) for v in xu.matrix_world.translation))
    # 臀/脚
    for bn in ("mixamorig:Hips", "mixamorig:RightFoot", "mixamorig:RightUpLeg"):
        pb = xu.pose.bones.get(bn)
        if pb:
            w = xu.matrix_world @ pb.head
            print(bn, tuple(round(v, 2) for v in w))

# 俯瞰相机
cam_data = bpy.data.cameras.new("probe_cam")
cam_data.lens = 24
cam = bpy.data.objects.new("probe_cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = (-2.5, -4.5, 4.5)
tgt = bpy.data.objects.get("seat_xu_pan").location
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 960
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(ROOT, "assets", "previs", "probe_shot10_topview.png")
bpy.ops.render.render(write_still=True)
print("saved topview")
