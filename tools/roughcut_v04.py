# -*- coding: utf-8 -*-
"""粗剪 v0.4 = v0.3（开头版本卡换 v0.4、尾部冻结裁短）+ 过场卡「第二天清晨」+ shot05。

卡片版式复刻 v0.3：近黑底、宋体标题居中偏上、NotoSansSC 灰色小字副标题。
"""
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

V03 = "assets/h3_video/roughcut_v03.mp4"
SHOT05 = "assets/h3_video/shot05_h3.mp4"
OUT = "assets/h3_video/roughcut_v04.mp4"


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
    rdr = iio.get_reader(V03)
    v03 = [f for f in rdr]
    rdr.close()
    print("v03 frames:", len(v03))

    # 新片头卡（66f，与 v0.3 片头卡等长）
    title_card = make_card("告别与成长", "实验镜头粗剪 · v0.4", 66)

    # 过场卡 + shot05
    seg_card = make_card("第二天清晨", "她把焐热的发带递给妈妈", 60)
    rdr5 = iio.get_reader(SHOT05)
    shot05 = [f for f in rdr5]
    rdr5.close()
    print("shot05 frames:", len(shot05))

    # 组装：v03 前 13 帧（黑场淡入）+ 新片头卡余下部分 + v03 主体（66~936，936 起是尾卡）
    # + shot04 结尾 12 帧冻结 + 「第二天清晨」卡 + shot05 + v03 原尾卡（含淡入淡出）
    body = v03[66:936]
    tail_hold = [v03[935]] * 12
    end_card = v03[936:1020]
    out = v03[:13] + title_card[13:] + body + tail_hold + seg_card + shot05 + end_card
    print("v04 frames:", len(out), "=", len(out) / FPS, "s")

    iio.mimwrite(OUT, out, fps=FPS, codec="libx264", quality=7)
    print("saved", OUT)


main()
