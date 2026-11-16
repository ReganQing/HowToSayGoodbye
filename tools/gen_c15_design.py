# -*- coding: utf-8 -*-
"""C15 周远 三视图设计稿（水彩，对齐 C05_v07 版式：front/side/back + 右侧圆形色板）。"""
import json
import os
import time
import urllib.request
import urllib.parse

COMFY = "http://127.0.0.1:8188"
OUT = r"assets/ref/C15/C15_v02.png"

PROMPT = ("a young Chinese man in his mid-twenties, gentle scholarly engineer, realistic adult facial structure, "
          "defined jawline and cheekbones, natural small narrow eyes with single eyelids, subtle warm expression, "
          "neat short black hair with natural fringe, slim thin-frame round glasses, clean and understated clothing, "
          "a soft beige knit sweater over a light blue collared shirt, straight dark grey trousers, plain white sneakers, "
          "sophisticated watercolor concept art for an animated film, character design sheet, "
          "full body three views standing in a row, front view, side view, back view, "
          "standing naturally with relaxed posture, arms hanging loosely at the sides, "
          "entire body visible from head to feet in all three views, realistic human proportions seven and a half heads tall, "
          "delicate fine ink contour linework, loose transparent watercolor washes, visible granular cold-press paper texture, "
          "paint pooling and dry brush edges, hand painted, fashion editorial illustration quality, "
          "restrained muted palette of warm beige cream light blue and soft grey, "
          "clean untextured white paper background, soft even daylight, "
          "small round watercolor palette swatches along the right edge, no text, no watermark")
NEG = ("anime, manga, cartoon, cel shaded, flat color blocks, big eyes, large sparkly eyes, cute, kawaii, chibi, "
       "doll face, baby face, childish proportions, storybook, 3d render, cgi, photorealistic, photo, "
       "digital airbrush, smooth plastic skin, heavy texture, muddy dark colors, "
       "text, watermark, logo, signature, extra characters, cropped feet, cropped head, blurry, "
       "deformed hands, mismatched duplicate, dirty clothes, stains, frame, border, "
       "arms raised, T-pose, hands in pockets, crossed arms")

graph = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["2", 0]}},
    "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}},
    "6": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "7": {"class_type": "KSampler", "inputs": {
        "seed": 2026111202, "steps": 8, "cfg": 1.0, "sampler_name": "res_multistep",
        "scheduler": "simple", "denoise": 1.0,
        "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "Lux3Dref/C15_v02", "images": ["8", 0]}},
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
