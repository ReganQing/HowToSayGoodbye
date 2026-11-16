# -*- coding: utf-8 -*-
"""
《我们总要学会告别，并在告别中成长》
白模预演 × 成品镜头 —— 27 镜逐帧同步 1:1 左右分屏对比片

依据的过程文件（全部可追溯）：
  tools/build_progress.py            -> finals / shots_prev（镜头定稿索引）
  tmp_qc/roughcut_v07_timeline.json  -> 27 镜标题、七段落、in/out 时间线
  progress/04_白模预演/shot16b_预演审查/qc_report.json  -> shot16 预演 v03 过审
  progress/04_白模预演/shot17b_预演审查/qc_report.json  -> shot17 预演 v6 过审
  progress/04_白模预演/shot17_v4_手机落桌_判退/v4_verdict.json -> shot17 v4 判退
  progress/README.md                 -> 04/05 目录用途与命名规则

输出（output/previs_vs_final/）：
  白模预演×成品镜头_逐镜对比_1920x1080.mp4   主成片（标准 16:9，带专业标注）
  白模预演×成品镜头_纯净原生_2560x720.mp4     纯净版（原生像素，无标注）
  镜头匹配表.md / 镜头匹配表.json             27 镜一一匹配表
  剪映导入时间线.json                         供剪映按表复现
  build_compare.py                            本脚本副本
"""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(".")
OUT = ROOT / "output" / "previs_vs_final"
OV = OUT / "ov"
QC = OUT / "qc"
PREV_DIR = ROOT / "assets" / "previs"
FIN_DIR = ROOT / "assets" / "h3_video"

FPS = 24
SHOT_SEC = 8.0
N_SHOTS = 27
TOTAL_SEC = 216.0
TOTAL_FRAMES = 5184

FONT_BOLD = "<LOCAL_PATH>"
FONT_REG = "<LOCAL_PATH>"
FONT_MONO = "<LOCAL_PATH>"

# 配色（深色专业风）
BG = (14, 17, 22)
WHITE = (242, 245, 248, 255)
GREY = (138, 151, 166, 255)
DIM = (96, 108, 122, 255)
LINE = (42, 52, 64, 255)
TEAL = (92, 200, 178, 255)      # 白模预演侧
GOLD = (233, 185, 107, 255)     # 成品镜头侧
CARD = (22, 27, 34, 235)
TAGBG = (10, 14, 18, 200)


def run(cmd, *, check=True):
    print("  $ " + " ".join(str(c) for c in cmd[:8]) + (" ..." if len(cmd) > 8 else ""), flush=True)
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        print(r.stdout[-3000:])
        print(r.stderr[-3000:])
        raise RuntimeError(f"命令失败 exit={r.returncode}")
    return r


def ffprobe(path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
             "-show_entries", "format=duration", "-of", "json", path], check=False)
    d = json.loads(r.stdout)
    s = d["streams"][0]
    return dict(w=s["width"], h=s["height"], fps=s["r_frame_rate"],
                frames=int(s.get("nb_frames", 0)), duration=float(d["format"]["duration"]))


def fmt_tc(sec):
    m = int(sec) // 60
    s = sec - m * 60
    return f"{m:02d}:{s:06.3f}"


def load_mapping():
    """从过程文件读出 27 镜匹配关系，不靠文件名猜。"""
    src = (ROOT / "tools" / "build_progress.py").read_text(encoding="utf-8")

    # finals 是纯字面量字典，可安全 literal_eval
    tree = ast.parse(src)
    finals = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "finals" for t in node.targets):
            finals = ast.literal_eval(node.value)
    assert finals and len(finals) == 27, "finals 解析失败"

    # shots_prev 混有 dict(...) 调用，用正则只取 mp4 / title
    prev_mp4 = dict(re.findall(r"'shot(\d{2})':\s*dict\([^)]*?mp4='([^']+)'", src))
    prev_title = dict(re.findall(r"'shot(\d{2})':\s*dict\([^)]*?title='([^']+)'", src))

    tl = json.loads((ROOT / "tmp_qc" / "roughcut_v07_timeline.json").read_text(encoding="utf-8"))
    seg_of, title_of, inout_of, source_of = {}, {}, {}, {}
    for seg in tl["segments"]:
        for sid in seg["shots"]:
            seg_of[sid] = seg["name"]
    for sh in tl["shots"]:
        title_of[sh["shot"]] = sh["title"]
        inout_of[sh["shot"]] = (sh["in_s"], sh["out_s"])
        source_of[sh["shot"]] = sh["source"].split("/")[-1]

    # 过程文件判定出的 4 处特殊处理
    override = {
        "shot01": ("previs_shot01_v2.mp4", "build_progress.py:62 shots_prev 指定 v2；v1 为早期版本"),
        "shot09": ("previs_shot09.mp4", "build_progress.py:89 注释「shot09 无白模帧目录，assets/previs 仅有 previs_shot09.mp4，非遗漏」；视频实存，补入第 27 镜"),
        "shot16": ("previs_shot16b.mp4", "shot16b_预演审查/qc_report.json: v03 verdict=pass；previs_shot16.mp4 对应 v01/v02 因「旧发带未离桌」判退"),
        "shot17": ("previs_shot17b.mp4", "shot17b_预演审查/qc_report.json: v6 最终过审版；v4_verdict.json 判退 previs_shot17.mp4（手机平躺桌面）"),
    }

    rows = []
    for i in range(1, 28):
        sid = f"shot{i:02d}"
        n = f"{i:02d}"
        if sid in override:
            prev_file, basis = override[sid]
        else:
            prev_file, basis = prev_mp4[n], "build_progress.py shots_prev 索引（与 04_白模预演/shotNN 归档一致）"
        fin_file = finals[sid]
        assert source_of[sid] == fin_file, f"{sid} 成品定稿不一致: {fin_file} vs {source_of[sid]}"
        p, f = PREV_DIR / prev_file, FIN_DIR / fin_file
        assert p.exists(), f"缺白模: {p}"
        assert f.exists(), f"缺成品: {f}"
        rows.append(dict(
            shot=sid, index=i, title=title_of[sid], segment=seg_of[sid],
            in_s=inout_of[sid][0], out_s=inout_of[sid][1],
            previs=f"assets/previs/{prev_file}", final=f"assets/h3_video/{fin_file}",
            basis=basis, previs_from_index=prev_mp4.get(n),
        ))

    # shot09 是过程文件里唯一没有 Blender 白模的镜头：
    # make_previs09.py 证明 previs_shot09.mp4 由 P02 老照片做 Ken Burns 推近，属运动参考。
    # 不删镜（保 27 镜顺序与 216s），但必须在画面与匹配表里显式区分，绝不冒充白模。
    for r in rows:
        r["kind"] = "白模预演"
        r["display_title"] = r["title"]
        r["source_note"] = ""
    s9 = rows[8]
    assert s9["shot"] == "shot09"
    s9["kind"] = "运动参考"
    s9["display_title"] = "P02 老照片的缓慢推近"
    s9["source_note"] = ("tools/make_previs09.py:2 docstring 原文；"
                         "tmp_qc/roughcut_v07_timeline.json 该镜 title 为「—（镜头索引未收录，不臆造）」，"
                         "本片不臆造镜头标题，仅采用源脚本文本作画面标注")
    s9["basis"] = ("assets/previs/previs_shot09.mp4 实存，但 tools/make_previs09.py 证明其由 P02 老照片"
                   "Ken Burns 推近生成，非 Blender 白模；build_progress.py:89 记录本镜无白模帧目录。"
                   "故以「运动参考」入列并显式标注，保 27 镜顺序与 216s 不变")
    return rows, tl


def write_tables(rows, tl):
    (OUT / "镜头匹配表.json").write_text(
        json.dumps(dict(spec=dict(resolution_source="1280x720", fps=24, frames_per_shot=192,
                                  seconds_per_shot=8.0, total_seconds=216.0, total_frames=5184, audio=False),
                        sources=["tools/build_progress.py", "tmp_qc/roughcut_v07_timeline.json",
                                 "progress/04_白模预演/*_预演审查/qc_report.json", "progress/README.md"],
                        shots=rows), ensure_ascii=False, indent=2), encoding="utf-8")

    seg_order = [s["name"] for s in tl["segments"]]
    lines = [
        "# 白模预演 × 成品镜头 · 27 镜逐帧同步匹配表",
        "",
        "**结论**：27 镜全部一一匹配，左右同为 `1280×720 / 24fps / 192 帧 / 8.0s / 无音轨`，"
        "同顺序、同起止、同时长、同节奏，逐帧零误差；合计 **216.0s / 5184 帧**。"
        "其中 26 镜为 Blender 白模预演，shot09 为运动参考（唯一缺口，已在片中显式标注）。",
        "",
        "| 镜号 | 段落 | 镜头标题（过程文件定名） | 左侧类型 | 时间区间 | 左：预演 / 参考 | 右：成品镜头 | 匹配依据 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['index']:02d} | {seg_order.index(r['segment']) + 1}·{r['segment']} | {r['title']} "
            f"| {r['kind']} | {fmt_tc(r['in_s'])}–{fmt_tc(r['out_s'])} | `{Path(r['previs']).name}` "
            f"| `{Path(r['final']).name}` | {r['basis']} |")
    lines += [
        "",
        "## 来源与特殊处理（可追溯）",
        "",
        "| 项 | 出处 | 说明 |",
        "|---|---|---|",
        "| 成品定稿文件名 | `tools/build_progress.py:91–110` `finals` | 27 镜逐条指定；shot01–04 为返修定稿（v2 / bright），不可按 `shotNN_h3.mp4` 猜 |",
        "| 白模预演索引 | `tools/build_progress.py:61–90` `shots_prev` | 26 条；shot09 无帧目录但视频实存 |",
        "| 镜头标题 / 七段落 / in-out | `tmp_qc/roughcut_v07_timeline.json` | 与 `tools/roughcut_v07.py:36–44` `SEGMENTS` 一致 |",
        "| shot01 预演 | `build_progress.py:62` | 用 `previs_shot01_v2.mp4`，非 v1 |",
        "| shot09 补入 | `build_progress.py:89` 注释 + `tools/make_previs09.py` | 「非遗漏，勿强加」指帧目录；视频实存故补齐第 27 镜，但经源脚本核实为老照片运动参考而非白模，详见下节 |",
        "| shot16 预演 | `progress/04_白模预演/shot16b_预演审查/qc_report.json` | v03 `verdict=pass`；`previs_shot16.mp4` 对应 v01/v02，旧发带「从未离桌」导致 H3 生成不出「放进小包」 |",
        "| shot17 预演 | `progress/04_白模预演/shot17b_预演审查/qc_report.json` + `shot17_v4_手机落桌_判退/v4_verdict.json` | v6 过审；v4 手机平躺桌面、与 prompt `never placed on the table` 冲突而判退 |",
        "| 目录口径 | `progress/README.md:12–20` | 04 白模预演 / 05 镜头成片，「与 05 对比，彰显预演对生成质量的约束作用」 |",
        "",
        "## 已知缺口：shot09（唯一的非白模镜，已显式标注）",
        "",
        "- `tools/make_previs09.py:1–3`：`previs_shot09.mp4` 是「P02 老照片的缓慢推近（Ken Burns）」运动参考，"
        "由一张静态老照片裁切放大生成，**不是 Blender 白模预演**；`assets/previs/` 下也没有 `frames09/`。",
        "- `tmp_qc/roughcut_v07_timeline.json` 该镜 title 记为「—（镜头索引未收录，不臆造）」；"
        "`build_progress.py:89` 注释亦说明「shot09 无白模帧目录，非遗漏」。",
        "- 处理：**保留第 9 镜**（不打乱 27 镜顺序、不缩短 216s），左侧仍放该运动参考、右侧放成品，"
        "但画面左角标改为「运动参考 MOTION REF」、顶部注明「本镜无 Blender 白模预演」，"
        "并在匹配表中标明类型，避免误导。这也是过程文件「不臆造」原则的延续。",
        "",
        "## 白模预演的三项价值（本片要突出的重点）",
        "",
        "1. **镜头规划**：预演先行锁定机位、构图、走位与道具三态（shot27 三代红发带），成品只在同一构图里补材质与光。",
        "2. **节奏把控**：27 镜统一 8.0s / 192 帧，左右同起同止，动作节拍可直接逐帧比对。",
        "3. **制作指导**：预演判退直接驱动成片返修 —— shot16 补齐「旧带离桌→入包」物理链、shot17 改「从桌上拿起」拓扑后，H3 一次提交过审。",
        "",
    ]
    (OUT / "镜头匹配表.md").write_text("\n".join(lines), encoding="utf-8")

    ed = dict(
        version="白模预演×成品镜头 逐镜 1:1 对比",
        project=str(ROOT), total_duration_s=216.0, fps=24,
        layout="左 白模预演 / 右 成品镜头，各占一半，硬切，无转场无配乐",
        outputs=dict(main="白模预演×成品镜头_逐镜对比_1920x1080.mp4",
                     clean="白模预演×成品镜头_纯净原生_2560x720.mp4"),
        editor_note="剪映复现：新建 1920x1080/24fps 工程，导入两条 216s 轨；左轨缩放至 960x540 置于 x=0,y=270，右轨 960x540 置于 x=960,y=270；27 段按 in_s/out_s 硬切；文字按 overlay_XX.png 排版",
        shots=[dict(shot=r["shot"], title=r["title"], display_title=r["display_title"],
                    kind=r["kind"], segment=r["segment"], source_note=r["source_note"],
                    in_s=r["in_s"], out_s=r["out_s"], left=r["previs"], right=r["final"],
                    basis=r["basis"], overlay=f"ov/overlay_{r['index']:02d}.png") for r in rows],
    )
    (OUT / "剪映导入时间线.json").write_text(json.dumps(ed, ensure_ascii=False, indent=2), encoding="utf-8")


def font(path, size):
    return ImageFont.truetype(path, size)


def right(draw, x_right, y, text, fnt, fill):
    draw.text((x_right - draw.textlength(text, font=fnt), y), text, font=fnt, fill=fill)


def make_overlay(row, seg_no):
    """生成单镜 1920x1080 RGBA 标注层（透明区不遮挡画面）。"""
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = lambda s, b=False: font(FONT_BOLD if b else FONT_REG, s)
    mono = lambda s: font(FONT_MONO if Path(FONT_MONO).exists() else FONT_REG, s)

    # ---- 顶部信息带 0–270 ----
    d.text((72, 40), "白模预演 × 成品镜头", font=f(46, True), fill=WHITE)
    d.text((72, 108), "逐镜 1:1 同步对比  ·  同顺序 / 同起止 / 同时长 / 同节奏", font=f(23), fill=GREY)

    seg = f"第 {seg_no} 段 · {row['segment']}"
    w = d.textlength(seg, font=f(22))
    d.rounded_rectangle([72, 162, 72 + int(w) + 40, 204], radius=8, fill=CARD)
    d.text((92, 168), seg, font=f(22), fill=TEAL)
    d.text((72, 214), f"SHOT {row['index']:02d}   {row['display_title']}", font=f(28, True), fill=WHITE)
    if row["kind"] != "白模预演":
        d.text((400, 168), "注：本镜无 Blender 白模预演，左侧为运动参考", font=f(20), fill=GOLD)

    right(d, 1848, 42, f"{row['index']:02d} / 27", f(62, True), TEAL)
    right(d, 1848, 128, f"{fmt_tc(row['in_s'])} → {fmt_tc(row['out_s'])}", mono(23), WHITE)
    right(d, 1848, 172, "8.0s  ·  192 帧  ·  24fps", f(20), GREY)
    right(d, 1848, 216, "逐帧对齐  FRAME-LOCK", f(20), DIM)
    d.rectangle([72, 256, 1848, 258], fill=LINE)

    # ---- 画面区 270–810：透明，仅叠角标 ----
    d.rectangle([0, 270, 1920, 272], fill=LINE)
    d.rectangle([0, 808, 1920, 810], fill=LINE)
    d.rectangle([958, 270, 962, 810], fill=(210, 224, 235, 210))

    is_previs = row["kind"] == "白模预演"
    tag_l, col_l = ("白模预演   PREVIS", TEAL) if is_previs else ("运动参考   MOTION REF", GOLD)
    sub_l = ("Blender 白模 · 机位 / 走位 / 动作 / 节奏基准" if is_previs
             else "P02 老照片 Ken Burns 推近 · 本镜无 Blender 白模")
    d.rounded_rectangle([24, 286, 372, 342], radius=8, fill=TAGBG)
    d.text((44, 293), tag_l, font=f(24, True), fill=col_l)
    d.rounded_rectangle([984, 286, 1332, 342], radius=8, fill=TAGBG)
    d.text((1004, 293), "成品镜头   FINAL", font=f(24, True), fill=GOLD)

    d.rounded_rectangle([24, 748, 590, 790], radius=6, fill=TAGBG)
    d.text((40, 756), sub_l, font=f(19), fill=WHITE)
    d.rounded_rectangle([984, 748, 1534, 790], radius=6, fill=TAGBG)
    d.text((1000, 756), "MiniMax H3 · 按预演约束逐帧生成", font=f(19), fill=WHITE)

    # ---- 底部信息带 810–1080 ----
    cards = [
        ("镜头规划", "机位 · 构图 · 走位先锁定", TEAL),
        ("节奏把控", "27 镜 × 8.0s · 192 帧严格同步", WHITE),
        ("制作指导", "预演判退 → 成片返修 → 一次过审", GOLD),
    ]
    for k, (t1, t2, col) in enumerate(cards):
        x = 72 + k * 596
        d.rounded_rectangle([x, 838, x + 560, 920], radius=10, fill=CARD, outline=LINE, width=1)
        d.text((x + 22, 848), t1, font=f(26, True), fill=col)
        d.text((x + 22, 884), t2, font=f(19), fill=GREY)

    d.text((72, 942), "白模预演先行确定镜头语言，成品沿同一时间轴生成 —— 每一帧可对照、可回溯、可复现",
           font=f(23), fill=WHITE)

    d.rounded_rectangle([72, 1006, 1848, 1016], radius=5, fill=LINE)
    d.rounded_rectangle([72, 1006, 72 + int(1776 * row["index"] / 27), 1016], radius=5, fill=TEAL)
    d.text((72, 1028), f"{fmt_tc(row['in_s'])} / 03:36.000", font=mono(19), fill=GREY)
    right(d, 1848, 1028, "27 镜 · 216 秒 · 24fps · 源 1280×720", f(19), DIM)

    im.save(OV / f"overlay_{row['index']:02d}.png")


def prepare(rows, tl):
    for d in (OUT, OV, QC):
        d.mkdir(parents=True, exist_ok=True)
    write_tables(rows, tl)
    seg_order = [s["name"] for s in tl["segments"]]
    for r in rows:
        make_overlay(r, seg_order.index(r["segment"]) + 1)
    print(f"  标注层 {len(list(OV.glob('overlay_*.png')))} 张")

    # 关键：concat demuxer 用 -c copy 会留下不连续时间戳，hstack 的 shortest 会提前收尾
    # （本项目经验库已记录同类坑）。这里直接重编码成干净 CFR 轨，左右逐帧号严格对齐。
    for key, name in (("previs", "previs_track.mp4"), ("final", "final_track.mp4")):
        lst = OUT / f"{key}_concat.txt"
        lst.write_text("".join(f"file '{(ROOT / r[key]).as_posix()}'\n" for r in rows), encoding="utf-8")
        dst = OUT / name
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", lst, "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "16",
             "-r", str(FPS), "-fps_mode", "cfr", "-pix_fmt", "yuv420p",
             "-movflags", "+faststart", dst])
        info = ffprobe(dst)
        print(f"  {name}: {info}")
        assert info["frames"] == TOTAL_FRAMES and abs(info["duration"] - TOTAL_SEC) < 0.02, "轨长异常"
    # 字体测试图（QC 用）
    shutil.copy2(OV / "overlay_01.png", QC / "overlay_sample.png")


def render():
    common = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats"]
    enc = ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
           "-r", str(FPS), "-fps_mode", "cfr", "-frames:v", str(TOTAL_FRAMES),
           "-an", "-movflags", "+faststart"]

    # ---------- 主成片 1920x1080 ----------
    fc_main = (
        "[0:v]settb=AVTB,setpts=PTS-STARTPTS,scale=960:540:flags=lanczos,setsar=1[L];"
        "[1:v]settb=AVTB,setpts=PTS-STARTPTS,scale=960:540:flags=lanczos,setsar=1[R];"
        "[L][R]hstack=inputs=2:shortest=1[HS];"
        "color=c=0x0E1116:s=1920x1080:r=24:d=216[BG];"
        "[BG][HS]overlay=x=0:y=270:shortest=1[BASE];"
        "[2:v]fps=24,format=rgba,tpad=stop_mode=clone:stop_duration=8,"
        "trim=duration=216,setpts=PTS-STARTPTS[OV];"
        "[BASE][OV]overlay=0:0:format=auto,format=yuv420p[OUT]"
    )
    main = OUT / "白模预演×成品镜头_逐镜对比_1920x1080.mp4"
    print("  渲染主成片 1920x1080 ...", flush=True)
    run(common + ["-t", str(TOTAL_SEC), "-i", OUT / "previs_track.mp4",
                  "-t", str(TOTAL_SEC), "-i", OUT / "final_track.mp4",
                  "-framerate", "0.125", "-t", str(TOTAL_SEC), "-i", OV / "overlay_%02d.png",
                  "-filter_complex", fc_main, "-map", "[OUT]"] + enc + [main])

    # ---------- 纯净原生版 2560x720 ----------
    fc_clean = (
        "[0:v]settb=AVTB,setpts=PTS-STARTPTS,setsar=1[L];"
        "[1:v]settb=AVTB,setpts=PTS-STARTPTS,setsar=1[R];"
        "[L][R]hstack=inputs=2:shortest=1,"
        "drawbox=x=1278:y=0:w=4:h=720:color=0x2A3440:t=fill,format=yuv420p[OUT]"
    )
    clean = OUT / "白模预演×成品镜头_纯净原生_2560x720.mp4"
    print("  渲染纯净原生版 2560x720 ...", flush=True)
    run(common + ["-i", OUT / "previs_track.mp4", "-i", OUT / "final_track.mp4",
                  "-filter_complex", fc_clean, "-map", "[OUT]"] + enc + [clean])
    return main, clean


def qc(rows, main, clean):
    report = {}
    for p in (main, clean):
        info = ffprobe(p)
        r = run(["ffmpeg", "-v", "error", "-i", p, "-f", "null", "-"], check=False)
        errs = [x for x in (r.stderr or "").splitlines() if x.strip()]
        report[p.name] = dict(spec=info, decode_errors=errs[:10], decode_error_count=len(errs))
        print(f"  {p.name}: {info} 解码错误 {len(errs)}")
        assert info["frames"] == TOTAL_FRAMES, f"{p.name} 帧数不符"
        assert abs(info["duration"] - TOTAL_SEC) < 0.05, f"{p.name} 时长不符"
        assert not errs, f"{p.name} 有解码错误"

    # 每镜中点抽帧（左右同帧同步目检）
    for r in rows:
        t = r["in_s"] + 4.0
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", str(t),
             "-i", main, "-frames:v", "1", "-update", "1",
             QC / f"shot{r['index']:02d}_mid.png"])
    print(f"  抽帧 {len(rows)} 张 -> qc/shotNN_mid.png")

    # 首/中/尾三张拼联系表
    ims = [Image.open(QC / f"shot{i:02d}_mid.png").convert("RGB").resize((640, 360))
           for i in (1, 9, 18, 27)]
    sheet = Image.new("RGB", (1280, 720), BG[:3])
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % 2) * 640, (k // 2) * 360))
    sheet.save(QC / "对比片_四镜联系表.jpg", quality=90)
    (OUT / "qc_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    rows, tl = load_mapping()
    print(f"[1/4] 匹配表：{len(rows)} 镜，来源 finals / shots_prev / timeline / 审查判定", flush=True)
    prepare(rows, tl)
    print("[2/4] 两条 216s 同步轨已生成", flush=True)
    main_f, clean_f = render()
    print("[3/4] 两版成片已渲染", flush=True)
    qc(rows, main_f, clean_f)
    print("[4/4] QC 通过", flush=True)
    shutil.copy2(__file__, OUT / "build_compare.py")
    print("\n交付目录:", OUT)
    for p in sorted(OUT.iterdir()):
        if p.is_file():
            print(f"  {p.name}  {p.stat().st_size / 1048576:.2f} MB")


if __name__ == "__main__":
    main()
