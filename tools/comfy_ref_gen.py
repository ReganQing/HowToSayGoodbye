# -*- coding: utf-8 -*-
"""Drive local ComfyUI (Z-Image Turbo) to render reference images for Lux3D image-to-3D.

Usage:
  python3 tools/comfy_ref_gen.py --list
  python3 tools/comfy_ref_gen.py --only P01 C01
  python3 tools/comfy_ref_gen.py --p0
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import uuid

COMFY = "http://127.0.0.1:8188"
ROOT = r"."
OUT_ROOT = os.path.join(ROOT, "assets", "ref")
MANIFEST = os.path.join(ROOT, "assets", "ref", "manifest.json")

UNET = "z_image_turbo_bf16.safetensors"
CLIP = "qwen_3_4b.safetensors"
VAE = "ae.safetensors"

STEPS = 8
CFG = 1.0
SAMPLER = "res_multistep"
SCHEDULER = "simple"
VERSION = "v01"

# ---- style presets ----
# realistic   : scene/environment assets (spatial precision, avoids distortion)
# handdrawn   : watercolor picture-book style for characters/props (lower modeling complexity, unified look)

REAL_CHAR = ("photorealistic full-body character reference photo, front view, standing in a strict T-pose, "
        "both arms extended straight out to the sides horizontally at shoulder level, arms fully separated from the torso, "
        "palms facing forward, legs straight feet slightly apart, entire body visible from head to shoes including fingertips, "
        "plain light gray seamless studio background, soft even diffused lighting, no shadows on the backdrop, "
        "clean and tidy appearance, neat well-groomed hair, healthy clean skin, "
        "clean freshly washed and neatly pressed clothes, smooth flat fabric, crisp collar and cuffs, "
        "spotless clean shoes, no dirt, no stains, no wrinkles, no worn or distressed fabric, "
        "muted nostalgic 1990s Chinese color palette, no text, no watermark")
REAL_PROP = ("photorealistic single-object reference photo, the object centered and fully visible, three-quarter front view, "
        "plain light gray seamless studio background, soft even diffused lighting, sharp focus, high detail, "
        "no people, no hands, no text, no watermark")
REAL_ENV = ("photorealistic environment reference photo, wide establishing shot, eye-level to slightly elevated angle, "
       "soft overcast daylight, no people, no text, no watermark, muted nostalgic 1990s Chinese color palette")
REAL_NEG = ("text, watermark, logo, signature, extra people, cropped, blurry, deformed hands, "
        "arms down, arms hanging at sides, arms close to body, arms bent, "
        "cartoon, anime, illustration, "
        "dirty clothes, stains, grime, mud, wrinkled fabric, worn out clothing, distressed fabric, messy hair, "
        "torn fabric, patches, frayed edges")

HD_CHAR = ("hand-painted watercolor illustration, children's picture-book art style, full-body character reference, "
        "front view, standing in a strict T-pose, both arms extended straight out to the sides horizontally "
        "at shoulder level, arms fully separated from the torso, palms facing forward, "
        "legs straight with feet slightly apart, entire body visible from head to shoes including fingertips, "
        "clean confident ink outlines, soft translucent watercolor washes, "
        "mostly flat clean color blocks, minimal shading, minimal texture, simple clean shapes, "
        "plain very light warm gray seamless background, soft even lighting, "
        "clean and tidy appearance, neatly groomed hair, clean tidy clothes, smooth fabric, clean shoes, "
        "no dirt, no stains, no worn fabric, muted warm nostalgic palette, no text, no watermark")
HD_PROP = ("hand-painted watercolor illustration, children's picture-book art style, single object reference, "
        "the object centered and fully visible, three-quarter front view, clean confident ink outlines, "
        "soft translucent watercolor washes, mostly flat clean color blocks, minimal shading, simple clean shapes, "
        "plain very light warm gray seamless background, soft even lighting, "
        "no people, no hands, no text, no watermark")
HD_ENV = ("hand-painted watercolor illustration, children's picture-book art style, environment reference, "
        "wide establishing shot, eye-level angle, clean confident architectural outlines, soft watercolor washes, "
        "flat clean color blocks, clear readable spatial structure and perspective, "
        "no people, no text, no watermark, muted warm nostalgic palette")
HD_NEG = ("photorealistic, photo, 3d render, anime, manga, cartoon, text, watermark, logo, signature, extra people, "
        "cropped, blurry, deformed hands, arms down, arms hanging at sides, arms close to body, arms bent, "
        "dirty clothes, stains, grime, mud, wrinkled fabric, worn out clothing, "
        "torn fabric, messy hair, busy patterned background, heavy paper texture, dark muddy colors")

# freedom: refined watercolor concept-art (refined watercolor concept-art animation style, delicate ink linework,
# loose transparent watercolor washes, granular cold-press paper texture, restrained indigo black denim-grey and
# cream palette). Source: <EXTERNAL_REF: 风格规范.md (2026-10-05 用户决策>).
FREEDOM_CHAR = ("sophisticated watercolor concept art for an animated film, character design sheet, "
        "full body turnaround with front view side view and back view side by side, the same character repeated three times, "
        "standing straight with arms relaxed naturally at the sides, feet slightly apart, "
        "realistic human proportions seven and a half heads tall, natural small eyes, realistic facial anatomy with defined features, "
        "delicate fine ink contour linework, loose transparent watercolor washes, visible granular cold-press paper texture, "
        "paint pooling and dry brush edges, hand painted, fashion editorial illustration quality, "
        "restrained muted palette of indigo blue black denim grey and warm cream, "
        "clean untextured white paper background, soft even daylight, "
        "clean and tidy appearance, neatly groomed hair, clean neatly pressed clothes, spotless shoes, "
        "no dirt, no stains, small round watercolor palette swatches along the right edge, no text, no watermark")
FREEDOM_NEG = ("anime, manga, cartoon, cel shaded, flat color blocks, big eyes, large sparkly eyes, cute, kawaii, chibi, "
        "doll face, baby face, childish proportions, storybook, 3d render, cgi, photorealistic, photo, "
        "digital airbrush, smooth plastic skin, heavy texture, muddy dark colors, "
        "text, watermark, logo, signature, extra characters, cropped feet, cropped head, blurry, "
        "deformed hands, mismatched duplicate, dirty clothes, stains, frame, border")

STYLES = {
    "realistic": {"char": REAL_CHAR, "prop": REAL_PROP, "env": REAL_ENV, "neg": REAL_NEG},
    "handdrawn": {"char": HD_CHAR, "prop": HD_PROP, "env": HD_ENV, "neg": HD_NEG},
    "freedom": {"char": FREEDOM_CHAR, "prop": HD_PROP, "env": HD_ENV, "neg": FREEDOM_NEG},
}
STYLE_NAME = "realistic"

JOBS = [
    {"id": "C01", "name": "许宁·幼童", "kind": "char", "w": 1024, "h": 1536, "seed": 2026110101,
     "prompt": "a Chinese girl aged five with a round gentle face, neat straight black short hair, warm dark eyes, "
               "wearing a clean neatly buttoned pale yellow cotton jacket with a crisp collar, "
               "clean dark trousers and spotless white canvas shoes"},
    {"id": "C08", "name": "姥姥", "kind": "char", "w": 1024, "h": 1536, "seed": 2026110102,
     "prompt": "an elderly Chinese grandmother in her seventies, kind gentle face, neat silver hair in a tidy low bun, "
               "narrow gentle eyes, wearing a clean indigo blue cotton apron neatly tied over a clean gray buttoned jacket, "
               "clean dark loose trousers and spotless black cloth shoes"},
    {"id": "C09", "name": "妈妈·青年", "kind": "char", "w": 1024, "h": 1536, "seed": 2026110103,
     "prompt": "a young Chinese mother in her twenties, oval gentle face, black hair in two neat tidy low braids, "
               "wearing a clean neatly pressed blue cotton jacket with a crisp collar, clean dark trousers and clean cloth shoes"},
    {"id": "C12", "name": "爸爸·青年", "kind": "char", "w": 1024, "h": 1536, "seed": 2026110104,
     "prompt": "a young Chinese father in his thirties, square honest face, neat short black hair, "
               "wearing a clean neatly pressed blue work uniform with tidy rolled sleeves and a crisp collar, "
               "clean dark work trousers and clean canvas shoes"},
    {"id": "P01", "name": "红发带·崭新", "kind": "prop", "w": 1024, "h": 1024, "seed": 2026110105,
     "prompt": "two brand-new long red silk hair ribbons laid out flat and slightly curled, "
               "each with a tiny white flower embroidered at the end"},
    {"id": "P14", "name": "自行车·二八大杠", "kind": "prop", "w": 1344, "h": 1024, "seed": 2026110106,
     "prompt": "a vintage Chinese 28-inch black steel roadster bicycle with a rear rack, curved handlebars, "
               "a metal bell and a sprung leather saddle, side view"},
    {"id": "E01", "name": "老厂区楼道口", "kind": "env", "w": 1344, "h": 768, "seed": 2026110107,
     "prompt": "the stairwell entrance of an old 1990s Chinese factory dormitory building, narrow concrete stairs, "
               "several open wooden doors, exposed brick and weathered cement walls, hanging fluorescent lamp, "
               "warm late afternoon light falling across the steps"},
    {"id": "E05", "name": "南方城市街道", "kind": "env", "w": 1344, "h": 768, "seed": 2026110719,
     "prompt": "a street in a southern Chinese city in the early 2000s, summer afternoon, small storefronts along a worn concrete sidewalk, "
               "a simple fast-food eatery with a glass display counter and a red signboard, tall leafy banyan trees overhanging the street, "
               "electric scooters parked by the curb, warm humid daylight"},
]

# Core-cast freedom-style design sheets (v05, 2026-11-07). 9 people / 12 items.
# Identity DNA locked from the Excel asset list; Xu Ning ages C01->C07 share one face description.
DESIGN_JOBS = [
    {"id": "C01", "name": "许宁·幼童（5-6岁）", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110701,
     "prompt": "Xu Ning, a Chinese girl with a round gentle face, straight black hair with neat bangs, warm dark eyes and a small nose, "
               "age five, short unbraided hair, wearing a clean neatly buttoned pale yellow cotton jacket with a crisp collar, "
               "clean dark trousers and spotless white canvas shoes"},
    {"id": "C02", "name": "许宁·小学（双辫＋红发带）", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110702,
     "prompt": "Xu Ning, a Chinese girl with a round gentle face, straight black hair, warm dark eyes and a small nose, "
               "age seven, two slightly uneven braids tied with red ribbons with tiny white flowers at the ends, "
               "a clean primary school uniform and a neat red scarf, spotless white shoes"},
    {"id": "C03", "name": "许宁·初中（校服）", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110703,
     "prompt": "Xu Ning, a Chinese girl with a round gentle face, straight black hair, warm dark eyes and a small nose, "
               "age fourteen, a single neat ponytail, a clean loose blue and white middle school tracksuit, spotless white sneakers"},
    {"id": "C04", "name": "许宁·高中（校服）", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110704,
     "prompt": "Xu Ning, a Chinese girl with a round gentle face, straight black hair, warm dark eyes and a small nose, "
               "age seventeen, a neat high ponytail, a clean high school uniform with rolled cuffs, a canvas schoolbag on one shoulder"},
    {"id": "C05", "name": "许宁·大学", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110705,
     "prompt": "Xu Ning, a Chinese girl with a round gentle face, straight black hair, warm dark eyes and a small nose, "
               "age twenty, shoulder-length black hair, a clean simple beige cardigan over a white shirt, neat jeans and canvas shoes"},
    {"id": "C06", "name": "许宁·成年（职场/婚礼/育儿）", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110706,
     "prompt": "Xu Ning, a Chinese woman with a round gentle face, straight black hair, warm dark eyes and a small nose, "
               "age twenty-eight, shoulder-length hair tied loosely back, a clean plain wool coat, dark trousers and flat shoes"},
    {"id": "C07", "name": "许宁·老年（病房）", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110707,
     "prompt": "Xu Ning, an elderly Chinese woman with a round gentle face, warm dark eyes and a small nose, "
               "age seventy-five, short silver hair, deep smile lines, a kind tired expression, "
               "a clean pale blue hospital gown, thin hands, soft white slippers"},
    {"id": "C08", "name": "姥姥", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110708,
     "prompt": "an elderly Chinese grandmother in her seventies, kind gentle face, neat silver hair in a tidy low bun, narrow gentle eyes, "
               "a clean indigo blue cotton apron neatly tied over a clean gray buttoned jacket, clean dark loose trousers, spotless black cloth shoes"},
    {"id": "C09", "name": "妈妈·青年", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110709,
     "prompt": "a young Chinese mother in her twenties, oval gentle face, black hair in two neat tidy low braids, "
               "a clean neatly pressed blue cotton jacket with a crisp collar, clean dark trousers, clean black cloth shoes"},
    {"id": "C10", "name": "妈妈·中年（馄饨店围裙）", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110710,
     "prompt": "a Chinese mother in her forties, oval gentle face, tired gentle eyes, black hair tied back with a few gray strands, "
               "a clean white apron over a clean dark red sweater with rolled sleeves, clean dark trousers, soft cloth shoes"},
    {"id": "C11", "name": "妈妈·老年", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110711,
     "prompt": "an elderly Chinese mother in her seventies, oval gentle face, short gray hair, thin metal reading glasses, "
               "a loose clean dark cardigan over a light blouse, clean soft cloth shoes"},
    {"id": "C12", "name": "爸爸·青年（工装）", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110712,
     "prompt": "a young Chinese father in his thirties, square honest face, neat short black hair, "
               "a clean neatly pressed blue work uniform with tidy rolled sleeves and a crisp collar, clean dark work trousers, clean canvas shoes"},
    {"id": "C13", "name": "周远·大学", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110713,
     "prompt": "a Chinese male university student, slim, thin-framed glasses, a gentle reserved expression, "
               "a clean plain light-colored shirt and clean dark trousers, simple white sneakers"},
    {"id": "C16", "name": "女儿·成年", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110716,
     "prompt": "a Chinese woman in her thirties, a gentle tired face, shoulder-length black hair, "
               "a clean simple cardigan over a light top, clean dark trousers, flat shoes"},
    {"id": "C17", "name": "小满（演出裙＋新红发带）", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110717,
     "prompt": "a Chinese girl around eight years old, bright eyes, a round lively face, black hair in two neat braids tied with new plain red ribbons without any decoration, "
               "a clean simple white performance dress with a full skirt, white shoes"},
    {"id": "C14", "name": "工友叔叔", "kind": "char", "w": 1024, "h": 1024, "seed": 2026110718,
     "prompt": "a Chinese man in his late fifties, weathered square kind face, short graying crew-cut hair, deep smile lines, "
               "slightly stooped shoulders, a clean light gray short-sleeve polo shirt, clean dark loose trousers, black cloth slippers"},
]


def build_graph(job):
    style = STYLES[STYLE_NAME]
    text = f"{job['prompt']}, {style[job['kind']]}"
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "lumina2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": style["neg"], "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage",
              "inputs": {"width": job["w"], "height": job["h"], "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "seed": job["seed"], "steps": STEPS, "cfg": CFG, "sampler_name": SAMPLER,
            "scheduler": SCHEDULER, "denoise": 1.0,
            "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": f"Lux3Dref/{job['id']}_{VERSION}", "images": ["8", 0]}},
    }


def post_json(path, payload):
    req = urllib.request.Request(COMFY + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def get_json(path):
    with urllib.request.urlopen(COMFY + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def run_job(job):
    graph = build_graph(job)
    client_id = str(uuid.uuid4())
    t0 = time.time()
    resp = post_json("/prompt", {"prompt": graph, "client_id": client_id})
    pid = resp["prompt_id"]
    print(f"[{job['id']}] queued {pid} {job['name']}", flush=True)
    while True:
        time.sleep(3)
        hist = get_json(f"/history/{pid}")
        if pid in hist:
            entry = hist[pid]
            status = entry.get("status", {})
            if status.get("completed") or status.get("status_str") == "success":
                break
            if status.get("status_str") == "error":
                raise RuntimeError(f"{job['id']} failed: {json.dumps(entry)[:800]}")
    outputs = entry["outputs"]
    images = outputs["9"]["images"]
    dest_dir = os.path.join(OUT_ROOT, job["id"])
    os.makedirs(dest_dir, exist_ok=True)
    saved = []
    for i, img in enumerate(images):
        qs = urllib.parse.urlencode({"filename": img["filename"],
                                     "subfolder": img.get("subfolder", ""),
                                     "type": img.get("type", "output")})
        with urllib.request.urlopen(f"{COMFY}/view?{qs}", timeout=120) as r:
            data = r.read()
        suffix = "" if i == 0 else f"_{i}"
        dest = os.path.join(dest_dir, f"{job['id']}_{VERSION}{suffix}.png")
        with open(dest, "wb") as f:
            f.write(data)
        saved.append(dest)
    elapsed = round(time.time() - t0, 1)
    print(f"[{job['id']}] done in {elapsed}s -> {saved}", flush=True)
    return {"id": job["id"], "version": VERSION, "name": job["name"], "kind": job["kind"], "style": STYLE_NAME,
            "seed": job["seed"],
            "width": job["w"], "height": job["h"], "steps": STEPS, "cfg": CFG,
            "sampler": SAMPLER, "scheduler": SCHEDULER, "model": UNET,
            "prompt": f"{job['prompt']}, {STYLES[STYLE_NAME][job['kind']]}", "negative": STYLES[STYLE_NAME]["neg"],
            "seconds": elapsed, "files": saved}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--p0", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--version", default="v01", help="output version tag, e.g. v02")
    ap.add_argument("--style", choices=["realistic", "handdrawn", "freedom"], default="realistic",
                    help="realistic = photoreal (scenes), handdrawn = watercolor picture-book (characters/props), freedom = refined watercolor concept-art sheets")
    ap.add_argument("--design", action="store_true", help="use DESIGN_JOBS (core-cast freedom sheets) instead of JOBS")
    args = ap.parse_args()
    global VERSION, STYLE_NAME
    VERSION = args.version
    STYLE_NAME = args.style
    if args.list:
        for j in (DESIGN_JOBS if args.design else JOBS):
            print(j["id"], j["name"], j["kind"], f"{j['w']}x{j['h']}")
        return
    jobs = DESIGN_JOBS if args.design else JOBS
    if args.only:
        jobs = [j for j in jobs if j["id"] in args.only]
    records = []
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            records = json.load(f)
    done = {(r["id"], r.get("version", "v01")) for r in records}
    for job in jobs:
        if (job["id"], VERSION) in done:
            print(f"[{job['id']}] skip ({VERSION} already in manifest)", flush=True)
            continue
        rec = run_job(job)
        records.append(rec)
        os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
