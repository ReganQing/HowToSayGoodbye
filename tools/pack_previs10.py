import imageio.v3 as iio
import os
from PIL import Image
d = "assets/previs/frames10"
frames = [iio.imread(os.path.join(d, f"frame_{f:04d}.png")) for f in range(1, 193)]
iio.imwrite("assets/previs/previs_shot10.mp4", frames, fps=24, codec="libx264", quality=7)
# QC 拼图
idxs = [1, 40, 70, 100, 140, 190]
w, h = 640, 360
sheet = Image.new("RGB", (3*w, 2*h), (20,20,20))
for n, fi in enumerate(idxs):
    sheet.paste(Image.fromarray(frames[fi-1]).resize((w,h)), ((n%3)*w, (n//3)*h))
sheet.save("assets/previs/qc_previs10_full.jpg", quality=90)
print("saved", len(frames))
