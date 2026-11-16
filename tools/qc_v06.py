import imageio.v3 as iio
from PIL import Image
frames = iio.imread("assets/h3_video/roughcut_v06.mp4", index=None)
print("total:", len(frames))
idxs = [12, 66, 1259, 1332, 1511, 1512, 1703, 1704, 1787]
w, h = 426, 240
cols = 3
rows = (len(idxs)+cols-1)//cols
sheet = Image.new("RGB", (cols*w, rows*h), (20,20,20))
for n, fi in enumerate(idxs):
    sheet.paste(Image.fromarray(frames[fi]).resize((w,h)), ((n%cols)*w, (n//cols)*h))
sheet.save("assets/h3_video/qc_v06.jpg", quality=90)
print("ok")
