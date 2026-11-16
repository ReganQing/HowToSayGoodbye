# -*- coding: utf-8 -*-
"""从水彩角色参考图裁出"头肩特写"，作为 H3 ref_images 面容锚定输入。

裁剪目标：头顶到下巴的高度占裁剪图高度约 55%，含肩部上缘，
让人脸在参考构图中占比最大（H3 max 模式按短边 2048 缩放，不放大，
裁剪只改变面部占比、不损失面部原始像素）。

Run:
  python tools/face_crop.py
"""
import os
from PIL import Image, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "assets", "ref")

# (asset, x0_frac, x1_frac, y0_frac, y1_frac)  -- fractions of full image
# 依据目检：C08 头顶~6% 下巴~25%；C01 头顶~4% 下巴~22%；肩宽约 30%-70%
CROPS = {
    "C08": (0.20, 0.80, 0.01, 0.39),
    "C01": (0.18, 0.82, 0.00, 0.37),
}


def crop_face(cid, box):
    src = os.path.join(REF, cid, f"{cid}_v03.png")
    dst = os.path.join(REF, cid, f"{cid}_face_crop.png")
    im = Image.open(src).convert("RGB")
    w, h = im.size
    x0, x1 = int(w * box[0]), int(w * box[1])
    y0, y1 = int(h * box[2]), int(h * box[3])
    face = im.crop((x0, y0, x1, y1))
    # 轻微锐化+对比度，强化面容信息（水彩风格不变）
    face = ImageEnhance.Contrast(face).enhance(1.05)
    face = ImageEnhance.Sharpness(face).enhance(1.15)
    face.save(dst)
    print(f"{cid}: {w}x{h} -> {face.size[0]}x{face.size[1]}  {dst}")
    return dst


if __name__ == "__main__":
    for cid, box in CROPS.items():
        crop_face(cid, box)
