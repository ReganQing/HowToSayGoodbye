# -*- coding: utf-8 -*-
"""shot15+ 建模输入：8 个独立角色的严格 T-pose 单视图。

【资产分层 · 重要】
  本脚本产物是**写实照片风**，但它只进 Lux3D image-to-3D + auto-rig，
  绝不进 H3 ref_images，不决定成片画风。
  原因（tools/gen_c15_tpose.py 踩坑记录）：水彩风画不出严格 T-pose，
  Lux3D 会报 RIG_ELIGIBILITY_FAILED。解法 = 写实风格 + T-pose 要求放提示词句首 + 20 步采样。
  输出独立放 assets/ref_tpose/，与 assets/ref/ 的水彩参考图物理隔离，避免误用。
  Ron 2026-11-13「参考图绝对不要出现现实画风」约束的是进 H3 的场景图与面容图。

Run:
  py -3.12 tools/gen_tpose_shot15plus.py --list
  py -3.12 tools/gen_tpose_shot15plus.py --dry-run
  py -3.12 tools/gen_tpose_shot15plus.py --only C06 C06b
  py -3.12 tools/gen_tpose_shot15plus.py
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
OUT_ROOT = os.path.join(ROOT, "assets", "ref_tpose")
LEDGER = os.path.join(ROOT, "progress", "01_剧本分镜", "shot15+_参考图台账.json")

UNET = "z_image_turbo_bf16.safetensors"
CLIP = "qwen_3_4b.safetensors"
VAE = "ae.safetensors"
STEPS = 20  # T-pose 必须 20 步，8 步画不出严格水平手臂（C14 踩坑）
CFG = 1.0
SAMPLER = "res_multistep"
SCHEDULER = "simple"

# 沿用 gen_c15_tpose.py 的句首 T-pose 骨架与负向词，逐字不改
POSE_HEAD = (
    "strict T-pose full-body character reference photo, "
    "both arms extended straight out to the sides perfectly horizontally at exact shoulder level, "
    "arms forming one straight horizontal line across the shoulders, "
    "arms fully separated from the torso, palms facing forward, "
)
POSE_TAIL = (
    "front view, standing straight facing the camera, legs straight feet slightly apart, "
    "entire body visible from head to shoes including all fingertips, "
    "photorealistic, plain light gray seamless studio background, "
    "soft even diffused lighting, no shadows on the backdrop, "
    "natural skin texture, no text, no watermark"
)
NEG = (
    "arms down, arms hanging, arms at sides, arms lowered, arms diagonal, arms angled down, "
    "arms bent, elbows bent, "
    "text, watermark, logo, signature, extra people, cropped, blurry, deformed hands, "
    "cartoon, anime, illustration, watercolor, sketch, "
    "dirty clothes, stains, wrinkled fabric, worn out clothing, messy hair"
)

# (cid, version, 角色描述, seed)
JOBS = [
    ("C06", "C06_tpose_v01", 2026111341,
     "a Chinese woman aged twenty-eight, round gentle face, natural small narrow eyes, "
     "shoulder-length black hair tied loosely back at the nape, "
     "a clean cream short coat with a turned-down collar and two rows of buttons over a light top, "
     "loose dark indigo trousers and black flat shoes"),
    ("C06b", "C06b_tpose_v01", 2026111342,
     "a Chinese woman aged fifty-eight, mature face with fine crow's feet and nasolabial folds, "
     "natural small narrow eyes, short black hair with clear silver streaks combed back simply, "
     "a clean plain dove-grey knit cardigan over a light cotton blouse, "
     "loose dark indigo trousers and soft black cloth shoes"),
    ("C07", "C07_tpose_v01", 2026111343,
     "an elderly Chinese woman aged seventy-five, short neat silver hair, "
     "deep nasolabial folds and crow's feet, natural small narrow eyes, "
     "a clean pale blue hospital gown, loose dark trousers and soft white slippers"),
    ("C07b", "C07b_tpose_v01", 2026111344,
     "an elderly Chinese woman aged seventy-five, short neat silver hair, "
     "deep nasolabial folds and crow's feet, natural small narrow eyes, "
     "a clean soft oatmeal-beige knit cardigan over a pale blouse, "
     "loose dark grey trousers and soft white cloth slippers"),
    ("C11", "C11_tpose_v01", 2026111345,
     "an elderly Chinese mother in her seventies, short grey hair, thin metal reading glasses, "
     "an oval gentle face with natural small narrow eyes, "
     "a loose clean dark navy cardigan over a light blouse, "
     "dark loose trousers and soft dark cloth shoes"),
    ("C16", "C16_tpose_v01", 2026111346,
     "a Chinese woman in her thirties, gentle tired face, shoulder-length straight black hair, "
     "natural small narrow eyes, "
     "a clean simple beige cardigan over a light top, dark trousers and flat shoes"),
    # C11 v01 双手被画面左右边缘裁掉，auto-rig 报 RIG_ELIGIBILITY_FAILED（task 7153055）。
    # v02 改横版 1536x1024 留足手臂余量，并在句首补「完整手部不裁切」约束。
    ("C11", "C11_tpose_v02", 2026111351,
     "an elderly Chinese mother in her seventies, short grey hair, thin metal reading glasses, "
     "an oval gentle face with natural small narrow eyes, standing straight and upright, "
     "a loose clean dark navy cardigan over a light blouse, "
     "dark loose trousers and soft dark cloth shoes"),
    ("C17", "C17_tpose_v01", 2026111347,
     "a Chinese girl around eight years old, bright round lively face, "
     "black hair in two neat braids tied with plain red ribbons, "
     "a clean simple white short-sleeve performance dress with a full skirt, white socks and white shoes, "
     "realistic child body proportions"),
    ("C18", "C18_tpose_v01", 2026111348,
     "an elderly Chinese man aged seventy-two, short silver-grey hair, "
     "slim round black-framed glasses, a gentle scholarly face with deep nasolabial folds, "
     "natural small narrow single-eyelid eyes, standing straight, "
     "a clean soft beige knit sweater over a light blue collared shirt, "
     "straight dark grey trousers and plain white sneakers"),
]


def post_json(path, payload):
    req = urllib.request.Request(COMFY + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def get_json(path):
    with urllib.request.urlopen(COMFY + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def build_graph(job, w=1024, h=1536):
    cid, ver, seed, desc = job
    text = f"{POSE_HEAD}{desc}, {POSE_TAIL}"
    if ver == "C11_tpose_v02":
        # 横版画幅给水平展开的双臂留余量，避免指尖被裁导致绑骨资格校验失败
        w, h = 1536, 1024
        text = text.replace(
            "front view,",
            "front view, small full figure centered with wide empty space on both sides, "
            "both hands and every fingertip completely inside the frame, "
            "no cropping at the left or right edges,")
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "lumina2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": STEPS, "cfg": CFG, "sampler_name": SAMPLER,
            "scheduler": SCHEDULER, "denoise": 1.0,
            "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": f"Lux3Dref/{ver}", "images": ["8", 0]}},
    }, text


def load_ledger():
    if os.path.isfile(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            return json.load(f)
    return {"jobs": []}


def run_job(job, force=False):
    cid, ver, seed, desc = job
    dest = os.path.join(OUT_ROOT, f"{ver}.png")
    if os.path.isfile(dest) and not force:
        print(f"[{ver}] SKIP 已存在", flush=True)
        return None
    graph, text = build_graph(job)
    t0 = time.time()
    pid = post_json("/prompt", {"prompt": graph, "client_id": str(uuid.uuid4())})["prompt_id"]
    print(f"[{ver}] queued {pid}", flush=True)
    deadline = time.time() + 1800   # 可能排在 H3 长任务后面，留足排队时间
    while time.time() < deadline:
        time.sleep(2)
        hist = get_json(f"/history/{pid}")
        if pid in hist:
            entry = hist[pid]
            st = entry.get("status", {})
            if st.get("status_str") == "error":
                raise RuntimeError(f"{ver} failed: {json.dumps(entry)[:800]}")
            if st.get("completed") or st.get("status_str") == "success":
                break
    else:
        raise TimeoutError(f"{ver} timeout {pid}")
    img = entry["outputs"]["9"]["images"][0]
    qs = urllib.parse.urlencode({"filename": img["filename"],
                                 "subfolder": img.get("subfolder", ""),
                                 "type": img.get("type", "output")})
    with urllib.request.urlopen(f"{COMFY}/view?{qs}", timeout=120) as r:
        data = r.read()
    os.makedirs(OUT_ROOT, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)
    elapsed = round(time.time() - t0, 1)
    print(f"[{ver}] saved {dest} ({len(data)} B, {elapsed}s)", flush=True)
    return {
        "cid": cid, "version": ver, "seed": seed,
        "size": [graph["6"]["inputs"]["width"], graph["6"]["inputs"]["height"]],
        "prompt": text, "negative": NEG,
        "model": UNET, "steps": STEPS, "cfg": CFG, "sampler": SAMPLER, "scheduler": SCHEDULER,
        "comfy_prompt_id": pid, "seconds": elapsed,
        "output": f"assets/ref_tpose/{ver}.png",
        "usage": "Lux3D image-to-3D + auto-rig ONLY；不进 H3 ref_images",
        "visual_check": "pending", "verdict": "pending",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    jobs = JOBS
    if args.only:
        jobs = [j for j in jobs if j[0] in args.only]
    if args.list:
        for j in jobs:
            print(f"{j[0]:5s} {j[1]:18s} seed={j[2]}")
        return
    if args.dry_run:
        for j in jobs:
            _, text = build_graph(j)
            print(f"\n=== {j[1]} ===\n{text}\nNEG: {NEG}")
        return

    ledger = load_ledger()
    tpose = ledger.setdefault("tpose_jobs", {
        "created": "2026-11-13",
        "policy": "写实 T-pose 仅作 Lux3D 建模中间素材，不进 H3 ref_images；水彩画不出严格 T-pose 会 RIG_ELIGIBILITY_FAILED",
        "items": [],
    })
    known = {(r["cid"], r["version"]): r for r in tpose["items"]}
    for job in jobs:
        rec = run_job(job, args.force)
        if rec is None:
            continue
        key = (rec["cid"], rec["version"])
        if key in known:
            tpose["items"][tpose["items"].index(known[key])] = rec
        else:
            tpose["items"].append(rec)
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "w", encoding="utf-8") as f:
            json.dump(ledger, f, ensure_ascii=False, indent=2)
    print(f"LEDGER -> {LEDGER} (tpose_jobs {len(tpose['items'])} 条)", flush=True)


if __name__ == "__main__":
    main()
