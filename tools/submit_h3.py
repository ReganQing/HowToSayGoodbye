# -*- coding: utf-8 -*-
"""通用 H3 Ref2VA 提交器：校验输入素材 → 检查队列 → POST /prompt → 全程留痕。

用法：
  py -3.12 tools/submit_h3.py tools/h3_r2v_workflow_shot16b.json \
      --key 16b --inputs tmp_qc/shot16_inputs.json

--inputs 是可选的输入映射清单（json 数组，每项 src/dst/md5/size），
用来确认 ComfyUI input 目录里的裸文件名没被换过内容；不给则只校验存在性。

提交成功后：
  * prompt_id 写入 tools/redo_prompt_ids.json 的 --key
  * 完整记录（时间、工作流 MD5、seed、prefix、四张输入 MD5、队列初态）
    写入 tmp_qc/submit_h3_<key>.json
  * 只提交一次；如需等待，用 tools/wait_h3.py <prompt_id>

设计原则：付费生成绝不重复提交。提交前若队列非空，直接拒绝，除非显式 --force。
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMFY = "http://127.0.0.1:8188"
INPUT_DIR = r"D:\Comfy-Desktop\ComfyUI-Shared\input"
IDS = os.path.join(ROOT, "tools", "redo_prompt_ids.json")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get(path, timeout=30):
    with urllib.request.urlopen(COMFY + path, timeout=timeout) as r:
        return json.loads(r.read())


def collect_inputs(wf):
    """返回 [(裸文件名, class_type, node_id)]，按节点号排序便于留痕。"""
    out = []
    for nid in sorted(wf, key=lambda x: int(x) if x.isdigit() else 1 << 30):
        node = wf[nid]
        ct = node.get("class_type")
        if ct == "LoadImage":
            out.append((node["inputs"]["image"], ct, nid))
        elif ct == "LoadVideo":
            out.append((node["inputs"]["file"], ct, nid))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow")
    ap.add_argument("--key", default=None, help="redo_prompt_ids.json 的键，默认取工作流文件名")
    ap.add_argument("--inputs", default=None, help="输入映射清单 json（src/dst/md5/size）")
    ap.add_argument("--force", action="store_true", help="队列非空时仍提交（默认拒绝）")
    ap.add_argument("--no-record", action="store_true", help="不写 redo_prompt_ids.json")
    a = ap.parse_args()

    wf_path = os.path.join(ROOT, a.workflow) if not os.path.isabs(a.workflow) else a.workflow
    with open(wf_path, encoding="utf-8") as f:
        wf = json.load(f)
    key = a.key or os.path.basename(wf_path).replace("h3_r2v_workflow_", "").replace(".json", "")

    # 1. 输入素材校验
    mapping = {}
    if a.inputs:
        mp = os.path.join(ROOT, a.inputs) if not os.path.isabs(a.inputs) else a.inputs
        with open(mp, encoding="utf-8") as f:
            mapping = {m["dst"]: m for m in json.load(f)}
    checked = []
    ins = collect_inputs(wf)
    for name, ct, nid in ins:
        p = os.path.join(INPUT_DIR, name)
        assert os.path.exists(p), f"ComfyUI input 目录缺少 {name}（节点 {nid} {ct}）"
        m = md5(p)
        item = {"node": nid, "class_type": ct, "file": name, "md5": m,
                "size": os.path.getsize(p)}
        if name in mapping:
            exp = mapping[name]
            assert m == exp["md5"], f"{name} MD5 与清单不符：{m} != {exp['md5']}"
            src = os.path.join(ROOT, exp["src"])
            assert os.path.exists(src) and md5(src) == m, f"{name} 与项目源 {exp['src']} 不一致"
            item["src"] = exp["src"]
            item["match"] = "OK"
        checked.append(item)
        print(f"  {nid:>3} {ct:<11} {name:<28} {m}  {item.get('match', 'no-map')}", flush=True)

    # 2. 队列初态
    q = get("/queue")
    running, pending = len(q.get("queue_running", [])), len(q.get("queue_pending", []))
    print(f"队列初态 running={running} pending={pending}", flush=True)
    assert running == 0 and pending == 0 or a.force, \
        "队列非空，拒绝提交以免重复扣费；确认无在跑任务后再试，或用 --force"

    # 3. 提交（只发一次）
    payload = {"prompt": wf, "client_id": str(uuid.uuid4())}
    req = urllib.request.Request(
        COMFY + "/prompt", data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())
    pid = resp["prompt_id"]
    assert pid, f"提交未返回 prompt_id: {resp}"
    print("PROMPT_ID", pid, flush=True)

    # 4. 留痕
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    record = {
        "submitted_at": stamp,
        "key": key,
        "workflow": os.path.relpath(wf_path, ROOT).replace("\\", "/"),
        "workflow_md5": md5(wf_path),
        "prompt_id": pid,
        "seed": wf["9"]["inputs"].get("noise_seed"),
        "filename_prefix": wf["15"]["inputs"].get("filename_prefix"),
        "nodes": len(wf),
        "ref_images": wf["7"]["inputs"].get("ref_images"),
        "inputs": checked,
        "queue_before": {"running": running, "pending": pending},
        "prompt_length": len(wf["7"]["inputs"]["prompt"]),
    }
    tmp = os.path.join(ROOT, "tmp_qc")
    os.makedirs(tmp, exist_ok=True)
    rec_path = os.path.join(tmp, f"submit_h3_{key}.json")
    with open(rec_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    if not a.no_record:
        with open(IDS, encoding="utf-8") as f:
            ids = json.load(f)
        ids[key] = pid
        with open(IDS, "w", encoding="utf-8") as f:
            json.dump(ids, f, ensure_ascii=False, indent=2)

    print(f"留痕 {os.path.relpath(rec_path, ROOT)}  seed={record['seed']}  "
          f"prefix={record['filename_prefix']}  nodes={record['nodes']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
