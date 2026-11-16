# -*- coding: utf-8 -*-
"""shot15+ 参考图生成：4 张场景 + 3 张角色设计稿，全部锁定水彩概念动画风格。

风格铁律（Ron 2026-11-13 决策）：参考图绝对不要出现现实画风，避免画风漂移。
  - 正向风格段逐字沿用 shot12–14 场景脚本 / v07 角色设计稿批次
  - 负向词显式排除 photorealistic / photograph / photo / live action / 3d render / cgi
  - 生成后必须逐张目检；出现写实感、照片感、3D 渲染感或文字水印即判不合格，重出
  - 不使用 ImageGen（云端出图会消耗积分且与本地同批图不同源），走项目既有 ComfyUI Z-Image Turbo 链路

Run:
  python tools/gen_ref_shot15plus.py --list
  python tools/gen_ref_shot15plus.py --dry-run
  python tools/gen_ref_shot15plus.py --only E02 E11 E12 E13
  python tools/gen_ref_shot15plus.py
  python tools/gen_ref_shot15plus.py --only C18 --force
"""
import argparse
import json
import os
import time
import urllib.parse
import urllib.request
import uuid

COMFY = "http://127.0.0.1:8188"
ROOT = r"."
REF_ROOT = os.path.join(ROOT, "assets", "ref")
LEDGER = os.path.join(ROOT, "progress", "01_剧本分镜", "shot15+_参考图台账.json")

UNET = "z_image_turbo_bf16.safetensors"
CLIP = "qwen_3_4b.safetensors"
VAE = "ae.safetensors"
STEPS = 8
CFG = 1.0
SAMPLER = "res_multistep"
SCHEDULER = "simple"

# ---- 风格段：逐字沿用既有脚本，不改写、不简化 ----
STYLE_ENV = (
    "sophisticated watercolor concept art for an animated film, environment reference, "
    "delicate fine ink contour linework, loose transparent watercolor washes, "
    "granular cold-press paper texture, paint pooling and dry brush edges, hand painted, "
    "restrained muted palette of indigo blue black denim grey and warm cream, "
    "clear readable spatial structure, no people, no text, no watermark"
)
STYLE_CHAR = (
    "sophisticated watercolor concept art for an animated film, character design sheet, "
    "full body turnaround with front view side view and back view side by side, "
    "the same character repeated three times, "
    "standing straight with arms relaxed naturally at the sides, feet slightly apart, "
    "realistic human proportions seven and a half heads tall, natural small eyes, "
    "realistic facial anatomy with defined features, "
    "delicate fine ink contour linework, loose transparent watercolor washes, "
    "visible granular cold-press paper texture, paint pooling and dry brush edges, "
    "hand painted, fashion editorial illustration quality, "
    "restrained muted palette of indigo blue black denim grey and warm cream, "
    "clean untextured white paper background, soft even daylight, "
    "clean and tidy appearance, neatly groomed hair, clean neatly pressed clothes, spotless shoes, "
    "no dirt, no stains, small round watercolor palette swatches along the right edge, "
    "no text, no watermark"
)

# ---- 负向词：在既有 NEG 基础上强化「反写实」----
NEG_ENV = (
    "photorealistic, photograph, photo, live action, real scene photo, 3d render, cgi, digital render, "
    "hyperrealistic, realistic photographic texture, lens flare, depth of field bokeh, "
    "anime, manga, cartoon, cel shaded, text, watermark, logo, signature, people, "
    "blurry, muddy dark colors"
)
NEG_CHAR = (
    "photorealistic, photograph, photo, live action, real person, 3d render, cgi, digital render, "
    "hyperrealistic, realistic skin texture, lens flare, depth of field bokeh, "
    "anime, manga, cartoon, cel shaded, flat color blocks, big eyes, large sparkly eyes, cute, kawaii, chibi, "
    "doll face, baby face, childish proportions, storybook, digital airbrush, smooth plastic skin, "
    "heavy texture, muddy dark colors, text, watermark, logo, signature, extra characters, "
    "cropped feet, cropped head, blurry, deformed hands, mismatched duplicate, "
    "dirty clothes, stains, frame, border"
)

# (id, version, name, kind, w, h, seed, desc)
JOBS = [
    ("E02", "E02_v02", "医院病房·水彩重绘（去写实/去水印）", "env", 1344, 768, 2026111301,
     "interior of a modest Chinese hospital ward in the 2010s, "
     "lower walls painted pale sage green and upper walls white with a dark grey skirting line, "
     "a large three-panel window on the back wall with cream curtains and a cast-iron radiator below, "
     "a single metal hospital bed in the right foreground with white sheets, a folded pale blue-grey blanket, "
     "one white pillow and a simple metal bed rail, "
     "a wooden bedside cabinet with a thermos and an enamel mug beside the bed, "
     "a slim IV stand and a wall-mounted medical panel near the head of the bed, "
     "a tall wooden wardrobe against the left wall and a round wall clock, pale tiled floor, "
     "soft overcast daylight falling from the window, quiet sparse atmosphere, empty room, no people"),
    ("E11", "E11_v01", "阳台·择豆角", "env", 1344, 768, 2026111302,
     "a small enclosed balcony of a modest Chinese apartment, "
     "a metal security grille across the opening, a bamboo pole strung overhead, "
     "two low wooden stools placed side by side, "
     "a woven bamboo basket full of green long beans on the tiled floor, "
     "a few potted plants on the window ledge, a folded cloth and a small enamel basin, "
     "warm spring afternoon sunlight slanting in and casting soft long shadows, "
     "quiet unhurried domestic atmosphere, empty, no people"),
    ("E12", "E12_v01", "学校舞台·幕布", "env", 1344, 768, 2026111303,
     "a school auditorium stage seen from the wings, "
     "heavy deep indigo-red stage curtains drawn closed in soft vertical folds, "
     "warm overhead stage lights casting a gentle amber glow on the curtains, "
     "side curtains and a few stacked wooden chairs backstage, "
     "a narrow glimpse of blurred empty audience seats beyond the curtain edge, "
     "simple wooden stage floor, quiet anticipatory atmosphere before a performance, empty, no people"),
    ("E13", "E13_v01", "楼下晨景·早点摊刚收", "env", 1344, 768, 2026111304,
     "the foot of an old Chinese residential apartment building in the early morning, "
     "a folded-up street breakfast stall with a plain cloth cover, stacked small stools and a few plastic crates beside it, "
     "a large thermos and a covered pot on a low table, "
     "a low plaster wall with a patch of pale gold morning sunlight, "
     "a narrow paved path wide enough for a baby stroller, long soft shadows, "
     "quiet residential atmosphere, empty, no people"),
    # ---- v01 三张角色稿：2026-11-13 目检判不合格（动漫大眼/腮红/咧嘴卡通脸，与 v07 写实水彩成人脸不同族）----
    # 文件保留在 assets/ref/ 作过程素材，不进 H3 / Lux3D 素材池；定稿为下方 v02。
    ("C06b", "C06b_v01", "[弃用·卡通化] 许宁·中老年（居家）", "char", 1024, 1024, 2026111305,
     "Xu Ning, a Chinese woman in her late fifties, the same round gentle face, warm dark eyes and a small nose, "
     "short black hair with silver streaks tucked simply behind the ears, faint smile lines, a calm reserved expression, "
     "wearing a clean plain dove-grey knit cardigan over a light cotton blouse, "
     "loose dark indigo trousers and soft black cloth shoes"),
    ("C07b", "C07b_v01", "[弃用·卡通化] 许宁·老年（居家）", "char", 1024, 1024, 2026111306,
     "Xu Ning, an elderly Chinese woman aged seventy-five, the same round gentle face, warm dark eyes and a small nose, "
     "short neat silver hair, deep smile lines, a kind tired expression, "
     "wearing a clean soft oatmeal-beige knit cardigan over a pale blouse, "
     "loose dark grey trousers and soft white cloth slippers"),
    ("C18", "C18_v01", "[弃用·卡通化] 周远·老年", "char", 1024, 1024, 2026111307,
     "Zhou Yuan, an elderly Chinese man in his seventies, "
     "the same gentle scholarly face as his younger self with a defined jawline, "
     "narrow natural single-eyelid eyes and a subtle warm expression, "
     "neat short silver-grey hair, the same distinctive slim round black-framed glasses, "
     "slightly stooped gentle posture, "
     "wearing a clean soft beige knit sweater over a light blue collared shirt, "
     "straight dark grey trousers and plain white sneakers"),
    # ---- v02 定稿：正向描述锁成熟面部结构 / 中性闭口表情 / 自然小窄眼 ----
    # Z-Image Turbo 在 CFG 1.0 下负向词权重极低，卡通化只能靠正面描述压制，不能只加 negative。
    ("C06b", "C06b_v02", "许宁·中老年（居家）·独立建模稿·定稿", "char", 1024, 1024, 2026111315,
     "Xu Ning, a Chinese woman aged fifty-eight, realistic mature adult facial anatomy, "
     "defined jawline and cheekbones, narrow natural small eyes with a calm neutral gaze, a small nose, "
     "a closed mouth in a sober neutral expression, visible fine crow's feet and nasolabial folds, "
     "pale natural skin tone, mature neck and slender mature adult body proportions, "
     "short black hair with clear silver streaks combed back simply, "
     "wearing a clean plain dove-grey knit cardigan over a light cotton blouse, "
     "loose dark indigo trousers and soft black cloth shoes"),
    ("C07b", "C07b_v02", "许宁·老年（居家）·独立建模稿·定稿", "char", 1024, 1024, 2026111316,
     "Xu Ning, an elderly Chinese woman aged seventy-five, realistic elderly facial anatomy, "
     "defined bone structure with sunken cheeks and a defined jawline, narrow natural small eyes, a small nose, "
     "thin lips in a closed neutral mouth, deep nasolabial folds and crow's feet, "
     "pale natural skin tone, slender elderly body proportions, short neat silver hair, "
     "wearing a clean soft oatmeal-beige knit cardigan over a pale blouse, "
     "loose dark grey trousers and soft white cloth slippers"),
    ("C18", "C18_v02", "周远·老年·独立建模稿·定稿（沿用 C15 识别点）", "char", 1024, 1024, 2026111317,
     "Zhou Yuan, an elderly Chinese man aged seventy-two, realistic elderly male facial anatomy, "
     "defined jawline and cheekbones, narrow natural single-eyelid eyes behind slim round black-framed glasses, "
     "a small nose, thin lips in a closed neutral mouth, deep nasolabial folds and crow's feet, "
     "pale natural skin tone, slender elderly body proportions, neat short silver-grey hair, "
     "slightly stooped gentle posture, "
     "wearing a clean soft beige knit sweater over a light blue collared shirt, "
     "straight dark grey trousers and plain white sneakers"),
    # ---- v03：v02 脸部已合格，但 C06b / C18 中间视图被画成第二个正面（正/正/背），补严格 90° 侧视 ----
    ("C06b", "C06b_v03", "许宁·中老年（居家）·三视图版式修正", "char", 1024, 1024, 2026111321,
     "Xu Ning, a Chinese woman aged fifty-eight, realistic mature adult facial anatomy, "
     "defined jawline and cheekbones, narrow natural small eyes with a calm neutral gaze, a small nose, "
     "a closed mouth in a sober neutral expression, visible fine crow's feet and nasolabial folds, "
     "pale natural skin tone, mature neck and slender mature adult body proportions, "
     "short black hair with clear silver streaks combed back simply, "
     "wearing a clean plain dove-grey knit cardigan over a light cotton blouse, "
     "loose dark indigo trousers and soft black cloth shoes, "
     "three views arranged left to right: a full front view facing the camera on the left, "
     "a strict ninety degree side profile view in the middle showing only one eye and the nose silhouette, "
     "and a full back view on the right"),
    ("C18", "C18_v03", "周远·老年·三视图版式修正（沿用 C15 识别点）", "char", 1024, 1024, 2026111323,
     "Zhou Yuan, an elderly Chinese man aged seventy-two, realistic elderly male facial anatomy, "
     "defined jawline and cheekbones, narrow natural single-eyelid eyes behind slim round black-framed glasses, "
     "a small nose, thin lips in a closed neutral mouth, deep nasolabial folds and crow's feet, "
     "pale natural skin tone, slender elderly body proportions, neat short silver-grey hair, "
     "slightly stooped gentle posture, "
     "wearing a clean soft beige knit sweater over a light blue collared shirt, "
     "straight dark grey trousers and plain white sneakers, "
     "three views arranged left to right: a full front view facing the camera on the left, "
     "a strict ninety degree side profile view in the middle showing only one eye and the nose silhouette, "
     "and a full back view on the right"),
]


def post_json(path, payload):
    req = urllib.request.Request(COMFY + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def get_json(path):
    with urllib.request.urlopen(COMFY + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def build_graph(job):
    eid, ver, name, kind, w, h, seed, desc = job
    style = STYLE_ENV if kind == "env" else STYLE_CHAR
    neg = NEG_ENV if kind == "env" else NEG_CHAR
    text = f"{desc}, {style}"
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "lumina2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": STEPS, "cfg": CFG, "sampler_name": SAMPLER,
            "scheduler": SCHEDULER, "denoise": 1.0,
            "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": f"Lux3Dref/shot15plus_{ver}", "images": ["8", 0]}},
    }, text, neg


def load_ledger():
    if os.path.isfile(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            return json.load(f)
    return {
        "created": "2026-11-13",
        "purpose": "shot15+ 参考图生成台账（过程素材，可追溯）",
        "style_policy": {
            "rule": "参考图绝对不要出现现实画风（Ron 2026-11-13）",
            "engine": "local ComfyUI Z-Image Turbo（不调用云端 ImageGen）",
            "positive_style": "逐字沿用 shot12–14 场景脚本 / v07 角色设计稿批次",
            "negative_realism_lock": "photorealistic / photograph / photo / live action / 3d render / cgi 显式排除",
            "acceptance": "逐张目检：不得有写实感、照片感、3D 渲染感、文字或水印；布局与识别点对齐",
        },
        "jobs": [],
    }


def save_ledger(ledger):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)


def run_job(job, force=False):
    eid, ver, name, kind, w, h, seed, desc = job
    out_dir = os.path.join(REF_ROOT, eid)
    dest = os.path.join(out_dir, f"{ver}.png")
    if os.path.isfile(dest) and not force:
        print(f"[{ver}] SKIP 目标已存在 {dest}", flush=True)
        return None
    graph, text, neg = build_graph(job)
    t0 = time.time()
    resp = post_json("/prompt", {"prompt": graph, "client_id": str(uuid.uuid4())})
    pid = resp["prompt_id"]
    print(f"[{ver}] queued {pid} {name}", flush=True)
    deadline = time.time() + 600
    while time.time() < deadline:
        time.sleep(2)
        hist = get_json(f"/history/{pid}")
        if pid in hist:
            entry = hist[pid]
            st = entry.get("status", {})
            if st.get("status_str") == "error":
                raise RuntimeError(f"{ver} generation failed: {json.dumps(entry)[:800]}")
            if st.get("completed") or st.get("status_str") == "success":
                break
    else:
        raise TimeoutError(f"{ver} timeout waiting for {pid}")
    img = entry["outputs"]["9"]["images"][0]
    qs = urllib.parse.urlencode({"filename": img["filename"],
                                 "subfolder": img.get("subfolder", ""),
                                 "type": img.get("type", "output")})
    with urllib.request.urlopen(f"{COMFY}/view?{qs}", timeout=120) as r:
        data = r.read()
    os.makedirs(out_dir, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)
    elapsed = round(time.time() - t0, 1)
    print(f"[{ver}] saved {dest} ({len(data)} B, {elapsed}s)", flush=True)
    return {
        "id": eid, "version": ver, "name": name, "kind": kind,
        "seed": seed, "width": w, "height": h,
        "prompt": text, "negative": neg,
        "model": UNET, "clip": CLIP, "vae": VAE,
        "steps": STEPS, "cfg": CFG, "sampler": SAMPLER, "scheduler": SCHEDULER,
        "comfy_prompt_id": pid, "seconds": elapsed,
        "output": os.path.relpath(dest, ROOT).replace("\\", "/"),
        "visual_check": "pending",
        "verdict": "pending",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="只打印 prompt，不提交")
    ap.add_argument("--only", nargs="*", default=[], help="按 id 过滤，如 E02 C18")
    ap.add_argument("--force", action="store_true", help="目标文件已存在时也重出")
    args = ap.parse_args()

    jobs = JOBS
    if args.only:
        jobs = [j for j in jobs if j[0] in args.only]

    if args.list:
        for j in jobs:
            print(f"{j[0]:5s} {j[1]:10s} {j[3]:4s} {j[4]}x{j[5]} seed={j[6]}  {j[2]}")
        return

    if args.dry_run:
        for j in jobs:
            graph, text, neg = build_graph(j)
            print(f"\n=== {j[1]} ({j[4]}x{j[5]}, seed {j[6]}) ===")
            print("PROMPT:", text)
            print("NEGATIVE:", neg)
        return

    ledger = load_ledger()
    known = {(r["id"], r["version"]): r for r in ledger["jobs"]}
    for job in jobs:
        rec = run_job(job, args.force)
        if rec is None:
            continue
        key = (rec["id"], rec["version"])
        if key in known:
            ledger["jobs"][ledger["jobs"].index(known[key])] = rec
        else:
            ledger["jobs"].append(rec)
        save_ledger(ledger)
    print(f"LEDGER -> {LEDGER} ({len(ledger['jobs'])} 条)", flush=True)


if __name__ == "__main__":
    main()
