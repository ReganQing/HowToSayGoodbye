# -*- coding: utf-8 -*-
"""粗剪 v0.8 = v0.7 + 观聆评审意见 1/4/5 的结构性返修（仍无配乐）。

观聆 5 条意见的落实口径：
  1) 叠化只给时间大跳跃 40s / 88s / 112s 各 0.5s；176s 合盖、184s 空椅不转场、留满静 → 落地
  2) 谷底 176–208s 压短 shot25 前 2s → 与「每镜 8s / 总长 216s」硬约束冲突，本版不动，
     改为补做尾帧→首帧接缝 QC，把塌不塌用数据说清楚
  3) shot26→27 否掉叠化、改 L-cut 声桥 → 本版无音轨，无法做声桥；记入二轮交接单，不假做
  4) shot27 延至 10–12s、闪后留 2–3s 空场 → 用「3 处叠化让出的 1.5s」补成片尾尾帧定格，
     既给空场又把总长精确守在 216.0s（Ron 决策）；要 2–3s 需放宽总长，交用户拍板
  5) 补查前镜尾帧→次镜首帧跳变、破 8s 均分 → 落地接缝 QC；8s=70BPM 下 9.33 拍非整小节
     属配乐写作问题，写入音频交接单，不在无配乐版改画面

做法：把 27 镜按段落合成 5 个块（段内 concat 无损直拼），块间用 xfade 叠化 3 处、
硬切 1 处（176s），最后 tpad 克隆末帧 1.5s。总长 = 214.5 + 1.5 = 216.0s。

Run: py -3.12 tools/roughcut_v08.py
输出:
  assets/h3_video/roughcut_v08_no_bgm.mp4
  tmp_qc/roughcut_v08_timeline.json
  tmp_qc/roughcut_v08_seams.json
"""
import io
import json
import os
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roughcut_v07 as v7  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(ROOT, "assets", "h3_video")
PARTS = os.path.join(ROOT, "tmp_qc", "rc08_parts")
OUT = os.path.join(VIDEO_DIR, "roughcut_v08_no_bgm.mp4")
TIMELINE = os.path.join(ROOT, "tmp_qc", "roughcut_v08_timeline.json")
SEAMS = os.path.join(ROOT, "tmp_qc", "roughcut_v08_seams.json")

FPS, XFADE, TAIL = 24, 0.5, 1.5
EXPECT_SEC = 216.0
BLOCKS = [(1, 5), (6, 11), (12, 14), (15, 22), (23, 27)]
XFADE_AT = [40.0, 88.0, 112.0]
XFADE_NOTES = ["童年→父亲线，时间大跳跃", "父亲线→母亲的店", "离家→成年"]
HARD_CUTS = [176.0, 184.0, 192.0, 200.0, 208.0]


def main():
    finals = v7.load_index()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(PARTS, exist_ok=True)

    blocks = []
    for bi, (a, b) in enumerate(BLOCKS, 1):
        lst = os.path.join(PARTS, f"block{bi}.txt")
        with io.open(lst, "w", encoding="utf-8") as f:
            for i in range(a, b + 1):
                p = os.path.join(VIDEO_DIR, finals["shot%02d" % i])
                f.write("file '" + p.replace("\\", "/") + "'\n")
        dst = os.path.join(PARTS, f"block{bi}.mp4")
        r = subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst,
                            "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                            "-pix_fmt", "yuv420p", "-r", str(FPS),
                            "-fps_mode", "cfr", "-an", dst],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-600:]
        info = v7.probe(dst, ff)
        want = (b - a + 1) * 8.0
        assert abs(info["duration_s"] - want) < 0.05, \
            f"block{bi} 时长 {info['duration_s']} != {want}"
        blocks.append(dst)
        print(f"BLOCK {bi}: shot{a:02d}–{b:02d}  {info['duration_s']}s", flush=True)

    durations = [(b - a + 1) * 8.0 for a, b in BLOCKS]
    offsets, cur, expect = [], durations[0], []
    for i in range(3):
        offsets.append(round(cur - XFADE, 2))
        cur = cur + durations[i + 1] - XFADE
        expect.append(round(cur, 2))
    print("XFADE offsets:", offsets, "→ 各步期望", expect,
          "→ 拼接", round(cur + durations[4], 2), "+ 尾帧", TAIL,
          "=", round(cur + durations[4] + TAIL, 2), "s", flush=True)

    def xfade_pair(pa, pb, offset, dst, want):
        """分步叠化：一次只接两段，输出后立刻校验时长，避免长链 filter 截断。"""
        fc = (f"[0:v]settb=AVTB,fps={FPS},format=yuv420p,setsar=1,setpts=PTS-STARTPTS[x];"
              f"[1:v]settb=AVTB,fps={FPS},format=yuv420p,setsar=1,setpts=PTS-STARTPTS[y];"
              f"[x][y]xfade=transition=fade:duration={XFADE}:offset={offset}[v]")
        r = subprocess.run([ff, "-y", "-i", pa, "-i", pb,
                            "-filter_complex", fc, "-map", "[v]",
                            "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                            "-pix_fmt", "yuv420p", "-r", str(FPS), "-an", dst],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-900:]
        got = v7.probe(dst, ff)["duration_s"]
        print(f"  XFADE {os.path.basename(pa)}+{os.path.basename(pb)} "
              f"offset={offset} → {got}s (期望 {want}s)", flush=True)
        assert abs(got - want) < 0.1, f"叠化步长异常 {got} != {want}"
        return dst

    s1 = xfade_pair(blocks[0], blocks[1], offsets[0],
                    os.path.join(PARTS, "step1.mp4"), expect[0])
    s2 = xfade_pair(s1, blocks[2], offsets[1],
                    os.path.join(PARTS, "step2.mp4"), expect[1])
    s3 = xfade_pair(s2, blocks[3], offsets[2],
                    os.path.join(PARTS, "step3.mp4"), expect[2])

    # 176s 保持硬切：concat demuxer 直拼第 5 块，再用 tpad 克隆末帧 1.5s
    lst = os.path.join(PARTS, "join.txt")
    with io.open(lst, "w", encoding="utf-8") as f:
        for p in (s3, blocks[4]):
            f.write("file '" + p.replace("\\", "/") + "'\n")
    r = subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-vf", f"tpad=stop_mode=clone:stop_duration={TAIL}",
                        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                        "-pix_fmt", "yuv420p", "-r", str(FPS), "-an",
                        "-movflags", "+faststart", OUT],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-1200:]
    out = v7.probe(OUT, ff)
    print("OUTPUT", os.path.relpath(OUT, ROOT), out, os.path.getsize(OUT), "B", flush=True)
    assert abs(out["duration_s"] - EXPECT_SEC) < 0.1, \
        f"总长 {out['duration_s']}s != {EXPECT_SEC}s"
    assert not out["has_audio"], "本版必须无音轨"

    # ---- 观聆第 5 条：前镜尾帧 → 次镜首帧 全接缝跳变 QC ----
    seam_rows = []
    for k in range(1, 27):
        t = k * 8.0
        vals = []
        for tag, ts in (("pre", t - 0.12), ("post", t + 0.12)):
            f = os.path.join(PARTS, f"s{k:02d}_{tag}.jpg")
            subprocess.run([ff, "-y", "-ss", str(ts), "-i", OUT,
                            "-frames:v", "1", "-q:v", "3", f],
                           capture_output=True, text=True, check=True)
            im = Image.open(f).convert("RGB").resize((32, 18))
            px = list(im.getdata())
            vals.append(sum(sum(p) / 3 for p in px) / len(px))
        seam_rows.append({
            "at_s": t, "prev_shot": "shot%02d" % k,
            "next_shot": "shot%02d" % (k + 1),
            "pre_luma": round(vals[0], 1), "post_luma": round(vals[1], 1),
            "delta": round(abs(vals[0] - vals[1]), 1),
            "transition": "0.5s 叠化" if t in XFADE_AT else "硬切",
        })
    worst = sorted(seam_rows, key=lambda x: -x["delta"])[:5]
    print("SEAM worst 5:", [(x["at_s"], x["delta"], x["transition"]) for x in worst],
          flush=True)
    with io.open(SEAMS, "w", encoding="utf-8") as f:
        json.dump({"shot": "roughcut_v08", "seam_count": 26,
                   "method": "每处接缝取 t-0.12s / t+0.12s 两帧，32x18 缩略灰度均值差",
                   "worst_5": worst, "all": seam_rows}, f,
                  ensure_ascii=False, indent=2)

    timeline = {
        "version": "v0.8 观聆评审返修版 · 无配乐",
        "total_duration_s": out["duration_s"],
        "spec": {"resolution": "1280x720", "fps": FPS, "audio": False},
        "based_on": "roughcut_v07_no_bgm.mp4 + 观聆有条件通过意见 1/4/5",
        "transitions": [
            {"at_s": t, "type": "0.5s 叠化", "note": n,
             "shots": ["shot%02d" % int(t / 8), "shot%02d" % (int(t / 8) + 1)]}
            for t, n in zip(XFADE_AT, XFADE_NOTES)
        ] + [{"at_s": t, "type": "硬切", "note": "情绪谷底不转场、留满静"}
             for t in HARD_CUTS],
        "tail_hold": {"start_s": 214.5, "duration_s": TAIL,
                      "method": "tpad 克隆末帧",
                      "note": "红发带闪后留空场；叠化让出 1.5s 正好补回，总长仍 216.0s"},
        "remaining_for_round2": [
            "L-cut 声桥：208s 音乐于 shot26 尾 0.5–1s 先入、画面硬切（需配乐，本版无音轨不做）",
            "shot27 是否延至 10–12s：与 Ron 总片长 216s 决策冲突，待用户拍板",
            "shot25 是否压短前 2s：与每镜 8s 规格冲突，待用户拍板",
            "配乐 70BPM 下 8s = 9.33 拍非整小节，末镜 3/4 需按最终长度重对齐卡点（交绿野）",
            "跨镜道具 / 四代角色一致性、叠化重影逐镜检查",
        ],
        "editor_note": "剪映导入按 8s 网格排 27 段；3 处叠化需前后镜各让出 0.5s 重叠；"
                       "片尾 1.5s 为末帧定格，不是新镜头",
        "shots": [
            {"shot": "shot%02d" % i, "title": v7.TITLES["shot%02d" % i],
             "in_s": (i - 1) * 8.0, "out_s": i * 8.0,
             "source": "assets/h3_video/" + finals["shot%02d" % i],
             "cue": v7.CUES.get(i, "")}
            for i in range(1, 28)
        ],
    }
    with io.open(TIMELINE, "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    print("TIMELINE", os.path.relpath(TIMELINE, ROOT), flush=True)
    print("SEAMS", os.path.relpath(SEAMS, ROOT), flush=True)
    print("ROUGHCUT_V08_DONE", flush=True)


if __name__ == "__main__":
    main()
