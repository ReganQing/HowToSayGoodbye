import imageio.v3 as iio
from PIL import Image
v05 = iio.imread("assets/h3_video/roughcut_v05.mp4", index=None)
idxs = [1199, 1200, 1259, 1260, 1300, 1332, 1400, 1451, 1452]
w, h = 426, 240
sheet = Image.new("RGB", (3*w, 3*h), (20,20,20))
for n, fi in enumerate(idxs):
    sheet.paste(Image.fromarray(v05[fi]).resize((w,h)), ((n%3)*w, (n//3)*h))
sheet.save("assets/h3_video/qc_v05_probe.jpg", quality=90)
print("ok", len(v05))
