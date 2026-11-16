# -*- coding: utf-8 -*-
"""Upload local files to Aholo Lux3D through the unified Asset/OUS chain.

Flow (per Lux3D skill protocol):
  GET /asset/v1/token (Authorization: <raw LUX3D_CN_API_KEY>, no Bearer)
  -> single/block OUS upload with ous-token-v2 header
  -> poll upload status until status=5 with a real URL

Usage:
  python3 tools/lux3d_upload.py <file> [<file> ...]

Prints one TSV line per file: <path>\t<url>. Also appends to assets/uploads.json.
The API key is read from process env, then HKCU\\Environment, then
HKLM\\Session Manager\\Environment. It is never printed or written to disk.
"""
import hashlib
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
import winreg

ASSET_BASE = "https://api.aholo3d.cn"
KEY_NAME = "LUX3D_CN_API_KEY"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_JSON = os.path.join(ROOT, "assets", "uploads.json")


def get_api_key():
    key = os.environ.get(KEY_NAME)
    if key:
        return key
    for hive, path in ((winreg.HKEY_CURRENT_USER, r"Environment"),
                       (winreg.HKEY_LOCAL_MACHINE,
                        r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")):
        try:
            with winreg.OpenKey(hive, path) as k:
                v, _ = winreg.QueryValueEx(k, KEY_NAME)
                if v:
                    return v
        except OSError:
            continue
    raise SystemExit(f"{KEY_NAME} not found in process env / HKCU / HKLM")


def envelope(raw):
    """Parse business envelope; return (data, error)."""
    try:
        d = json.loads(raw.decode("utf-8"))
    except Exception:
        return None, f"non-JSON response: {raw[:120]!r}"
    if isinstance(d, dict) and "c" in d:
        if str(d.get("c")) != "0":
            return None, f"business code c={d.get('c')} m={d.get('m')}"
        return d.get("d", d), None
    return d, None


def http(method, url, headers=None, data=None, timeout=30):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def form_only(fields):
    boundary = "----WBLux3D" + hashlib.md5(str(time.time()).encode()).hexdigest()
    body = b""
    for k, v in fields.items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode("utf-8")
    body += f"--{boundary}--\r\n".encode("utf-8")
    return body, f"multipart/form-data; boundary={boundary}"


def form_with_file(fields, file_field, filename, content):
    boundary = "----WBLux3D" + hashlib.md5(str(time.time()).encode()).hexdigest()
    body = b""
    for k, v in fields.items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode("utf-8")
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; "
             f"filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode("utf-8")
    body += content
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, f"multipart/form-data; boundary={boundary}"


def get_token(api_key):
    status, raw = http("GET", f"{ASSET_BASE}/asset/v1/token",
                       headers={"Authorization": api_key}, timeout=30)
    if status != 200:
        raise SystemExit(f"token HTTP {status}: {raw[:200]!r}")
    d, err = envelope(raw)
    if err:
        raise SystemExit(f"token failed: {err}")
    for k in ("ousToken", "globalDomain", "blockSize"):
        if not isinstance(d, dict) or k not in d:
            raise SystemExit(f"token response missing {k}: {list(d.keys()) if isinstance(d, dict) else d}")
    return d


def poll_status(domain, token, budget=120):
    t0 = time.time()
    last = None
    while time.time() - t0 < budget:
        status, raw = http("GET", f"{domain}/ous/api/v2/upload/status",
                           headers={"ous-token-v2": token}, timeout=30)
        d, err = envelope(raw)
        if not err and isinstance(d, dict):
            st = d.get("status")
            last = st
            if st == 5 and d.get("url"):
                return d["url"]
            if st in (6, 8):
                raise SystemExit(f"upload terminal failure status={st} m={d.get('m') or d.get('msg')}")
        time.sleep(1)
    raise SystemExit(f"upload status timeout after {budget}s (last status={last})")


def single_upload(domain, token, path, md5):
    with open(path, "rb") as f:
        content = f.read()
    body, ctype = form_with_file({"md5": md5}, "file", os.path.basename(path), content)
    status, raw = http("POST", f"{domain}/ous/api/v2/single/upload",
                       headers={"ous-token-v2": token, "Content-Type": ctype}, data=body, timeout=120)
    if status != 200:
        raise SystemExit(f"single upload HTTP {status}: {raw[:200]!r}")
    d, err = envelope(raw)
    if err:
        raise SystemExit(f"single upload failed: {err}")


def expand_lack(lack, blocks):
    if not lack:
        return list(range(1, blocks + 1))
    out = []
    for part in str(lack).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return [i for i in out if 1 <= i <= blocks]


def block_upload(domain, token, path, md5, size, block_size):
    blocks = math.ceil(size / block_size)
    body, ctype = form_only({"md5": md5, "blocks": str(blocks), "size": str(size),
                             "name": os.path.basename(path)})
    status, raw = http("POST", f"{domain}/ous/api/v2/block/upload/init",
                       headers={"ous-token-v2": token, "Content-Type": ctype}, data=body, timeout=60)
    if status != 200:
        raise SystemExit(f"block init HTTP {status}: {raw[:200]!r}")
    d, err = envelope(raw)
    if err:
        raise SystemExit(f"block init failed: {err}")
    if isinstance(d, dict) and d.get("deduplicated"):
        print("  block init: deduplicated, skipping parts", flush=True)
        return
    lack = expand_lack(d.get("lackBlocks") if isinstance(d, dict) else None, blocks)
    print(f"  block init: {blocks} blocks, uploading {len(lack)} parts", flush=True)
    with open(path, "rb") as f:
        for idx in lack:
            f.seek((idx - 1) * block_size)
            chunk = f.read(block_size)
            pbody, pctype = form_with_file({"block": str(idx)}, "file",
                                           os.path.basename(path), chunk)
            pstatus, praw = http("POST", f"{domain}/ous/api/v2/block/upload/part",
                                 headers={"ous-token-v2": token, "Content-Type": pctype},
                                 data=pbody, timeout=120)
            if pstatus != 200:
                raise SystemExit(f"block part {idx} HTTP {pstatus}: {praw[:200]!r}")
            pd, perr = envelope(praw)
            if perr:
                raise SystemExit(f"block part {idx} failed: {perr}")
    print("  all parts sent", flush=True)


def upload_file(path):
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise SystemExit(f"not a file: {path}")
    api_key = get_api_key()
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    tok = get_token(api_key)
    domain = str(tok["globalDomain"]).rstrip("/")
    ous = tok["ousToken"]
    block_size = int(tok["blockSize"])
    print(f"  upload {os.path.basename(path)} size={size} md5={md5[:8]}... blockSize={block_size}", flush=True)
    if size <= block_size:
        single_upload(domain, ous, path, md5)
    else:
        block_upload(domain, ous, path, md5, size, block_size)
    url = poll_status(domain, ous)
    return url, md5, size


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    records = {}
    if os.path.exists(UPLOADS_JSON):
        with open(UPLOADS_JSON, encoding="utf-8") as f:
            records = json.load(f)
    for path in sys.argv[1:]:
        url, md5, size = upload_file(path)
        records[os.path.abspath(path)] = {"url": url, "md5": md5, "size": size,
                                          "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        print(f"OK\t{os.path.abspath(path)}\t{url}", flush=True)
    os.makedirs(os.path.dirname(UPLOADS_JSON), exist_ok=True)
    with open(UPLOADS_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
