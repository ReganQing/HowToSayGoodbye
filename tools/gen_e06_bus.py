# -*- coding: utf-8 -*-
"""E06 长途大巴车内参考图（写实风格，给 H3 当空间/质感锚；不做 Lux3D 重建，车内程序化）。
剧本：返校的车上（L237-241）。"""
import json
import os
import time
import urllib.request
import urllib.parse
import uuid

COMFY = "http://127.0.0.1:8188"
OUT_DIR = r"assets/ref/E06"
os.makedirs(OUT_DIR, exist_ok=True)

PROMPT = ("photorealistic interior of a long-distance coach bus in China in the early 2000s, "
          "a row of simple blue fabric passenger seats beside a large sliding window on the right, "
          "warm afternoon sunlight streaming through the window across the seat backs, "
          "soft blurred view of green banyan trees and a southern city street outside the window, "
          "worn grey carpet aisle, pale plastic window frame and curtain rail, simple luggage rack above, "
          "empty seats, quiet nostalgic atmosphere, slightly faded colors, "
          "no people, no text, no watermark")
NEG = ("text, watermark, logo, people, driver, crowded, blurry interior, fisheye, "
       "cartoon, anime, illustration, dark, night")
SEED = 2026110805
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
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["2", 0]}},
    "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}},
    "6": {"class_type": "EmptyLatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
    "7": {"class_type": "KSampler", "inputs": {
        "seed": SEED, "steps": 8, "cfg": 1.0, "sampler_name": "res_multistep",
        "scheduler": "simple", "denoise": 1.0,
        "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "prop/E06_v01", "images": ["8", 0]}},
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
    qs = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img.get("subfolder", ""), "type": img.get("type", "output")})
    with urllib.request.urlopen(f"{COMFY}/view?{qs}", timeout=120) as r:
        data = r.read()
    dest = os.path.join(OUT_DIR, "E06_v01.png")
    with open(dest, "wb") as f:
        f.write(data)
    print("saved", dest, len(data), "bytes", round(time.time() - t0, 1), "s", flush=True)
