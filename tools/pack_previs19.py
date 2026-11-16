# -*- coding: utf-8 -*-
"""把 frames19 的 192 张 PNG 合成 assets/previs/previs_shot19.mp4。

shot19 全渲一次性跑完 192 帧（不分三段），目的是让许宁右手的逐帧求解器
seed 连续演进，避免分段重启导致段间角度跳变。合成仍用 ffmpeg 按序读盘，
不在内存里同时驻留 192 张 720p 帧。

Run: py -3.12 tools/pack_previs19.py
"""
import os
import subprocess

import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(ROOT, "assets", "previs", "frames19")
OUT = os.path.join(ROOT, "assets", "previs", "previs_shot19.mp4")


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
