# -*- coding: utf-8 -*-
"""重绘 C18 周远·老年 的水彩头肩面容图（shot19 / shot23 第三张 ref_image）。

为什么需要：assets/ref/C18/C18_v03.png 三视图的服装/体型/版式正确，但脸被
Z-Image Turbo 画成卡通爷爷（大圆眼、粗黑圆框镜、简笔笑纹、上扬微笑），
裁出的 assets/ref_face/C18_v03_head.png 与定稿族 C06_v07_head / C06b_v03_head
不同族。详见 progress/06_质检返修/shot19_C18面容图_画风漂移登记/risk_note.json。

做法：沿用 tools/gen_ref_shot18.py v3 已验证的媒介质感写法（该变体一次把婴儿
从「照片写实」和「平涂卡通」两端拉回定稿族），主体换成老年男性；CFG 1.0 下
负向词近乎无效，所以全部约束写进正向，不依赖 negative。

Lux3D 模型只进哑光白模、不进 H3 ref_images，因此 C18 模型不重建。

⚠️ 本脚本占用 ComfyUI 队列与 GPU，必须等 shot18 H3 生成完成、队列空闲后再跑。

Run:
  py -3.12 tools/gen_ref_c18_head.py --dry-run
  py -3.12 tools/gen_ref_c18_head.py
  py -3.12 tools/gen_ref_c18_head.py --seed 2026111424 --ver C18_head_v02
"""
import argparse
import io
import json
import os
import time
import urllib.parse
import urllib.request
import uuid

COMFY = "http://127.0.0.1:8188"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_ROOT = os.path.join(ROOT, "assets", "ref", "C18")
LEDGER = os.path.join(ROOT, "progress", "01_剧本分镜", "shot15+_参考图台账.json")

UNET = "z_image_turbo_bf16.safetensors"
CLIP = "qwen_3_4b.safetensors"
VAE = "ae.safetensors"
STEPS, CFG, SAMPLER, SCHEDULER = 8, 1.0, "res_multistep", "simple"

DESC = (
    "an understated line and wash portrait study of a Chinese man aged seventy-two, "
    "head and shoulders, facing the camera, drawn with economical restrained pen strokes, "
    "a lean elderly face with a defined jawline suggested by a few fine broken ink contours, "
    "two short fine ink strokes for narrow natural single-eyelid eyes with tiny dark pupils, "
    "no white catchlight in the eyes, a pair of very fine thin round spectacle rims drawn "
    "with light ink strokes rather than bold heavy black frames, "
    "a small suggested nose, a short closed line mouth with no smile, "
    "fine short ink strokes for nasolabial folds and crow's feet, "
    "short neat silver-grey hair indicated by a handful of light strokes, "
    "a quiet sober neutral expression, "
    "wearing a plain soft beige knit sweater over a light blue collared shirt"
)

# 媒介质感逐字沿用 gen_ref_shot18.py 的 V3_STYLE，只换「不是什么」的那一句
STYLE = (
    "sophisticated watercolor concept art for an animated film, character portrait reference, "
    "a sober observational sketch rather than a cute cartoon grandfather illustration, "
    "very fine delicate thin ink contour linework with uneven hand drawn weight, "
    "line dominant drawing with most of the white paper left unpainted, "
    "pale transparent watercolor washes with no tonal modelling on the face, "
    "visible granular cold-press paper texture, paint pooling and dry brush edges, hand painted, "
    "fashion editorial illustration quality, "
    "restrained muted palette of indigo blue black denim grey and warm cream, "
    "no rosy cheeks, no pink on the face, matte finish, no gloss, "
    "clean untextured white paper background, soft even daylight with no cast shadows on the face, "
    "no text, no watermark"
)

NEG = (
    "photorealistic, photograph, photo, live action, real person, 3d render, cgi, digital render, "
    "hyperrealistic, realistic photographic skin texture, lens flare, depth of field bokeh, "
    "anime, manga, cartoon, cel shaded, flat color blocks, big eyes, large sparkly eyes, "
    "cute, kawaii, chibi, doll face, storybook, digital airbrush, smooth plastic skin, "
    "rosy blush cheeks, laughing, smiling, open mouth, "
    "thick outline, bold dark contour, heavy black spectacles, big round eyes, white catchlight, "
    "flat vector, sticker art, simplified flat stylized, graphic simplified shapes, "
    "photographic shading, realistic skin gradient, glossy lips, specular highlight, "
    "3d shading, airbrush, photographic realism, soft focus portrait, studio lighting, "
    "rendered skin, subsurface scattering, hyper detailed pores, "
    "heavy texture, muddy dark colors, text, watermark, logo, signature, extra characters, "
    "cropped head, blurry, deformed hands, frame, border"
)


def get_json(path):
    with urllib.request.urlopen(COMFY + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def post_json(path, payload):
    req = urllib.request.Request(COMFY + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def build_graph(seed, ver):
    text = f"{DESC}, {STYLE}"
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "lumina2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": STEPS, "cfg": CFG, "sampler_name": SAMPLER,
            "scheduler": SCHEDULER, "denoise": 1.0,
            "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": f"Lux3Dref/{ver}", "images": ["8", 0]}},
    }, text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed", type=int, default=2026111423)
    ap.add_argument("--ver", default="C18_head_v01")
    a = ap.parse_args()

    graph, text = build_graph(a.seed, a.ver)
    if a.dry_run:
        print("PROMPT:", text)
        print("NEGATIVE:", NEG)
        return

    q = get_json("/queue")
    assert not q.get("queue_running") and not q.get("queue_pending"), \
        "ComfyUI 队列非空，等正在跑的 H3 生成结束后再跑本脚本"

    dest = os.path.join(REF_ROOT, f"{a.ver}.png")
    os.makedirs(REF_ROOT, exist_ok=True)
    t0 = time.time()
    resp = post_json("/prompt", {"prompt": graph, "client_id": str(uuid.uuid4())})
    pid = resp["prompt_id"]
    print(f"[{a.ver}] queued {pid} seed={a.seed}", flush=True)

    entry = None
    deadline = time.time() + 1800
    while time.time() < deadline:
        time.sleep(2)
        hist = get_json(f"/history/{pid}")
        if pid in hist:
            entry = hist[pid]
            st = entry.get("status", {})
            if st.get("status_str") == "error":
                raise RuntimeError(f"{a.ver} 生成失败: {json.dumps(entry)[:800]}")
            if st.get("completed") or st.get("status_str") == "success":
                break
    else:
        raise TimeoutError(f"{a.ver} 等待超时 {pid}；不要重提，用 /history/{pid} 复查")

    img = entry["outputs"]["9"]["images"][0]
    qs = urllib.parse.urlencode({"filename": img["filename"],
                                 "subfolder": img.get("subfolder", ""),
                                 "type": img.get("type", "output")})
    with urllib.request.urlopen(f"{COMFY}/view?{qs}", timeout=120) as r:
        data = r.read()
    with open(dest, "wb") as f:
        f.write(data)
    elapsed = round(time.time() - t0, 1)
    print(f"[{a.ver}] saved {dest} ({len(data)} B, {elapsed}s)", flush=True)

    rec = {
        "id": "C18_head", "version": a.ver,
        "name": "周远·老年 水彩头肩图（shot19 / shot23 第三张 ref_image）",
        "kind": "face_repaint", "seed": a.seed, "width": 1024, "height": 1024,
        "prompt": text, "negative": NEG,
        "model": UNET, "clip": CLIP, "vae": VAE,
        "steps": STEPS, "cfg": CFG, "sampler": SAMPLER, "scheduler": SCHEDULER,
        "comfy_prompt_id": pid, "seconds": elapsed,
        "output": os.path.relpath(dest, ROOT).replace("\\", "/"),
        "visual_check": "pending", "verdict": "pending",
        "basis": "progress/06_质检返修/shot19_C18面容图_画风漂移登记/risk_note.json",
        "note": "必须目检：细淡墨线 + 极淡透明水彩 + 纸纹 + 收敛小眼 + 细圆框镜 + 闭口无笑 + 无腮红；合格后裁成 SHOT19_C18_face.png 拷入 ComfyUI input",
    }
    led = json.load(io.open(LEDGER, encoding="utf-8"))
    jobs = led.setdefault("jobs", [])
    jobs[:] = [j for j in jobs if not (j.get("id") == "C18_head" and j.get("version") == a.ver)]
    jobs.append(rec)
    with io.open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(led, f, ensure_ascii=False, indent=2)
    print("LEDGER ->", os.path.relpath(LEDGER, ROOT))
    print("GEN_REF_C18_HEAD_DONE")


if __name__ == "__main__":
    main()
