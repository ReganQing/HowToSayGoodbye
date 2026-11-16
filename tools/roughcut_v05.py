# -*- coding: utf-8 -*-
"""粗剪 v0.5 = v0.4 + 过场卡「火车站」+ shot06 火车站送别。

卡片版式与 v0.4 一致：近黑底、宋体标题居中偏上、NotoSansSC 灰色小字副标题。
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

V04 = "assets/h3_video/roughcut_v04.mp4"
SHOT06 = "assets/h3_video/shot06_h3.mp4"
OUT = "assets/h3_video/roughcut_v05.mp4"


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
    rdr = iio.get_reader(V04)
    v04 = [f for f in rdr]
    rdr.close()
    print("v04 frames:", len(v04))

    # v0.4 结构：13 黑场 + 53 片头卡余下 + 870 主体 + 12 冻结 + 60 过场卡 + 192 shot05 + 84 尾卡
    head = v04[:13]
    title_card = make_card("告别与成长", "实验镜头粗剪 · v0.5", 53)
    body = v04[66:960]            # 870 主体 + 12 冻结 + 60 shot05 前的过场卡之后…见下
    # 稳妥做法：直接按 v0.4 的段落边界切片
    body_main = v04[66:936]       # 主体
    tail_hold = v04[936:948]      # shot04 结尾冻结
    seg_card_05 = v04[948:1008]   # 「第二天清晨」卡
    shot05 = v04[1008:1200]       # shot05
    end_card = v04[1200:]         # 尾卡（含淡入淡出）
    print("segments:", len(body_main), len(tail_hold), len(seg_card_05), len(shot05), len(end_card))

    # 新过场卡 + shot06
    seg_card_06 = make_card("火车站", "送她进站，隔着闸机挥了两次手", 60)
    rdr6 = iio.get_reader(SHOT06)
    shot06 = [f for f in rdr6]
    rdr6.close()
    print("shot06 frames:", len(shot06))

    out = (head + title_card + body_main + tail_hold + seg_card_05 + shot05
           + seg_card_06 + shot06 + end_card)
    print("v05 frames:", len(out), "=", len(out) / FPS, "s")

    iio.mimwrite(OUT, out, fps=FPS, codec="libx264", quality=7)
    print("saved", OUT)


main()
