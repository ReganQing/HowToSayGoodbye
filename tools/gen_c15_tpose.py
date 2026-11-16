# -*- coding: utf-8 -*-
"""C15 周远 写实 T-pose 单视图（auto-rig 用）。

踩坑教训（C14）：水彩风画不出严格 T-pose → RIG_ELIGIBILITY_FAILED。
解法：写实风格 + T-pose 要求放提示词句首 + 20 步采样（v08c 配方）。
"""
import json
import os
import time
import urllib.request
import urllib.parse

COMFY = "http://127.0.0.1:8188"
OUT = r"assets/ref/C15/C15_tpose_v02.png"

PROMPT = ("strict T-pose full-body character reference photo, both arms extended straight out to the sides "
          "perfectly horizontally at exact shoulder level, arms forming one straight horizontal line across the shoulders, "
          "arms fully separated from the torso, palms facing forward, "
          "a young Chinese man in his mid-twenties, gentle scholarly engineer, realistic adult facial structure, "
          "defined jawline, natural small narrow eyes with single eyelids, subtle warm expression, "
          "neat short black hair, slim thin-frame round glasses, "
          "front view, standing straight facing the camera, legs straight feet slightly apart, "
          "entire body visible from head to shoes including all fingertips, "
          "a soft beige knit sweater over a light blue collared shirt, straight dark grey trousers, plain white sneakers, "
          "photorealistic, plain light gray seamless studio background, soft even diffused lighting, no shadows on the backdrop, "
          "natural skin texture, no text, no watermark")
NEG = ("arms down, arms hanging, arms at sides, arms lowered, arms diagonal, arms angled down, arms bent, elbows bent, "
       "text, watermark, logo, signature, extra people, cropped, blurry, deformed hands, "
       "cartoon, anime, illustration, watercolor, sketch, "
       "dirty clothes, stains, wrinkled fabric, worn out clothing, messy hair")

graph = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["2", 0]}},
    "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}},
    "6": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1536, "batch_size": 1}},
    "7": {"class_type": "KSampler", "inputs": {
        "seed": 2026111212, "steps": 20, "cfg": 1.0, "sampler_name": "res_multistep",
        "scheduler": "simple", "denoise": 1.0,
        "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "Lux3Dref/C15_tpose_v02", "images": ["8", 0]}},
}

req = urllib.request.Request(COMFY + "/prompt", data=json.dumps({"prompt": graph}).encode("utf-8"),
                             headers={"Content-Type": "application/json"})
pid = json.loads(urllib.request.urlopen(req, timeout=60).read())["prompt_id"]
print("queued", pid, flush=True)
while True:
    time.sleep(3)
    h = json.loads(urllib.request.urlopen(COMFY + f"/history/{pid}", timeout=60).read())
    if pid in h:
        entry = h[pid]
        st = entry.get("status", {})
        if st.get("status_str") == "error":
            raise SystemExit("generation failed: " + json.dumps(entry)[:600])
        if st.get("completed") or st.get("status_str") == "success":
            break
img = entry["outputs"]["9"]["images"][0]
qs = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img.get("subfolder", ""), "type": "output"})
data = urllib.request.urlopen(f"{COMFY}/view?{qs}", timeout=120).read()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "wb") as f:
    f.write(data)
print("saved", OUT, flush=True)
