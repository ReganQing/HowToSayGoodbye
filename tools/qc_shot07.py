import imageio.v3 as iio
import numpy as np
from PIL import Image

frames = iio.imread("assets/h3_video/shot07_h3.mp4", index=None)
print("total frames:", len(frames))

# luma stats every 12 frames
lumas = []
for i in range(0, len(frames), 12):
    g = np.asarray(Image.fromarray(frames[i]).convert("L"))
    lumas.append((i, round(float(g.mean()), 1)))
print("luma:", lumas)

# contact sheet 7 frames
idxs = [0, 31, 63, 95, 127, 159, 191]
cols, rows = 4, 2
w, h = 640, 360
sheet = Image.new("RGB", (cols * w, rows * h), (20, 20, 20))
for n, fi in enumerate(idxs):
    im = Image.fromarray(frames[fi]).resize((w, h))
    sheet.paste(im, ((n % cols) * w, (n // cols) * h))
sheet.save("assets/h3_video/qc_shot07_h3.jpg", quality=90)

# zoom on pointing frame ~f96 (frame index 96)
Image.fromarray(frames[96]).resize((1280, 720)).save("assets/h3_video/qc_shot07_f96.png")
print("saved sheet + f96 zoom")
