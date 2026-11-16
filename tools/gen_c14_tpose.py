# -*- coding: utf-8 -*-
"""C14 工友叔叔 T-pose 单视图（水彩，参照 C05_v08 的做法，auto-rig 用）。"""
import json
import os
import time
import urllib.request
import urllib.parse

COMFY = "http://127.0.0.1:8188"
OUT = r"assets/ref/C14/C14_v08.png"

PROMPT = ("a Chinese man in his late fifties, weathered square kind face, short graying crew-cut hair, deep smile lines, "
          "slightly stooped shoulders, a clean light gray short-sleeve polo shirt, clean dark loose trousers, black cloth slippers, "
          "sophisticated watercolor concept art for an animated film, character design sheet, "
          "full body single front view, standing straight in a strict T-pose, "
          "both arms extended straight out to the sides horizontally at shoulder level, arms fully separated from the torso, "
          "palms facing forward, legs straight with feet slightly apart, entire body visible from head to feet including fingertips, "
          "realistic human proportions seven and a half heads tall, natural small eyes, realistic facial anatomy with defined features, "
          "delicate fine ink contour linework, loose transparent watercolor washes, visible granular cold-press paper texture, "
          "paint pooling and dry brush edges, hand painted, fashion editorial illustration quality, "
          "restrained muted palette of indigo blue black denim grey and warm cream, "
          "clean untextured white paper background, soft even daylight, "
          "small round watercolor palette swatches along the right edge, no text, no watermark")
NEG = ("anime, manga, cartoon, cel shaded, flat color blocks, big eyes, large sparkly eyes, cute, kawaii, chibi, "
       "doll face, baby face, childish proportions, storybook, 3d render, cgi, photorealistic, photo, "
       "digital airbrush, smooth plastic skin, heavy texture, muddy dark colors, "
       "text, watermark, logo, signature, extra characters, cropped feet, cropped head, blurry, "
       "deformed hands, mismatched duplicate, dirty clothes, stains, frame, border, arms down, arms bent")

graph = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["2", 0]}},
    "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}},
    "6": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1536, "batch_size": 1}},
    "7": {"class_type": "KSampler", "inputs": {
        "seed": 2026110721, "steps": 8, "cfg": 1.0, "sampler_name": "res_multistep",
        "scheduler": "simple", "denoise": 1.0,
        "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "Lux3Dref/C14_v08", "images": ["8", 0]}},
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
