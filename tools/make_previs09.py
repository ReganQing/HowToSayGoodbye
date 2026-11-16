"""shot09 预演：P02 老照片的缓慢推近（Ken Burns），推向爸爸（画面右侧）。
H3 以此为运动参考，再靠提示词补蒸汽/灯光微动。"""
from PIL import Image
import imageio.v3 as iio
import math

SRC = "assets/ref/P02/P02_v02.png" if False else "assets/ref/P02/P02_v01.png"
img = Image.open(SRC).convert("RGB")
W, H = img.size          # 1344x768
OUT_W, OUT_H = 1280, 720
N = 192
CX, CY = 0.70, 0.36      # 推近中心：爸爸（画面右侧坐着笑的工装男人）

def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))

frames = []
for f in range(N):
    t = ease(f / (N - 1))
    zoom = 1.06 + 0.16 * t          # 推近幅度：1.06 → 1.22
    cw, ch = W / zoom, H / zoom
    cx, cy = CX * W, CY * H
    # 限制裁切框不越界
    cx = min(max(cx, cw / 2), W - cw / 2)
    cy = min(max(cy, ch / 2), H - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    frames.append(img.crop(box).resize((OUT_W, OUT_H), Image.LANCZOS))

iio.imwrite("assets/previs/previs_shot09.mp4", frames, fps=24, codec="libx264", quality=7)
print("saved", len(frames))
