import bpy
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=r"assets/models/C10/tex_mesh_v08_animated.glb")
for ac in bpy.data.actions:
    print("ACTION:", ac.name, "range:", tuple(ac.frame_range))
# NLA 轨道
for o in bpy.context.scene.objects:
    if o.type == "ARMATURE" and o.animation_data:
        for tr in o.animation_data.nla_tracks:
            print("NLA:", tr.name, [s.name for s in tr.strips])
print("PROBE_DONE")
