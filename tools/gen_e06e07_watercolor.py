# -*- coding: utf-8 -*-
"""E06 大巴车内 / E07 宿舍夜景：重画为水彩版（与影片 freedom 风格同源，替代写实版当 H3 锚）。"""
import json, os, time, urllib.request, urllib.parse, uuid

COMFY = "http://127.0.0.1:8188"
STYLE = ("sophisticated watercolor concept art for an animated film, environment reference, "
         "delicate fine ink contour linework, loose transparent watercolor washes, "
         "granular cold-press paper texture, paint pooling and dry brush edges, hand painted, "
         "restrained muted palette of indigo blue black denim grey and warm cream, "
         "clear readable spatial structure, no people, no text, no watermark")
NEG = ("photorealistic, photo, 3d render, cgi, anime, manga, cartoon, cel shaded, "
       "text, watermark, logo, signature, people, blurry, muddy dark colors")

JOBS = [
    ("E06", "E06_v02", 2026110821,
     "interior of a long-distance coach bus in China in the early 2000s, "
     "a row of blue-grey fabric passenger seats beside a large sliding window with teal curtains, "
     "warm afternoon sunlight streaming through the window across the seat backs, "
     "soft green banyan trees and a southern city street outside the window, "
     "worn grey carpet aisle, pale luggage rack above, quiet nostalgic atmosphere"),
    ("E07", "E07_v02", 2026110822,
     "interior of a Chinese university dormitory room at night, early 2000s, "
     "a small wooden desk by the window with a warm glowing desk lamp, stacks of books and a red "
     "plastic thermos on the desk, a metal-frame bunk bed with a bookshelf along the wall, "
     "a window showing deep blue night sky and the dark silhouette of a campus tree, "
     "warm yellow lamplight pooling on the desk, the rest of the room in soft blue shadow, "
     "quiet intimate nighttime atmosphere"),
]

def post_json(path, payload):
    req = urllib.request.Request(COMFY + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def get_json(path):
    with urllib.request.urlopen(COMFY + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

for eid, ver, seed, desc in JOBS:
    out_dir = rf"assets/ref/{eid}"
    os.makedirs(out_dir, exist_ok=True)
    graph = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{desc}, {STYLE}", "clip": ["2", 0]}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}},
        "6": {"class_type": "EmptyLatentImage", "inputs": {"width": 1344, "height": 768, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "res_multistep",
            "scheduler": "simple", "denoise": 1.0,
            "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": f"prop/{ver}", "images": ["8", 0]}},
    }
    resp = post_json("/prompt", {"prompt": graph, "client_id": str(uuid.uuid4())})
    pid = resp["prompt_id"]
    print(eid, "queued", pid, flush=True)
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
    img = entry["outputs"]["9"]["images"][0]
    qs = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img.get("subfolder", ""), "type": img.get("type", "output")})
    with urllib.request.urlopen(f"{COMFY}/view?{qs}", timeout=120) as r:
        data = r.read()
    dest = os.path.join(out_dir, f"{ver}.png")
    with open(dest, "wb") as f:
        f.write(data)
    print(eid, "saved", dest, len(data), flush=True)
print("ALL DONE")
