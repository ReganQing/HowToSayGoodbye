# -*- coding: utf-8 -*-
"""shot24 预演 192 PNG → previs_shot24.mp4 + 规格校验 + ComfyUI input 登记。

Run: py -3.12 tools/pack_previs24.py
"""
import hashlib
import json
import os
import re
import shutil
import subprocess

import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(ROOT, "assets", "previs", "frames24")
OUT = os.path.join(ROOT, "assets", "previs", "previs_shot24.mp4")
REPORT = os.path.join(ROOT, "assets", "previs", "previs24_report.json")
INPUT_DIR = r"D:\Comfy-Desktop\ComfyUI-Shared\input"
MANIFEST = os.path.join(ROOT, "tmp_qc", "shot24_inputs.json")


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    names = sorted(n for n in os.listdir(FRAMES) if n.endswith(".png"))
    assert len(names) == 192, f"帧数异常 {len(names)}"
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-framerate", "24", "-start_number", "1",
           "-i", os.path.join(FRAMES, "frame_%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-movflags", "+faststart", OUT]
    subprocess.run(cmd, check=True, capture_output=True, text=True)

    r = subprocess.run([ff, "-i", OUT], capture_output=True, text=True)
    lines = [l.strip() for l in r.stderr.splitlines()
             if "Duration:" in l or "Video:" in l or "Stream #" in l]
    print("FFMPEG_SPEC")
    for l in lines:
        print("  ", l)
    assert any("Duration: 00:00:08.00" in l for l in lines), "时长不是 8.0s"
    assert any("1280x720" in l for l in lines), "分辨率不是 1280x720"
    assert any("24 fps" in l for l in lines), "帧率不是 24fps"

    m, size = md5(OUT), os.path.getsize(OUT)
    dst = os.path.join(INPUT_DIR, "previs_shot24.mp4")
    shutil.copy2(OUT, dst)
    assert md5(dst) == m, "ComfyUI input 拷贝后 MD5 不一致"
    print("COPIED ->", dst, m, size, "B")

    rep = json.load(open(REPORT, encoding="utf-8"))
    rep["packed_video"] = "assets/previs/previs_shot24.mp4"
    rep["packed_md5"] = m
    rep["packed_size"] = size
    rep["packed_spec"] = {"frames": 192, "fps": 24, "duration_s": 8.0,
                          "resolution": [1280, 720], "codec": "h264 / yuv420p"}
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)

    man = json.load(open(MANIFEST, encoding="utf-8"))
    man = [x for x in man if x["dst"] != "previs_shot24.mp4"]
    man.append({"src": "assets/previs/previs_shot24.mp4",
                "dst": "previs_shot24.mp4", "md5": m,
                "size": size, "input_md5": md5(dst)})
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)
    print("MANIFEST 3 inputs:", [x["dst"] for x in man])
    print("PACK_PREVIS24_DONE")


if __name__ == "__main__":
    main()
