from PIL import Image
import os
d = "assets/previs/frames10"
idxs = [1, 40, 70, 100, 140, 190]
w, h = 640, 360
sheet = Image.new("RGB", (3*w, 2*h), (20,20,20))
for n, fi in enumerate(idxs):
    im = Image.open(os.path.join(d, f"frame_{fi:04d}.png")).resize((w,h))
    sheet.paste(im, ((n%3)*w, (n//3)*h))
sheet.save("assets/previs/qc_previs10.jpg", quality=90)
print("ok")
