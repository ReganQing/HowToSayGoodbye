from PIL import Image
import os
d = "assets/previs/frames08"
idxs = [1, 12, 28, 50, 80, 130, 190]
w, h = 640, 360
sheet = Image.new("RGB", (4*w, 2*h), (20,20,20))
for n, fi in enumerate(idxs):
    im = Image.open(os.path.join(d, f"frame_{fi:04d}.png")).resize((w,h))
    sheet.paste(im, ((n%4)*w, (n//4)*h))
sheet.save("assets/previs/qc_previs08.jpg", quality=90)
print("ok")
