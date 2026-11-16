# -*- coding: utf-8 -*-
"""取回 7 个「服务端已成功、本地下载失败」的 image-to-3d 产物。

事故：首轮批量建模时 `assets/models/<CID>/` 目录未预建，lux3d image 命令
在下载阶段报 `Output directory does not exist`。远端任务 status=3 且已扣 1 积分/个，
**不能重新提交**。本脚本只按 taskId 查询既有任务并下载，不创建任何新任务。

taskId 与 CID 的对应按提交时间（tmp_qc/build_models_shot15plus.log）逐一对齐。
"""
import hashlib
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "progress", "01_剧本分镜", "shot15+_参考图台账.json")
TOOLS = os.path.join(ROOT, "tools")

TASKS = [
    ("C06b", 7148701, "00:18:17"),
    ("C07",  7148991, "00:19:20"),
    ("C07b", 7149256, "00:20:22"),
    ("C11",  7149504, "00:21:25"),
    ("C16",  7149709, "00:22:28"),
    ("C17",  7150248, "00:24:17"),
    ("C18",  7150631, "00:25:35"),
]


def query(tid):
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "lux3d.py"), "query", str(tid)],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=90)
    if r.returncode != 0:
        raise RuntimeError(f"query {tid} 失败: {r.stdout[-300:]} {r.stderr[-300:]}")
    return json.loads(r.stdout)


def download(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}), timeout=300) as r, open(path + ".part", "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    os.replace(path + ".part", path)
    return os.path.getsize(path)


def main():
    with open(LEDGER, encoding="utf-8") as f:
        ledger = json.load(f)
    items = {it["cid"]: it for it in ledger["model_progress"]["items"]}
    results = []
    for cid, tid, submitted in TASKS:
        path = os.path.join(ROOT, "assets", "models", cid, "tex_mesh.glb")
        d = query(tid)
        if d.get("status") != 3:
            raise RuntimeError(f"{cid} task {tid} 状态 {d.get('status')}，跳过等待人工核对")
        url = d["outputs"][0]["content"]
        size = download(url, path)
        if size < 1000000:
            raise RuntimeError(f"{cid} 文件异常小 {size}B")
        md5 = hashlib.md5(open(path, "rb").read()).hexdigest()
        it = items[cid]
        it.update({
            "image_to_3d": "done",
            "mesh": f"assets/models/{cid}/tex_mesh.glb",
            "mesh_size": size,
            "mesh_md5": md5,
            "image_task_id": str(tid),
            "image_submitted_at": submitted,
            "image_recovery": "首轮目录未预建导致下载失败；远端任务 status=3 已扣费，按 taskId 查询并下载，未重复提交",
        })
        print(f"OK {cid:5s} task {tid} -> {size} B md5 {md5[:12]}", flush=True)
        results.append({"cid": cid, "task_id": tid, "url": url, "size": size, "md5": md5})
    ledger.setdefault("recovery_log", []).append({
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "reason": "image-to-3d 下载阶段 Output directory does not exist",
        "policy": "只查询既有 taskId 并下载，未重新提交任何付费任务",
        "items": results,
    })
    tmp = LEDGER + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
    os.replace(tmp, LEDGER)
    print("RECOVERY_DONE", len(results), flush=True)


if __name__ == "__main__":
    main()
