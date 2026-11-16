import imageio.v3 as iio
from PIL import Image
frames = iio.imread("assets/h3_video/shot07_h3.mp4", index=None)
w, h = 640, 360
sheet = Image.new("RGB", (4*w, h), (20,20,20))
for n, fi in enumerate([40, 50, 58, 70]):
    sheet.paste(Image.fromarray(frames[fi]).resize((w,h)), (n*w, 0))
sheet.save("assets/h3_video/qc_shot07_trans.jpg", quality=90)
print("ok")
