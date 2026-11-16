# -*- coding: utf-8 -*-
"""把 assets/previs/frames22 的 192 张 PNG 合成 assets/previs/previs_shot22.mp4。

shot22 与 shot19/20/21 一样采用 192 帧一次性全渲：三只工作手每帧坐标下降
都以上一帧解为起点，分段渲染会让求解器 seed 断链，因此不分三段。

Run: py -3.12 tools/pack_previs22.py
"""
import hashlib
import json
import os
import subprocess

import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(ROOT, "assets", "previs", "frames22")
OUT = os.path.join(ROOT, "assets", "previs", "previs_shot22.mp4")
REPORT = os.path.join(ROOT, "assets", "previs", "previs22_report.json")


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    pngs = [f"frame_{i:04d}.png" for i in range(1, 193)]
    missing = [n for n in pngs if not os.path.exists(os.path.join(FRAMES, n))]
    assert not missing, f"缺帧 {len(missing)} 张，例：{missing[:5]}"
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-framerate", "24", "-start_number", "1",
           "-i", os.path.join(FRAMES, "frame_%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-movflags", "+faststart", OUT]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    print("PACKED", os.path.relpath(OUT, ROOT), os.path.getsize(OUT), "bytes", md5(OUT))
    if os.path.exists(REPORT):
        with open(REPORT, encoding="utf-8") as f:
            r = json.load(f)
        r["packed_video"] = os.path.relpath(OUT, ROOT).replace("\\", "/")
        r["packed_md5"] = md5(OUT)
        r["packed_size"] = os.path.getsize(OUT)
        with open(REPORT, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
        print("REPORT updated", os.path.relpath(REPORT, ROOT))
    print("PACK_PREVIS22_DONE")


if __name__ == "__main__":
    main()
