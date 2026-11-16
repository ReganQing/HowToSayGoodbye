# -*- coding: utf-8 -*-
"""P02 老照片（道具图，非 Lux3D 资产）：爸爸和工友们围矮桌吃饭的照片内容。
剧本 L235：几个人围着矮桌吃饭，爸爸坐在边上，笑得眼睛眯起来；L241：碗边一双筷子、
桌上半瓶凝水珠的汽水。风格贴影片水彩质感、带旧快照的褪色暖调。
"""
import json
import os
import time
import urllib.request
import urllib.parse
import uuid

COMFY = "http://127.0.0.1:8188"
ROOT = r"."
OUT_DIR = os.path.join(ROOT, "assets", "ref", "P02")
os.makedirs(OUT_DIR, exist_ok=True)

UNET = "z_image_turbo_bf16.safetensors"
CLIP = "qwen_3_4b.safetensors"
VAE = "ae.safetensors"

PROMPT = (
    "a candid old snapshot photo brought to life in sophisticated watercolor concept art style for an animated film, "
    "delicate fine ink contour linework, loose transparent watercolor washes, granular cold-press paper texture, "
    "interior of a small cheap eatery in a southern Chinese factory town, early 2000s, warm tungsten bulb light, "
    "five Chinese male factory workers in their thirties sitting on low plastic stools around a low square table eating dinner, "
    "steamed rice bowls, stir-fry dishes, worn wooden table, thermos, folded newspapers, "
    "at the edge of the group sits a young Chinese father in his thirties, square honest face, neat short black hair, "
    "wearing a navy blue work jacket over a white shirt, laughing with eyes crinkled into crescents, mouth open mid-sentence "
    "as if telling a joke, one hand gesturing loosely, a pair of wooden chopsticks resting on the rim of his rice bowl, "
    "half a bottle of orange soda standing on the table with tiny condensation droplets glistening on the glass, "
    "beside him a sturdy fellow worker with a dark crew-cut laughing along, "
    "snapshot composition slightly tilted, slightly faded warm film-photo colors, soft halation around the lamp, "
    "muted nostalgic palette, hand painted, no text, no watermark"
)
NEG = ("text, watermark, logo, signature, frame, border, white border, anime, manga, cartoon, "
       "cel shaded, 3d render, cgi, photorealistic, dark muddy colors, deformed hands, extra fingers")
SEED = 2026110801
W, H = 1344, 768


def post_json(path, payload):
    req = urllib.request.Request(COMFY + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def get_json(path):
    with urllib.request.urlopen(COMFY + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


graph = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "lumina2"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["2", 0]}},
    "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}},
    "6": {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
    "7": {"class_type": "KSampler", "inputs": {
        "seed": SEED, "steps": 8, "cfg": 1.0, "sampler_name": "res_multistep",
        "scheduler": "simple", "denoise": 1.0,
        "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "prop/P02_v01", "images": ["8", 0]}},
}

resp = post_json("/prompt", {"prompt": graph, "client_id": str(uuid.uuid4())})
pid = resp["prompt_id"]
print("queued", pid, flush=True)
t0 = time.time()
while True:
    time.sleep(3)
    hist = get_json(f"/history/{pid}")
    if pid in hist:
        entry = hist[pid]
        st = entry.get("status", {})
        if st.get("completed") or st.get("status_str") == "success":
            break
        if st.get("status_str") == "error":
            raise RuntimeError(json.dumps(entry)[:800])

imgs = entry["outputs"]["9"]["images"]
for img in imgs:
    qs = urllib.parse.urlencode({"filename": img["filename"],
                                 "subfolder": img.get("subfolder", ""),
                                 "type": img.get("type", "output")})
    with urllib.request.urlopen(f"{COMFY}/view?{qs}", timeout=120) as r:
        data = r.read()
    dest = os.path.join(OUT_DIR, "P02_v01.png")
    with open(dest, "wb") as f:
        f.write(data)
    print("saved", dest, len(data), "bytes", round(time.time() - t0, 1), "s", flush=True)
