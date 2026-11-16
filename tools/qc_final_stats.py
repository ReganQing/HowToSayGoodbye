# -*- coding: utf-8 -*-
"""成片程序化质检：亮度 / 突变帧 / 帧间差 / 每 24 帧亮度 / 首中末平均 RGB。

口径与 shot14/15/16 的 QC 报告一致（见 tmp_qc/shot16_final_stats.json）：
  brightness              每帧 RGB 全通道均值，再对全片求 mean/std/min/max
  brightness_jump_frames  相邻帧亮度差绝对值 > --jump-threshold 的帧号
  interframe_diff         相邻帧逐像素绝对差的平均值（0–255），对全片求 mean/std/max
  interframe_diff_top6    最大的 6 个 [帧号, 差值]，帧号取后一帧编号
  brightness_per_24_frames 每 24 帧一组取均值，共 8 组
  avg_rgb_first_mid_last  首帧 / 中间帧 / 末帧的逐通道平均

用法：
  py -3.12 tools/qc_final_stats.py assets/h3_video/shot16_h3_v02.mp4 -o tmp_qc/shot16b_final_stats.json
  py -3.12 tools/qc_final_stats.py --frames-dir <联系表 _frames 目录> -o <json>

联系表与关键帧目检仍用 tools/qc_allframes.py；本脚本只出数值，不替代目检。

口径复验：用 shot16 v01 的 192 张全帧跑本脚本得亮度 122.52±0.74 (120.94~123.65)、
帧间差 2.104±0.601 max 3.672、零突变帧、每 24 帧亮度 123.26→121.38→123.01，
与当时的手写统计 122.53 / 2.108 / 3.676 一致（四舍五入误差 ≤0.01）。
注意亮度必须是 Rec.601 加权灰度，用 RGB 简单平均会整体偏低约 3.2。
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def extract_frames(mp4, out):
    os.makedirs(out, exist_ok=True)
    if imageio_ffmpeg is None:
        raise RuntimeError("需要 imageio-ffmpeg：py -3.12 -m pip install imageio-ffmpeg")
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-i", mp4, "-fps_mode", "passthrough",
                    os.path.join(out, "f_%04d.png"), "-loglevel", "error"], check=True)


def frame_names(d):
    names = sorted(n for n in os.listdir(d) if n.lower().endswith(".png"))
    assert names, f"{d} 里没有 png"
    return names


def iter_frames(d, names):
    """流式读取，只保留上一帧；192 帧 720p 全量驻留会吃掉 2 GB 内存。"""
    for n in names:
        with Image.open(os.path.join(d, n)) as im:
            yield np.asarray(im.convert("RGB"), dtype=np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", nargs="?", default=None, help="成片 mp4")
    ap.add_argument("--frames-dir", default=None, help="直接读已有抽帧目录，跳过抽帧")
    ap.add_argument("-o", "--output", required=True, help="输出 json")
    ap.add_argument("--jump-threshold", type=float, default=3.0,
                    help="相邻帧亮度差超过此值记为突变帧，默认 3.0")
    a = ap.parse_args()
    assert a.source or a.frames_dir, "需要 mp4 或 --frames-dir"

    tmp = None
    if a.frames_dir:
        frames_dir = a.frames_dir
        source = a.frames_dir
        source_md5 = None
    else:
        tmp = tempfile.mkdtemp(prefix="qc_final_stats_")
        extract_frames(a.source, tmp)
        frames_dir = tmp
        source = a.source
        source_md5 = md5(a.source)

    names = frame_names(frames_dir)
    n_frames = len(names)
    mid_idx = n_frames // 2
    bright, diffs, rgb_at = [], [], {}
    W = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    prev_gray = None
    for i, arr in enumerate(iter_frames(frames_dir, names)):
        # Rec.601 加权灰度，与 shot14/15/16 历史报告口径一致（不是 RGB 简单平均）
        gray = arr @ W
        bright.append(float(gray.mean()))
        if prev_gray is not None:
            diffs.append(float(np.abs(gray - prev_gray).mean()))
        if i == 0:
            rgb_at["first"] = [round(float(arr[:, :, c].mean()), 1) for c in range(3)]
        if i == mid_idx:
            rgb_at["mid"] = [round(float(arr[:, :, c].mean()), 1) for c in range(3)]
        if i == n_frames - 1:
            rgb_at["last"] = [round(float(arr[:, :, c].mean()), 1) for c in range(3)]
        prev_gray = gray
    rgb = [rgb_at["first"], rgb_at["mid"], rgb_at["last"]]

    bv, dv = np.array(bright), np.array(diffs)
    jump = [i + 2 for i in range(1, len(bright))
            if abs(bright[i] - bright[i - 1]) > a.jump_threshold]
    top6 = [[int(i + 2), round(float(diffs[i]), 2)]
            for i in np.argsort(dv)[-6:][::-1]]
    per24 = [round(float(bv[s:s + 24].mean()), 2)
             for s in range(0, len(bright), 24)]

    out = {
        "source": source,
        "source_md5": source_md5,
        "frame_count": n_frames,
        "jump_threshold": a.jump_threshold,
        "brightness_mean": round(float(bv.mean()), 2),
        "brightness_std": round(float(bv.std()), 2),
        "brightness_min": round(float(bv.min()), 2),
        "brightness_max": round(float(bv.max()), 2),
        "brightness_jump_frames": jump,
        "interframe_diff_mean": round(float(dv.mean()), 3),
        "interframe_diff_std": round(float(dv.std()), 3),
        "interframe_diff_max": round(float(dv.max()), 3),
        "interframe_diff_top6": top6,
        "brightness_per_24_frames": per24,
        "avg_rgb_first_mid_last": rgb,
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    with open(a.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"帧数 {out['frame_count']}  亮度 {out['brightness_mean']} ± {out['brightness_std']} "
          f"({out['brightness_min']}~{out['brightness_max']})", flush=True)
    print(f"突变帧 {jump}  帧间差 {out['interframe_diff_mean']} ± "
          f"{out['interframe_diff_std']} max {out['interframe_diff_max']}", flush=True)
    print(f"每 24 帧亮度 {per24}", flush=True)
    print(f"首/中/末平均 RGB {rgb}", flush=True)
    print("写出", a.output, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
