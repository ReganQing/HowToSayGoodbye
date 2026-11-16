# -*- coding: utf-8 -*-
"""shot15+ 面容参考图裁切：从 8 张定稿设计稿的最左正面视图裁头肩。

对齐既有构图：`assets/ref_face/C05_v07_head.png` (267x317)、`C15_v02_head.png` (287x308)
—— 单人正面、头顶到下巴约占高度一半、含肩上缘、不混入其他视图/色卡/文字。

风格铁律（Ron 2026-11-13）：只从水彩定稿裁，绝不把写实 T-pose 建模图当面容参考。
写实 T-pose 图仅用于 Lux3D auto-rig（水彩画不出严格 T-pose，会 RIG_ELIGIBILITY_FAILED），
不进 H3 ref_images，因此不影响成片画风。

Run:
  py -3.12 tools/face_crop_shot15plus.py --preview   # 只裁 + 出联系表，不写台账
  py -3.12 tools/face_crop_shot15plus.py             # 正式写入台账
"""
import argparse
import hashlib
import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = r"."
REF = os.path.join(ROOT, "assets", "ref")
FACE = os.path.join(ROOT, "assets", "ref_face")
LEDGER = os.path.join(ROOT, "progress", "01_剧本分镜", "shot15+_参考图台账.json")

# (cid, 源图相对 assets/ref 路径, x0, y0, x1, y1, 说明)
# 坐标是全图宽高的比例；裁框按各稿正面视图的头部位置单独定，避免一刀切切掉头顶或混入色卡。
CROPS = [
    ("C06",  "C06/C06_v07.png",     0.060, 0.010, 0.345, 0.320, "许宁·成年"),
    ("C06b", "C06b/C06b_v03.png",   0.060, 0.010, 0.345, 0.320, "许宁·中老年居家·定稿"),
    ("C07",  "C07/C07_v07.png",     0.060, 0.010, 0.345, 0.320, "许宁·老年病号服"),
    ("C07b", "C07b/C07b_v02.png",   0.055, 0.005, 0.340, 0.315, "许宁·老年居家·定稿"),
    ("C11",  "C11/C11_v07.png",     0.060, 0.010, 0.345, 0.320, "妈妈·老年"),
    ("C16",  "C16/C16_v07.png",     0.060, 0.010, 0.345, 0.320, "女儿·成年"),
    ("C17",  "C17/C17_v07.png",     0.060, 0.005, 0.345, 0.315, "小满·演出裙（儿童头身比）"),
    ("C18",  "C18/C18_v03.png",     0.055, 0.010, 0.340, 0.320, "周远·老年·定稿"),
]


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="只裁图+联系表，不写台账")
    args = ap.parse_args()

    os.makedirs(FACE, exist_ok=True)
    records = []
    thumbs = []
    for cid, rel, x0, y0, x1, y1, note in CROPS:
        src = os.path.join(REF, rel.replace("/", os.sep))
        if not os.path.isfile(src):
            print(f"[{cid}] MISSING {src}")
            continue
        im = Image.open(src).convert("RGB")
        w, h = im.size
        box = (int(w * x0), int(h * y0), int(w * x1), int(h * y1))
        face = im.crop(box)
        ver = os.path.basename(rel).replace(".png", "")
        dst = os.path.join(FACE, f"{ver}_head.png")
        face.save(dst)
        records.append({
            "cid": cid, "note": note,
            "source": "assets/ref/" + rel,
            "source_size": [w, h], "source_md5": md5(src),
            "crop_frac": [x0, y0, x1, y1], "crop_px": list(box),
            "output": f"assets/ref_face/{ver}_head.png",
            "output_size": [face.size[0], face.size[1]],
            "visual_check": "pending", "verdict": "pending",
        })
        print(f"[{cid}] {w}x{h} crop{box} -> {face.size[0]}x{face.size[1]}  {dst}")
        thumbs.append((cid, face.copy()))

    # 联系表：4 列 x 2 行，每格等比缩到 220 宽，底部标角色号
    if thumbs:
        tw = 220
        cells = []
        for cid, im in thumbs:
            th = int(im.height * tw / im.width)
            cells.append((cid, im.resize((tw, th))))
        ch = max(c[1].height for c in cells)
        sheet = Image.new("RGB", (tw * 4, (ch + 26) * 2), (245, 243, 238))
        draw = ImageDraw.Draw(sheet)
        for i, (cid, im) in enumerate(cells):
            cx, cy = (i % 4) * tw, (i // 4) * (ch + 26)
            sheet.paste(im, (cx, cy))
            draw.text((cx + 6, cy + ch + 5), cid, fill=(40, 40, 40))
        sheet_path = os.path.join(FACE, "_contact_shot15plus.jpg")
        sheet.save(sheet_path, quality=90)
        print("CONTACT ->", sheet_path)

    if args.preview:
        print("PREVIEW ONLY，未写台账")
        return

    ledger = {}
    if os.path.isfile(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            ledger = json.load(f)
    ledger["face_crops"] = {
        "created": "2026-11-13",
        "policy": "仅从水彩定稿裁；写实 T-pose 建模图不进 H3 ref_images",
        "reference_composition": ["assets/ref_face/C05_v07_head.png", "assets/ref_face/C15_v02_head.png"],
        "items": records,
    }
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
    print(f"LEDGER -> {LEDGER} (face_crops {len(records)} 条, jobs {len(ledger.get('jobs', []))} 条)")


if __name__ == "__main__":
    sys.exit(main())
