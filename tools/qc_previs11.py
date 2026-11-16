from PIL import Image
import os
d = "assets/previs/frames11"
idxs = [1, 60, 120, 190]
w, h = 640, 360
sheet = Image.new("RGB", (2*w, 2*h), (20,20,20))
for n, fi in enumerate(idxs):
    im = Image.open(os.path.join(d, f"frame_{fi:04d}.png")).resize((w,h))
    sheet.paste(im, ((n%2)*w, (n//2)*h))
sheet.save("assets/previs/qc_previs11.jpg", quality=90)
print("ok")
