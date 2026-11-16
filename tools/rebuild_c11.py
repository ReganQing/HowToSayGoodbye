# -*- coding: utf-8 -*-
"""C11 重建：用 C11_tpose_v02.png（横版、双手完整）替换被裁切的 v01。

背景：v01 的 auto-rig（task 7153055）报 RIG_ELIGIBILITY_FAILED，
根因是 T-pose 图里双手被画面左右边缘裁掉，骨架关键点不足。
失败的远端任务不重提；这里从新的 T-pose 图重新走完整链路。

用法（在 C11_tpose_v02.png 目检通过后执行）：
  py -3.12 tools/rebuild_c11.py --check
  py -3.12 tools/rebuild_c11.py
"""
import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "progress", "01_剧本分镜", "shot15+_参考图台账.json")
UPLOADS = os.path.join(ROOT, "assets", "uploads.json")
TPOSE = os.path.join(ROOT, "assets", "ref_tpose", "C11_tpose_v02.png")
MODEL_DIR = os.path.join(ROOT, "assets", "models", "C11")


def item(d):
    for it in d["model_progress"]["items"]:
        if it["cid"] == "C11":
            return it
    raise KeyError("C11")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not os.path.isfile(TPOSE):
        raise SystemExit(f"缺 {TPOSE}，先跑 gen_tpose_shot15plus.py --only C11 并目检")
    with open(LEDGER, encoding="utf-8") as f:
        d = json.load(f)
    it = item(d)
    print("v02 图:", TPOSE, os.path.getsize(TPOSE), "B")
    print("旧失败记录:", it.get("failure", {}).get("code"))
    if args.check:
        print("--check：只核对，不上传、不改台账、不提交任何付费任务")
        return 0

    # 1. 上传新 T-pose 图
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "lux3d_upload.py"), TPOSE],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=600)
    if r.returncode != 0:
        raise SystemExit(f"上传失败: {r.stdout[-400:]} {r.stderr[-400:]}")
    with open(UPLOADS, encoding="utf-8") as f:
        records = json.load(f)
    url = records[os.path.abspath(TPOSE)]["url"]
    print("上传完成:", url)

    # 2. 旧 mesh 保留作过程素材，不删
    old_mesh = os.path.join(MODEL_DIR, "tex_mesh.glb")
    if os.path.isfile(old_mesh):
        backup = os.path.join(MODEL_DIR, "tex_mesh_v01_rig_failed.glb")
        os.replace(old_mesh, backup)
        print("旧 mesh 归档:", os.path.basename(backup))

    # 3. 重置 C11 的建模状态，让 build_models 从头走；失败记录留痕
    it["tpose_version"] = "C11_tpose_v02"
    it["tpose_url"] = url
    it["image_to_3d"] = "pending"
    it["mesh"] = ""
    it["mesh_size"] = None
    it["mesh_upload_url"] = ""
    it["auto_rig"] = "pending"
    it["animations"] = "pending"
    for k in ("rig_task_id", "rig_result_url", "rigged", "rigged_size", "rigged_upload_url",
              "retarget_task_id", "retarget_actions", "animated", "animated_size",
              "animated_clip_order"):
        it.pop(k, None)
    it.setdefault("failure", {})["resolved_by"] = "C11_tpose_v02 横版重出 + 完整重建"
    it["note"] = "v01 T-pose 手部裁切导致 RIG_ELIGIBILITY_FAILED；改用 v02 重建中"
    d.setdefault("recovery_log", []).append({
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "reason": "C11 auto-rig RIG_ELIGIBILITY_FAILED：T-pose 双手被裁",
        "policy": "失败任务 7153055 不重提；换横版 T-pose 图从 image-to-3d 重新走完整链路",
        "new_tpose_url": url,
    })
    tmp = LEDGER + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, LEDGER)
    print("台账已重置 C11 状态（旧失败记录保留）")

    # 4. 走标准建模流水线
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_models_shot15plus.py"),
                        "--only", "C11"], cwd=ROOT, timeout=2400)
    print("build 返回码:", r.returncode)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
