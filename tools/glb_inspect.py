# -*- coding: utf-8 -*-
"""Inspect GLB files: meshes, triangles, materials, textures, bounding box.

Usage:
  python3 tools/glb_inspect.py <file.glb> [<file.glb> ...]
"""
import json
import struct
import sys

COMP = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
TYPE_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"glTF":
        raise ValueError("not a GLB")
    json_len, bin_len = struct.unpack("<II", data[12:20])
    gltf = json.loads(data[20:20 + json_len].decode("utf-8"))
    bin_start = 20 + json_len + 8
    bin_data = data[bin_start:bin_start + bin_len]
    return gltf, bin_data


def png_size(b):
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", b[16:24])
    return w, h


def jpg_size(b):
    if b[:2] != b"\xff\xd8":
        return None
    i = 2
    while i < len(b) - 9:
        if b[i] != 0xFF:
            i += 1
            continue
        marker = b[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3):
            h, w = struct.unpack(">HH", b[i + 5:i + 9])
            return w, h
        seg = struct.unpack(">H", b[i + 2:i + 4])[0]
        i += 2 + seg
    return None


def inspect(path):
    gltf, bin_data = read_glb(path)
    accessors = gltf.get("accessors", [])
    meshes = gltf.get("meshes", [])
    materials = gltf.get("materials", [])
    textures = gltf.get("textures", [])
    images = gltf.get("images", [])
    nodes = gltf.get("nodes", [])

    total_tris = 0
    total_verts = 0
    mn = [float("inf")] * 3
    mx = [float("-inf")] * 3
    for m in meshes:
        for p in m.get("primitives", []):
            acc = accessors[p["attributes"]["POSITION"]]
            total_verts += acc["count"]
            if "indices" in p:
                total_tris += accessors[p["indices"]]["count"] // 3
            else:
                total_tris += acc["count"] // 3
            for i in range(3):
                mn[i] = min(mn[i], acc["min"][i])
                mx[i] = max(mx[i], acc["max"][i])
    dims = [round(mx[i] - mn[i], 3) for i in range(3)]

    tex_info = []
    for img in images:
        bv = img.get("bufferView")
        if bv is None:
            tex_info.append(f"{img.get('uri', img.get('name', '?'))}(external)")
            continue
        view = gltf["bufferViews"][bv]
        blob = bin_data[view.get("byteOffset", 0):view.get("byteOffset", 0) + view["byteLength"]]
        size = png_size(blob) or jpg_size(blob)
        mime = img.get("mimeType", "?")
        tex_info.append(f"{size[0]}x{size[1]}({mime.split('/')[-1]})" if size else f"{len(blob)}B({mime})")

    mat_names = [m.get("name", "?") for m in materials]
    pbr = sum(1 for m in materials if "pbrMetallicRoughness" in m)
    print(f"== {path}")
    print(f"   meshes={len(meshes)} nodes={len(nodes)} tris={total_tris} verts={total_verts}")
    print(f"   bbox_dims(xyz)={dims} materials={len(materials)}(pbr={pbr}) textures={len(textures)}")
    if tex_info:
        print(f"   texture_sizes={tex_info}")
    if mat_names:
        print(f"   material_names={mat_names[:8]}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        inspect(p)
