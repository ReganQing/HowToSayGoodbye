# -*- coding: utf-8 -*-
"""等待 ComfyUI 的 H3 Ref2VA 任务完成，并打印输出文件名。

shot15 曾出现「提交后 15 分钟 history 里还查不到、但队列 running=1 / GPU 100%」
的情况，直接判超时会误伤已付费的生成任务。这里只轮询、不重提，
并把队列状态一起打进日志，便于事后追溯。

用法：
  py -3.12 tools/wait_h3.py <prompt_id>
  py -3.12 tools/wait_h3.py <prompt_id> --timeout 2400 --interval 20
"""
import argparse
import json
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:8188"


def get(path, timeout=30):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as resp:
        return json.loads(resp.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt_id")
    ap.add_argument("--timeout", type=int, default=2400, help="总等待秒数，默认 2400")
    ap.add_argument("--interval", type=int, default=20, help="轮询间隔秒数，默认 20")
    a = ap.parse_args()

    deadline = time.time() + a.timeout
    print(f"等待 {a.prompt_id}（上限 {a.timeout}s）", flush=True)
    while True:
        try:
            h = get("/history/" + a.prompt_id)
            if a.prompt_id in h:
                item = h[a.prompt_id]
                st = item.get("status", {})
                print("status_str:", st.get("status_str"), "completed:", st.get("completed"),
                      flush=True)
                for nid, o in sorted(item.get("outputs", {}).items()):
                    for kind in ("images", "gifs", "videos"):
                        for f in o.get(kind, []):
                            print("OUTPUT", nid, kind, f.get("filename"), flush=True)
                print("WAIT_H3_DONE", flush=True)
                return 0 if st.get("completed") else 1
        except Exception as e:
            print("history 查询异常:", repr(e), flush=True)

        if time.time() > deadline:
            print("WAIT_H3_TIMEOUT（任务可能仍在跑，勿重提）", flush=True)
            return 2
        try:
            q = get("/queue")
            print(f"[{time.strftime('%H:%M:%S')}] running={len(q.get('queue_running', []))} "
                  f"pending={len(q.get('queue_pending', []))}", flush=True)
        except Exception as e:
            print("队列查询异常:", repr(e), flush=True)
        time.sleep(a.interval)


if __name__ == "__main__":
    sys.exit(main())
