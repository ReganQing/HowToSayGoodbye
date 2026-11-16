# -*- coding: utf-8 -*-
"""shot18 婴儿水彩头肩参考图（C20 半岁女儿）。

为什么需要：方案 §5 把 C20 标为「襁褓道具，无需绑骨」，不需要 Lux3D 模型；
但 H3 要画出可辨识的婴儿脸，光靠 prompt 容易崩或画成卡通大眼。给一张
水彩概念动画风的头肩图当第三张 ref_image，把脸锁住。

风格铁律（Ron 2026-11-13 决策 4 + HANDOFF §5.11/§5.12）：
  - 进 H3 的参考图必须水彩概念动画风，绝不写实、绝不照片感
  - 也要避免 Z-Image Turbo 把婴儿画成动漫大眼/腮红/咧嘴笑，正向写足自然五官
  - 负向词显式排除 photorealistic / photograph / 3d render / anime / cartoon / big eyes
  - 生成后必须目检；不合格换 seed 重出，弃用稿保留归档

⚠️ 本脚本会占用 ComfyUI 队列与 GPU，必须在 shot17 H3 生成完成后再跑。

变体轨迹（全部留档，不覆盖）：
  v1 = 写实照片感判退（seed 2026111420）
  v2 = 平涂卡通化判退（seed 2026111421）
  v3 = 向定稿族回归的中间态（seed 2026111422），当前默认

Run:
  py -3.12 tools/gen_ref_shot18.py --dry-run
  py -3.12 tools/gen_ref_shot18.py
  py -3.12 tools/gen_ref_shot18.py --variant v1 --seed 2026111420 --ver C20_v01
"""
import argparse
import json
import os
import time
import urllib.parse
import urllib.request
import uuid

COMFY = "http://127.0.0.1:8188"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_ROOT = os.path.join(ROOT, "assets", "ref", "C20")
LEDGER = os.path.join(ROOT, "progress", "01_剧本分镜", "shot15+_参考图台账.json")

UNET = "z_image_turbo_bf16.safetensors"
CLIP = "qwen_3_4b.safetensors"
VAE = "ae.safetensors"
STEPS, CFG, SAMPLER, SCHEDULER = 8, 1.0, "res_multistep", "simple"

# 风格段沿用 gen_ref_shot15plus.py 的角色稿画风，改为头肩肖像版式
STYLE_FACE = (
    "sophisticated watercolor concept art for an animated film, character portrait reference, "
    "a single head and shoulders portrait facing the camera, "
    "delicate fine ink contour linework, loose transparent watercolor washes, "
    "visible granular cold-press paper texture, paint pooling and dry brush edges, hand painted, "
    "restrained muted palette of indigo blue black denim grey and warm cream, "
    "clean untextured white paper background, soft even daylight, "
    "natural small eyes with a calm neutral gaze, realistic natural facial proportions, "
    "closed mouth in a sober neutral expression, no smile, "
    "no text, no watermark"
)

NEG_FACE = (
    "photorealistic, photograph, photo, live action, real person, 3d render, cgi, digital render, "
    "hyperrealistic, realistic photographic skin texture, lens flare, depth of field bokeh, "
    "anime, manga, cartoon, cel shaded, flat color blocks, big eyes, large sparkly eyes, cute, kawaii, chibi, "
    "doll face, exaggerated baby proportions, storybook, digital airbrush, smooth plastic skin, "
    "rosy blush cheeks, laughing, open mouth, pacifier, hat, bonnet, "
    "heavy texture, muddy dark colors, text, watermark, logo, signature, extra characters, "
    "cropped head, blurry, deformed hands, frame, border"
)

DESC = (
    "a Chinese baby girl about six months old, head and shoulders portrait, "
    "lying on her back and looking up calmly toward the viewer, "
    "soft round infant face with realistic natural infant proportions, "
    "small natural eyes with a quiet open gaze, a tiny nose, small closed lips, "
    "smooth pale natural skin, sparse fine dark hair, "
    "wrapped snugly in a plain pale cream swaddle with only the head and shoulders visible, "
    "quiet gentle morning mood, no toys, no props"
)


# ---------------- v2 修正版（v01 判退后）----------------
# v01 虽有水彩媒介，但脸是照片转水彩：皮肤连续渐变、立体光影、瞳孔高光、粉红腮红、
# 眼睛偏大偏亮，与项目的水彩概念动画设计稿不同族。CFG 1.0 下负向词几乎不起作用，
# 所以把「扁平化 / 概括笔画 / 无摄影式明暗」全部写进正向。
V2_DESC = (
    "a Chinese baby girl about six months old, head and shoulders portrait, "
    "drawn in a simplified flat stylized way for an animated film, "
    "a round calm infant face built from a few clean graphic shapes, "
    "small almond shaped eyes drawn with a few ink strokes and one flat dark pupil each, "
    "eyes of natural small size with no shine and no catchlight, "
    "a tiny simple nose, a small closed line mouth with no smile, "
    "flat pale cream skin tone with no shading, no blush and no gloss, "
    "sparse fine dark hair suggested by a few loose ink strokes, "
    "wrapped snugly in a plain pale cream swaddle with only the head and shoulders visible, "
    "quiet gentle morning mood, no toys, no props"
)
V2_STYLE = (
    "sophisticated watercolor concept art for an animated film, character portrait reference, "
    "a single head and shoulders portrait facing the camera, "
    "delicate fine ink contour linework of even weight, flat matte watercolor washes, "
    "minimal tonal modelling, graphic simplified shapes rather than photographic detail, "
    "visible granular cold-press paper texture, paint pooling and dry brush edges, hand painted, "
    "restrained muted palette of indigo blue black denim grey and warm cream, "
    "clean untextured white paper background, soft even flat daylight with no cast shadows on the face, "
    "no text, no watermark"
)
V2_NEG = NEG_FACE + (
    ", photographic shading, realistic skin gradient, glossy lips, specular highlight, catchlight, "
    "rosy cheeks, 3d shading, airbrush, photographic realism, soft focus portrait, studio lighting, "
    "rendered skin, subsurface scattering, hyper detailed pores"
)

# ---------------- v3 中间态（v01 太写实、v02 太卡通后的定稿族回归）----------------
# 根因复盘（见 progress/06_质检返修/shot18_C20_v02_卡通化_弃用/v02_verdict.json）：
#   Z-Image Turbo + CFG 1.0 下负向词几乎不起作用，约束必须全部写进正向。
#   v1 输在主体描述：realistic / smooth pale natural skin 把婴儿拉成照片转水彩；
#   v2 输在主体描述：simplified flat stylized / graphic shapes 把婴儿拉成矢量萌娃。
#   v3 保留 v1 的媒介质感（与定稿 assets/ref_face/C06_v07_head.png 同族：细淡墨线、
#   极淡透明水彩、冷压纸纹、收敛五官），但主体只写「用极少的淡墨笔画概括出来的头形」，
#   彻底不出现 realistic / smooth / skin / cute 这类会把题材推向照片或萌娃的词。
V3_DESC = (
    "an understated line and wash portrait study of a Chinese baby girl about six months old, "
    "head and shoulders, facing the camera, drawn with economical restrained pen strokes, "
    "a gently rounded infant head shape suggested by a few fine broken ink contours, "
    "two short fine ink strokes for small naturally placed almond eyes with tiny dark pupils, "
    "no white catchlight in the eyes, a tiny suggested nose, a short closed line mouth with no smile, "
    "sparse fine hair indicated by a handful of light ink strokes, "
    "quiet sober calm expression, "
    "wrapped in a plain pale cream swaddle with only the head and shoulders visible"
)
V3_STYLE = (
    "sophisticated watercolor concept art for an animated film, character portrait reference, "
    "a sober observational sketch rather than a cute baby illustration, "
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
V3_NEG = NEG_FACE + (
    ", thick outline, bold dark contour, big round eyes, white catchlight, rosy cheeks, "
    "flat vector, sticker art, simplified flat stylized, graphic simplified shapes, "
    "photographic shading, realistic skin gradient, glossy lips, specular highlight, "
    "3d shading, airbrush, photographic realism, soft focus portrait, studio lighting, "
    "rendered skin, subsurface scattering, hyper detailed pores"
)

VARIANTS = {
    "v1": (DESC, STYLE_FACE, NEG_FACE),
    "v2": (V2_DESC, V2_STYLE, V2_NEG),
    "v3": (V3_DESC, V3_STYLE, V3_NEG),
}


def post_json(path, payload):
    req = urllib.request.Request(COMFY + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def get_json(path):
    with urllib.request.urlopen(COMFY + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def build_graph(seed, ver, variant="v3"):
    desc, style, neg = VARIANTS[variant]
    text = f"{desc}, {style}"
    graph = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "lumina2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": STEPS, "cfg": CFG, "sampler_name": SAMPLER,
            "scheduler": SCHEDULER, "denoise": 1.0,
            "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": f"Lux3Dref/shot18_{ver}", "images": ["8", 0]}},
    }
    return graph, text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed", type=int, default=2026111422)
    ap.add_argument("--ver", default="C20_v03")
    ap.add_argument("--variant", choices=sorted(VARIANTS), default="v3",
                    help="v1 写实感判退稿、v2 平涂卡通判退稿（均留档），v3 定稿族中间态")
    a = ap.parse_args()

    graph, text = build_graph(a.seed, a.ver, a.variant)
    if a.dry_run:
        print("PROMPT:", text)
        print("NEGATIVE:", VARIANTS[a.variant][2])
        return

    # 队列必须空闲，避免与 H3 生成争显存 / 重复排队
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
        "id": "C20", "version": a.ver, "name": "婴儿·半岁·水彩头肩图（shot18 第三张 ref_image）",
        "kind": "face", "seed": a.seed, "width": 1024, "height": 1024,
        "prompt": text, "negative": VARIANTS[a.variant][2], "variant": a.variant,
        "model": UNET, "clip": CLIP, "vae": VAE,
        "steps": STEPS, "cfg": CFG, "sampler": SAMPLER, "scheduler": SCHEDULER,
        "comfy_prompt_id": pid, "seconds": elapsed,
        "output": os.path.relpath(dest, ROOT).replace("\\", "/"),
        "visual_check": "pending", "verdict": "pending",
        "note": "必须目检：不得写实/照片感/3D 渲染感，也不得动漫大眼/腮红/咧嘴笑；合格后裁成 SHOT18_C20_face.png 拷入 ComfyUI input",
    }
    with open(LEDGER, encoding="utf-8") as f:
        led = json.load(f)
    jobs = led.setdefault("jobs", [])
    jobs[:] = [j for j in jobs if not (j.get("id") == "C20" and j.get("version") == a.ver)]
    jobs.append(rec)
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(led, f, ensure_ascii=False, indent=2)
    print("LEDGER ->", os.path.relpath(LEDGER, ROOT))
    print("GEN_REF_SHOT18_DONE")


if __name__ == "__main__":
    main()
