# -*- coding: utf-8 -*-
"""全片粗剪 v0.7：27 镜成片按镜号顺序硬切拼接，无配乐、无字幕卡、无转场。

用途：给用户看的第一版「纯镜头素材」粗剪，总长 216.0 秒。
素材口径取自 tools/build_progress.py 的 `finals` 映射（shot01/02 定稿是
_h3_v2_bright / _h3_v2，不能按 shotNN_h3.mp4 猜），镜头标题取自 `shots_prev`。

本版刻意不做：配乐、环境音、转场、字幕、片头片尾卡、调色。
理由：先看清楚 27 镜本身的叙事节奏与情绪落点，二轮再加东西才不会把问题盖住。

Run: py -3.12 tools/roughcut_v07.py
输出:
  assets/h3_video/roughcut_v07_no_bgm.mp4
  tmp_qc/roughcut_v07_timeline.json   （剪映导入用时间线：每镜入出点/标题/段落/卡点）
"""
import ast
import io
import json
import os
import re
import subprocess
import sys

import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "tools", "build_progress.py")
VIDEO_DIR = os.path.join(ROOT, "assets", "h3_video")
OUT = os.path.join(VIDEO_DIR, "roughcut_v07_no_bgm.mp4")
CONCAT = os.path.join(ROOT, "tmp_qc", "roughcut_v07_concat.txt")
TIMELINE = os.path.join(ROOT, "tmp_qc", "roughcut_v07_timeline.json")

FPS, SHOT_SEC = 24, 8.0
EXPECTED_SEC = 216.0

SEGMENTS = [
    ("序·第一次告别", 1, 5),
    ("父亲的远行", 6, 11),
    ("母亲的店", 12, 14),
    ("成年与三代", 15, 22),
    ("遗物与空椅", 23, 24),
    ("病房·跳舞", 25, 26),
    ("幕布拉开", 27, 27),
]

CUES = {
    3: "主题初现·乐句悬置",
    5: "第一次告别·音区下沉",
    11: "最后一次通话·音乐停一拍",
    16: "旧发带收进小包·话停半拍",
    18: "三代的手·动机首次完整",
    23: "合盖坐到天黑·转小调",
    24: "两碗面空椅·全片最空",
    26: "没有音乐·孩子自己数拍子",
    27: "幕布拉开·音乐首次响起并解决",
}


TITLES = {
    "shot01": "楼道口幻觉", "shot02": "楼道口别发带", "shot03": "病房捧手",
    "shot04": "镜前梳头", "shot05": "清晨递发带", "shot06": "火车站送别",
    "shot07": "南方线·找工友", "shot08": "老照片·掏手机",
    "shot09": "—（镜头索引未收录，不臆造）",
    "shot10": "返校的车上", "shot11": "夜里的电话", "shot12": "晒书的人",
    "shot13": "两只碗", "shot14": "厨房的和好", "shot15": "再攒两年",
    "shot16": "婚礼·胸针与旧发带", "shot17": "我自己来",
    "shot18": "楼下晨光·婴儿车", "shot19": "报纸后面",
    "shot20": "妈，你晚上吃什么", "shot21": "一袋橘子",
    "shot22": "阳台择豆角", "shot23": "地址纸与盒子", "shot24": "两碗面",
    "shot25": "病房·跳舞之约", "shot26": "跳一点给外婆看",
    "shot27": "幕布拉开",
}


def load_index():
    tree = ast.parse(io.open(BUILD, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "finals":
                    finals = ast.literal_eval(node.value)
                    assert len(finals) == 27, f"finals 只有 {len(finals)} 镜"
                    return finals
    raise AssertionError("build_progress.py 里未找到 finals 字典")


def probe(path, ff):
    r = subprocess.run([ff, "-i", path], capture_output=True, text=True)
    txt = r.stderr
    dur = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", txt)
    res = re.search(r"(\d{3,4})x(\d{3,4})", txt)
    fps = re.search(r"([\d.]+)\s*fps", txt)
    return {
        "duration_s": (int(dur.group(1)) * 3600 + int(dur.group(2)) * 60
                       + float(dur.group(3))) if dur else 0.0,
        "resolution": res.group(0) if res else "?",
        "fps": float(fps.group(1)) if fps else 0.0,
        "has_audio": "Audio:" in txt,
    }


def main():
    finals = load_index()
    ff = imageio_ffmpeg.get_ffmpeg_exe()

    clips, rows = [], []
    for i in range(1, 28):
        sid = "shot%02d" % i
        name = finals[sid]
        path = os.path.join(VIDEO_DIR, name)
        assert os.path.exists(path), "缺成片 " + path
        info = probe(path, ff)
        assert info["resolution"] == "1280x720" and abs(info["fps"] - FPS) < 0.01, \
            f"{sid} 规格异常 {info}"
        assert not info["has_audio"], f"{sid} 带音轨，本版要求纯净画面"
        clips.append(path)
        in_s, out_s = (i - 1) * SHOT_SEC, i * SHOT_SEC
        seg = next(n for n, a, b in SEGMENTS if a <= i <= b)
        rows.append({
            "shot": sid,
            "title": TITLES[sid],
            "source": "assets/h3_video/" + name,
            "in_s": round(in_s, 2), "out_s": round(out_s, 2),
            "duration_s": SHOT_SEC, "frames": int(SHOT_SEC * FPS),
            "segment": seg, "transition_in": "硬切",
            "cue": CUES.get(i, ""),
            "spec": {"resolution": info["resolution"], "fps": info["fps"],
                     "audio": False},
        })

    with io.open(CONCAT, "w", encoding="utf-8") as f:
        for p in clips:
            f.write("file '" + p.replace("\\", "/").replace("'", "'\\''") + "'\n")

    cmd = [ff, "-y", "-f", "concat", "-safe", "0", "-i", CONCAT,
           "-c", "copy", "-an", "-movflags", "+faststart", OUT]
    print("FFMPEG:", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("concat copy 失败，改用重编码兜底", r.stderr[-500:], flush=True)
        cmd = [ff, "-y", "-f", "concat", "-safe", "0", "-i", CONCAT,
               "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
               "-pix_fmt", "yuv420p", "-r", str(FPS), "-an",
               "-movflags", "+faststart", OUT]
        r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-900:]

    out = probe(OUT, ff)
    print("OUTPUT:", os.path.relpath(OUT, ROOT), out, os.path.getsize(OUT), "B", flush=True)
    assert abs(out["duration_s"] - EXPECTED_SEC) < 0.1, \
        f"总长 {out['duration_s']}s != {EXPECTED_SEC}s"
    assert out["resolution"] == "1280x720" and not out["has_audio"]

    timeline = {
        "version": "v0.7 无配乐粗剪",
        "source_count": 27,
        "total_duration_s": out["duration_s"],
        "spec": {"resolution": "1280x720", "fps": FPS, "audio": False,
                 "codec": "h264 / yuv420p"},
        "editor_note": "剪映导入：按 in_s/out_s 顺序排 27 段，段间全部硬切；"
                       "本版不加任何配乐、环境音、转场、字幕、片头片尾卡与调色",
        "segments": [
            {"name": n, "shots": ["shot%02d" % i for i in range(a, b + 1)],
             "in_s": (a - 1) * SHOT_SEC, "out_s": b * SHOT_SEC}
            for n, a, b in SEGMENTS
        ],
        "shots": rows,
        "cues": [{"time_s": (k - 1) * SHOT_SEC, "note": v} for k, v in sorted(CUES.items())],
        "next": "二轮：3 处段落交界加 0.5s 叠化（会让总长变化，需从别处补回），"
                "接入配乐与三层音频，按 cue 卡点对齐",
    }
    with io.open(TIMELINE, "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    print("TIMELINE:", os.path.relpath(TIMELINE, ROOT), flush=True)
    print("ROUGHCUT_V07_DONE", flush=True)


if __name__ == "__main__":
    main()
