# -*- coding: utf-8 -*-
"""E10 出租屋厨房：水彩版环境参考图（与 E09 同一套朝北出租屋，H3 Picture 锚）。"""
import json, os, time, urllib.request, urllib.parse

COMFY = "http://127.0.0.1:8188"
STYLE = ("sophisticated watercolor concept art for an animated film, environment reference, "
         "delicate fine ink contour linework, loose transparent watercolor washes, "
         "granular cold-press paper texture, paint pooling and dry brush edges, hand painted, "
         "restrained muted palette of indigo blue black denim grey and warm cream, "
         "clear readable spatial structure, no people, no text, no watermark")
NEG = ("photorealistic, photo, 3d render, cgi, anime, manga, cartoon, cel shaded, "
       "text, watermark, logo, signature, people, blurry, muddy dark colors")

EID, VER, SEED = "E10", "E10_v01", 2026111213
DESC = ("a small modest kitchen corner in a rented northern Chinese apartment in the 2010s, "
        "a white tiled countertop with a stainless steel sink under a small window, "
        "a gooseneck faucet, a few washed ceramic bowls and plates stacked beside the sink, "
        "a dish rag draped over the faucet base, a bottle of dish soap, "
        "an electric kettle and a rice cooker on the counter, "
        "open shelves above holding jars and a small stack of bowls, "
        "a small square dining table with two simple wooden chairs tucked beside the counter, "
        "pale cool daylight from the window with a faint warm bounce from a wall lamp, "
        "sparse tidy humble atmosphere, "
        "empty room, no people")

def post_json(path, payload):
    req = urllib.request.Request(COMFY + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def get_json(path):
    with urllib.request.urlopen(COMFY + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

out_dir = r"assets/ref/E10"
os.makedirs(out_dir, exist_ok=True)
graph = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{DESC}, {STYLE}", "clip": ["2", 0]}},
    "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["2", 0]}},
    "6": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "7": {"class_type": "KSampler", "inputs": {
        "seed": SEED, "steps": 8, "cfg": 1.0, "sampler_name": "res_multistep",
        "scheduler": "simple", "denoise": 1.0,
        "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": f"Lux3Dref/{VER}", "images": ["8", 0]}},
}

pid = post_json("/prompt", {"prompt": graph})["prompt_id"]
print("queued", pid, flush=True)
while True:
    time.sleep(3)
    h = get_json(f"/history/{pid}")
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
out = os.path.join(out_dir, f"{VER}.png")
with open(out, "wb") as f:
    f.write(data)
print("saved", out, flush=True)
