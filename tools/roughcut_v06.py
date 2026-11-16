# -*- coding: utf-8 -*-
"""粗剪 v0.6 = v0.5 + 过场卡「大二暑假」+ shot07 找爸爸的工友（南方线）。"""
import numpy as np
import imageio.v2 as iio
from PIL import Image, ImageDraw, ImageFont

FPS = 24
W, H = 1280, 720
TITLE_FONT = "<LOCAL_PATH>"
BODY_FONT = "<LOCAL_PATH>"
BG = (13, 13, 15)
TITLE_COLOR = (236, 230, 214)
SUB_COLOR = (150, 145, 135)

V05 = "assets/h3_video/roughcut_v05.mp4"
SHOT07 = "assets/h3_video/shot07_h3.mp4"
OUT = "assets/h3_video/roughcut_v06.mp4"


def make_card(title, sub, n_frames, fade_in=12, fade_out=12):
    base = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(base)
    t_font = ImageFont.truetype(TITLE_FONT, 66)
    s_font = ImageFont.truetype(BODY_FONT, 26)
    tb = draw.textbbox((0, 0), title, font=t_font)
    sb = draw.textbbox((0, 0), sub, font=s_font)
    draw.text(((W - (tb[2] - tb[0])) / 2 - tb[0], 318), title, font=t_font, fill=TITLE_COLOR)
    draw.text(((W - (sb[2] - sb[0])) / 2 - sb[0], 388), sub, font=s_font, fill=SUB_COLOR)
    arr = np.asarray(base, dtype=np.float32)
    frames = []
    for f in range(n_frames):
        a = 1.0
        if f < fade_in:
            a = f / fade_in
        elif f >= n_frames - fade_out:
            a = max(0.0, (n_frames - 1 - f) / fade_out)
        frames.append((arr * a).astype(np.uint8))
    return frames


def main():
    rdr = iio.get_reader(V05)
    v05 = [f for f in rdr]
    rdr.close()
    print("v05 frames:", len(v05))
    assert len(v05) == 1536, "v0.5 边界变了，先核对段落"

    head_black = v05[:13]
    body = v05[66:1452]      # 片头卡后 ~ shot06 末
    end_card = v05[1452:]    # 尾卡（含淡入淡出）
    print("segments:", len(head_black), len(body), len(end_card))

    title_card = make_card("告别与成长", "实验镜头粗剪 · v0.6", 53)
    seg_card_07 = make_card("大二暑假", "旧宿舍拆了，工友叔叔带她沿街慢慢走", 60)

    rdr7 = iio.get_reader(SHOT07)
    shot07 = [f for f in rdr7]
    rdr7.close()
    print("shot07 frames:", len(shot07))

    out = head_black + title_card + body + seg_card_07 + shot07 + end_card
    print("v06 frames:", len(out), "=", len(out) / FPS, "s")

    iio.mimwrite(OUT, out, fps=FPS, codec="libx264", quality=7)
    print("saved", OUT)


main()
