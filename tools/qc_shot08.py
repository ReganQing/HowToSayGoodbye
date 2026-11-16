import imageio.v3 as iio
import numpy as np
from PIL import Image

frames = iio.imread("assets/h3_video/shot08_h3.mp4", index=None)
print("total frames:", len(frames))

lumas = []
for i in range(0, len(frames), 12):
    g = np.asarray(Image.fromarray(frames[i]).convert("L"))
    lumas.append((i, round(float(g.mean()), 1)))
print("luma:", lumas)

idxs = [0, 31, 63, 95, 127, 159, 191]
w, h = 640, 360
sheet = Image.new("RGB", (4*w, 2*h), (20,20,20))
for n, fi in enumerate(idxs):
    sheet.paste(Image.fromarray(frames[fi]).resize((w,h)), ((n%4)*w, (n//4)*h))
sheet.save("assets/h3_video/qc_shot08_h3.jpg", quality=90)
Image.fromarray(frames[150]).resize((1280,720)).save("assets/h3_video/qc_shot08_f150.png")
print("saved")
