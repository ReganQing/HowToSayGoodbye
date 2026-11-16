# -*- coding: utf-8 -*-
"""Download Lux3D task result files (GLB/ZIP) to assets/models/.

Usage:
  python3 tools/lux3d_fetch.py <asset_id> <result_url> [<result_url> ...]

Example:
  python3 tools/lux3d_fetch.py C01 https://.../C01.glb
"""
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_ROOT = os.path.join(ROOT, "assets", "models")


def fetch(url, dest):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)
    return len(data)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    asset_id = sys.argv[1]
    dest_dir = os.path.join(OUT_ROOT, asset_id)
    for url in sys.argv[2:]:
        name = url.split("?")[0].rstrip("/").split("/")[-1] or "result.bin"
        if "." not in name:
            name += ".glb"
        dest = os.path.join(dest_dir, name)
        size = fetch(url, dest)
        print(f"OK\t{dest}\t{size} bytes", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
