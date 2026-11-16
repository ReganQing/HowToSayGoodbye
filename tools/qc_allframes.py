# -*- coding: utf-8 -*-
"""逐帧审查：把成片全部 192 帧拼成 8 张 24 格 contact sheet（每格带帧号）。
用法: python tools/qc_allframes.py <mp4> <out_dir> [n_frames]
"""
import os
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageDraw

ff = imageio_ffmpeg.get_ffmpeg_exe()

def main(mp4, out_dir, n=192):
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, "_frames")
    os.makedirs(tmp, exist_ok=True)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    subprocess.run([ff, "-y", "-i", mp4, "-fps_mode", "passthrough",
                    os.path.join(tmp, "f_%04d.png"), "-loglevel", "error"], check=True)
    frames = sorted(os.listdir(tmp))
    print("extracted", len(frames))
    per_sheet = 24
    cols, rows = 6, 4
    tw = 300
    for s in range(0, len(frames), per_sheet):
        batch = frames[s:s + per_sheet]
        ims = []
        for fn in batch:
            im = Image.open(os.path.join(tmp, fn)).convert("RGB")
            w, h = im.size
            th = int(h * tw / w)
            ims.append((im.resize((tw, th)), int(fn.split("_")[1].split(".")[0])))
        th = ims[0][0].size[1]
        sheet = Image.new("RGB", (tw * cols, (th + 14) * rows), (25, 25, 25))
        d = ImageDraw.Draw(sheet)
        for i, (im, no) in enumerate(ims):
            x = (i % cols) * tw
            y = (i // cols) * (th + 14)
            sheet.paste(im, (x, y + 14))
            d.text((x + 4, y + 2), f"f{no}", fill=(255, 230, 0))
        out = os.path.join(out_dir, f"sheet_{s//per_sheet + 1:02d}_f{s+1:03d}-{s+len(batch):03d}.jpg")
        sheet.save(out, quality=85)
        print("saved", out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 192)
