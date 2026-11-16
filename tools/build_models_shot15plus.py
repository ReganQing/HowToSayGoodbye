# -*- coding: utf-8 -*-
"""shot15+ 八个角色的 Lux3D 独立建模流水线（可续跑、每步留痕）。

流程：T-pose 图 → image-to-3d(G1-Turbo/100000/glb) → 上传 mesh
      → auto-rig → 下载 rigged → 上传 rigged
      → retarget(10 动作 / combined / glb) → 下载 animated

设计要点：
- 所有付费 POST 一旦返回 taskId 立刻写进台账；中断后用 --resume 只查询、不重新提交。
- 每个阶段的产物文件存在且台账标记 done 就跳过，重跑幂等。
- query 只认 status==3 成功；4/5/6 视为终态失败，保留 taskId 供人工排查。

用法：
  py -3.12 tools/build_models_shot15plus.py --only C06
  py -3.12 tools/build_models_shot15plus.py --resume
  py -3.12 tools/build_models_shot15plus.py --status
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
LEDGER = os.path.join(ROOT, "progress", "01_剧本分镜", "shot15+_参考图台账.json")
UPLOADS = os.path.join(ROOT, "assets", "uploads.json")
PY = sys.executable

# 一次 retarget 覆盖 shot15–27 全部动作需求（上限 10 个）。
# previs 脚本按 glb 内 clip 顺序取动作，顺序必须与提交顺序一致。
ANIMATIONS = [
    "Idle_Loop",              # 0 站姿待机
    "Walk_Loop",              # 1 走位
    "Sitting_Enter",          # 2 入座
    "Sitting_Idle_Loop",      # 3 坐姿待机
    "Sitting_Talking_Loop",   # 4 坐着说话
    "Idle_Talking_Loop",      # 5 站着说话
    "Idle_TalkingPhone_Loop", # 6 打电话
    "Interact",               # 7 递物/扶正/折纸/关火
    "Dance_Loop",             # 8 小满跳舞
    "Walk_Carry_Loop",        # 9 提橘子/推车
]
IDS = ["C06", "C06b", "C07", "C07b", "C11", "C16", "C17", "C18"]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ledger_load():
    with open(LEDGER, encoding="utf-8") as f:
        return json.load(f)


def ledger_save(d):
    tmp = LEDGER + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, LEDGER)


def item(d, cid):
    for it in d["model_progress"]["items"]:
        if it["cid"] == cid:
            return it
    raise KeyError(cid)


def mark(**kw):
    """把任意字段合并进当前处理项并立刻落盘。"""
    global CUR
    CUR.update(kw)
    ledger_save(LEDGER_DATA)


def cli(*args, timeout=900):
    cmd = [PY, os.path.join(TOOLS, "lux3d.py")] + [str(a) for a in args]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"CLI 失败 {' '.join(args[:2])}: {r.stdout[-400:]} {r.stderr[-400:]}")
    out = r.stdout.strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        # lux3d_upload.py 之类不走 CLI JSON 时返回纯文本
        return {"raw": out}


def upload(path):
    """上传本地文件，返回公开 URL。uploads.json 命中则复用。"""
    ap = os.path.abspath(path)
    records = {}
    if os.path.isfile(UPLOADS):
        with open(UPLOADS, encoding="utf-8") as f:
            records = json.load(f)
    rec = records.get(ap)
    if rec and rec.get("md5") == hashlib.md5(open(ap, "rb").read()).hexdigest():
        log(f"  上传复用 {os.path.basename(ap)}")
        return rec["url"]
    r = subprocess.run([PY, os.path.join(TOOLS, "lux3d_upload.py"), ap],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f"上传失败: {r.stdout[-500:]} {r.stderr[-500:]}")
    with open(UPLOADS, encoding="utf-8") as f:
        records = json.load(f)
    if ap not in records:
        raise RuntimeError(f"uploads.json 未写入 {ap}")
    log(f"  上传完成 {os.path.basename(ap)}")
    return records[ap]["url"]


def query_until_done(task_id, budget=900, interval=12):
    """只查询已存在的任务，不创建任何新任务。"""
    t0 = time.time()
    last = None
    while time.time() - t0 < budget:
        d = cli("query", task_id, timeout=60)
        st = d.get("status", last)
        last = st
        if st == 3:
            return d
        if st in (4, 5, 6):
            raise RuntimeError(f"task {task_id} 终态失败 status={st}: {json.dumps(d, ensure_ascii=False)[:500]}")
        log(f"  task {task_id} status={st}，等待 {interval}s")
        time.sleep(interval)
    raise TimeoutError(f"task {task_id} 超时，最后 status={last}（任务仍可用 --resume 续查）")


def download(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(path + ".part", "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    os.replace(path + ".part", path)
    size = os.path.getsize(path)
    if size < 10000:
        raise RuntimeError(f"下载文件异常小 {size}B: {path}")
    return size


def model_paths(cid):
    d = os.path.join(ROOT, "assets", "models", cid)
    return (os.path.join(d, "tex_mesh.glb"),
            os.path.join(d, "tex_mesh_rigged.glb"),
            os.path.join(d, "tex_mesh_animated.glb"))


def build(cid, resume=False):
    global CUR, LEDGER_DATA
    LEDGER_DATA = ledger_load()
    CUR = item(LEDGER_DATA, cid)
    mesh_p, rig_p, anim_p = model_paths(cid)
    os.makedirs(os.path.dirname(mesh_p), exist_ok=True)  # image CLI 下载前要求目录已存在
    log(f"=== {cid} 开始（resume={resume}）===")

    # --- 1. image-to-3d ---
    if CUR.get("image_to_3d") != "done" or not os.path.isfile(mesh_p):
        if resume and CUR.get("image_task_id"):
            raise RuntimeError(f"{cid} image 阶段未完成且无 task_id 续查入口，需人工核对")
        tpose_url = CUR.get("tpose_url") or tpose_url_of(cid)
        log(f"  image-to-3d 提交 {cid}")
        cli("image", tpose_url, mesh_p, "--version", "G1-Turbo",
            "--face-count", "100000", "--format", "glb", timeout=900)
        mark(image_to_3d="done", mesh=rel(mesh_p), mesh_size=os.path.getsize(mesh_p),
             tpose_url=tpose_url)
    else:
        log(f"  image-to-3d 已完成，跳过（{os.path.getsize(mesh_p)}B）")

    # --- 2. 上传 mesh ---
    mesh_url = CUR.get("mesh_upload_url")
    if not mesh_url:
        mesh_url = upload(mesh_p)
        mark(mesh_upload_url=mesh_url)

    # --- 3. auto-rig ---
    if CUR.get("auto_rig") != "done" or not os.path.isfile(rig_p):
        tid = CUR.get("rig_task_id")
        if not tid:
            log(f"  auto-rig 提交 {cid}")
            res = cli("auto-rig", mesh_url, timeout=120)
            tid = res.get("taskId")
            if not tid:
                raise RuntimeError(f"auto-rig 未返回 taskId: {res}")
            mark(rig_task_id=str(tid), rig_task_created=time.strftime("%Y-%m-%dT%H:%M:%S"))
        else:
            log(f"  auto-rig 续查 task {tid}")
        d = query_until_done(tid, budget=1200)
        outputs = d.get("outputs") or []
        rig_url = outputs[0].get("content") if outputs else None
        if not rig_url or not str(rig_url).startswith("http"):
            raise RuntimeError(f"auto-rig task {tid} 无 GLB URL: {outputs}")
        mark(rig_result_url=rig_url)
        size = download(rig_url, rig_p)
        log(f"  rigged GLB 下载完成 {size}B")
        mark(auto_rig="done", rigged=rel(rig_p), rigged_size=size)
    else:
        log(f"  auto-rig 已完成，跳过（{os.path.getsize(rig_p)}B）")

    # --- 4. 上传 rigged ---
    rig_upload_url = CUR.get("rigged_upload_url")
    if not rig_upload_url:
        rig_upload_url = upload(rig_p)
        mark(rigged_upload_url=rig_upload_url)

    # --- 5. retarget 十动作 ---
    if CUR.get("animations") != "done" or not os.path.isfile(anim_p):
        tid = CUR.get("retarget_task_id")
        if not tid:
            log(f"  retarget 提交 {cid}（{len(ANIMATIONS)} 动作 / combined）")
            args = ["retarget", rig_upload_url]
            for a in ANIMATIONS:
                args += ["--animation-id", a]
            args += ["--output-mode", "combined", "--format", "glb"]
            res = cli(*args, timeout=120)
            tid = res.get("taskId")
            if not tid:
                raise RuntimeError(f"retarget 未返回 taskId: {res}")
            mark(retarget_task_id=str(tid), animation_ids=ANIMATIONS,
                 retarget_task_created=time.strftime("%Y-%m-%dT%H:%M:%S"))
        else:
            log(f"  retarget 续查 task {tid}")
        d = query_until_done(tid, budget=1200)
        outputs = d.get("outputs") or []
        raw = outputs[0].get("content") if outputs else ""
        payload = json.loads(raw) if isinstance(raw, str) and raw.strip().startswith("{") else {}
        actions = payload.get("actions") or []
        ok = [a for a in actions if a.get("status") == "success" and a.get("animationGlbUrl")]
        if not ok:
            raise RuntimeError(f"retarget task {tid} 无成功动作: {actions}")
        mark(retarget_actions=actions)
        urls = sorted({a["animationGlbUrl"] for a in ok})
        if len(urls) > 1:
            raise RuntimeError(f"combined 模式返回多个 URL，需人工确认: {urls}")
        size = download(urls[0], anim_p)
        log(f"  animated GLB 下载完成 {size}B，成功动作 {len(ok)}/{len(ANIMATIONS)}")
        mark(animations="done", animated=rel(anim_p), animated_size=size,
             animated_clip_order=[a["animation_id"] for a in ok],
             note="G1-Turbo / 100000 面 / glb；auto-rig + combined 十动作完成")
    else:
        log(f"  retarget 已完成，跳过（{os.path.getsize(anim_p)}B）")

    log(f"=== {cid} 完成 ===")


def tpose_url_of(cid):
    d = ledger_load()
    for r in d["tpose_jobs"]["items"]:
        if r["version"] == cid + "_tpose_v01":
            return r["upload_url"]
    raise KeyError(f"台账无 {cid} 的 T-pose upload_url")


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def status():
    d = ledger_load()
    for it in d["model_progress"]["items"]:
        cid = it["cid"]
        m, r, a = model_paths(cid)
        print(f"{cid:5s} mesh={'Y' if os.path.isfile(m) else '-'} "
              f"rig={'Y' if os.path.isfile(r) else '-'} "
              f"anim={'Y' if os.path.isfile(a) else '-'} | "
              f"image={it.get('image_to_3d')} rig={it.get('auto_rig')} "
              f"anims={it.get('animations')} | tasks "
              f"{it.get('rig_task_id','-')}/{it.get('retarget_task_id','-')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.status:
        status()
        return 0
    targets = args.only or IDS
    failed = []
    for cid in targets:
        try:
            build(cid, resume=args.resume)
        except Exception as e:
            log(f"!!! {cid} 失败: {type(e).__name__}: {str(e)[:400]}")
            failed.append((cid, str(e)[:200]))
    print(json.dumps({"failed": failed, "ok": [c for c in targets if c not in dict(failed)]},
                     ensure_ascii=False, indent=2), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
