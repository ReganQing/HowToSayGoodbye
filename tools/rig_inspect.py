# -*- coding: utf-8 -*-
"""Inspect rigged GLB: bones, skin weights, dimensions.

Usage:
  python3 tools/rig_inspect.py <glb> [<glb> ...]
"""
import json
import struct
import sys


def read_glb_json(path):
    data = open(path, "rb").read()
    assert data[:4] == b"glTF", "not a GLB"
    jlen = struct.unpack("<I", data[12:16])[0]
    return json.loads(data[20:20 + jlen].decode("utf-8"))


def inspect(path):
    g = read_glb_json(path)
    skins = g.get("skins", [])
    nodes = g.get("nodes", [])
    joints_total = sum(len(s.get("joints", [])) for s in skins)
    bone_nodes = [n for n in nodes if any(n.get("name") in s.get("joints", []) for s in skins)]
    # mesh with skin
    skinned_meshes = 0
    prim_skin = 0
    for m in g.get("meshes", []):
        for p in m.get("primitives", []):
            if "JOINTS_0" in p.get("attributes", {}):
                skinned_meshes += 1
            if "skin" in m:
                prim_skin += 1
    # accessor min/max for POSITION
    dims = None
    for m in g.get("meshes", []):
        for p in m.get("primitives", []):
            ai = p.get("attributes", {}).get("POSITION")
            if ai is not None:
                acc = g["accessors"][ai]
                mn, mx = acc.get("min"), acc.get("max")
                if mn and mx:
                    dims = [round(mx[i] - mn[i], 3) for i in range(3)]
    names = []
    for s in skins:
        for j in s.get("joints", []):
            nm = nodes[j].get("name", f"node{j}") if j < len(nodes) else f"node{j}"
            names.append(nm)
    print(f"== {path}")
    print(f"   skins={len(skins)} joints={joints_total} skinned_mesh_prims={skinned_meshes} "
          f"dims(xyz)={dims} tris_ok={'yes' if skinned_meshes else 'NO-SKIN'}")
    print(f"   bones: {', '.join(names)}")
    return {"joints": joints_total, "dims": dims}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        inspect(p)
