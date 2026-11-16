import imageio.v3 as iio
from PIL import Image, ImageDraw, ImageFont
v05 = iio.imread("assets/h3_video/roughcut_v05.mp4", index=None)
idxs = [1199, 1200, 1210, 1250, 1259, 1260]
font = ImageFont.truetype("<LOCAL_PATH>", 28)
w, h = 426, 240
sheet = Image.new("RGB", (3*w, 2*h), (20,20,20))
for n, fi in enumerate(idxs):
    im = Image.fromarray(v05[fi]).resize((w,h))
    d = ImageDraw.Draw(im)
    d.rectangle([0,0,110,36], fill=(0,0,0))
    d.text((8,4), f"f{fi}", font=font, fill=(255,255,0))
    sheet.paste(im, ((n%3)*w, (n//3)*h))
sheet.save("assets/h3_video/qc_v05_labeled.jpg", quality=90)
print("ok")
