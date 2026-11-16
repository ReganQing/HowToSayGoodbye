# -*- coding: utf-8 -*-
"""把 frames18 的 192 张 PNG 合成 assets/previs/previs_shot18.mp4。

三段式渲染（1-64 / 65-128 / 129-192）全部完成后再跑，避免内存里同时驻留
192 张 720p 帧；直接用 ffmpeg 按序读盘。

Run: py -3.12 tools/pack_previs18.py
"""
import os
import subprocess

import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(ROOT, "assets", "previs", "frames18")
OUT = os.path.join(ROOT, "assets", "previs", "previs_shot18.mp4")


def main():
    missing = [f for f in range(1, 193)
               if not os.path.exists(os.path.join(FRAMES, f"frame_{f:04d}.png"))]
    if missing:
        raise RuntimeError(f"缺 {len(missing)} 帧，首缺 {missing[:5]}")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg, "-y", "-framerate", "24", "-start_number", "1",
           "-i", os.path.join(FRAMES, "frame_%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           "-movflags", "+faststart", OUT]
    subprocess.run(cmd, check=True)
    print("saved", OUT, os.path.getsize(OUT), "B")


if __name__ == "__main__":
    main()
