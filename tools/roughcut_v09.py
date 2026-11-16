# -*- coding: utf-8 -*-
"""粗剪 v0.9 = v0.8 + 用户拍板「片尾留白放宽到 3.0s」（总长 216.0 → 217.5s）。

观聆复审必改 2 的落地：1.5s 末帧定格呼吸偏短 → 补到 3.0s 空场，
定格后不硬切黑（视频自然结束）。27 镜素材总长仍 216 秒，变化只在片尾空场。

复用 v0.8 的分步叠化流程，只覆盖 TAIL / EXPECT_SEC / 输出路径。

Run: py -3.12 tools/roughcut_v09.py
输出:
  assets/h3_video/roughcut_v09_no_bgm.mp4   (217.5s)
  tmp_qc/roughcut_v09_timeline.json
  tmp_qc/roughcut_v09_seams.json
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roughcut_v08 as v8  # noqa: E402
import roughcut_v07 as v7  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, ".workbuddy", "memory", "2026-11-15.md")

v8.TAIL = 3.0
v8.EXPECT_SEC = 217.5
v8.OUT = os.path.join(ROOT, "assets", "h3_video", "roughcut_v09_no_bgm.mp4")
v8.TIMELINE = os.path.join(ROOT, "tmp_qc", "roughcut_v09_timeline.json")
v8.SEAMS = os.path.join(ROOT, "tmp_qc", "roughcut_v09_seams.json")


def main():
    v8.main()

    t = json.load(io.open(v8.TIMELINE, encoding="utf-8"))
    t["version"] = "v0.9 用户拍板版 · 无配乐 · 观聆必改 2 已落地"
    t["user_decision"] = {
        "at": "2026-11-15",
        "question": "片尾留白是否放宽 216s 总长（Ron 决策）",
        "chosen": "放宽到 217.5 秒",
        "note": "27 镜素材总长仍 216 秒（Ron 决策不变）；成片粗剪因片尾 3.0s 空场为 217.5 秒。"
                "末帧定格后不硬切黑，视频自然结束。",
    }
    t["tail_hold"] = {
        "start_s": 214.5, "duration_s": 3.0, "method": "tpad 克隆末帧",
        "note": "观聆必改 2 落地：1.5s → 3.0s 空场；定格后不硬切黑",
    }
    t["review"] = {
        "v0.7": "观聆：有条件通过，5 条意见",
        "v0.8": "观聆复审：有条件通过，五条清三；前 32s 硬切认可；压短 shot25、L-cut 不卡通过",
        "v0.9": "唯一卡点「片尾 2–3s 空场需 Ron 拍板放宽 216s」已由用户拍板放行并落地，"
                "观聆三条必改中第 2 条解除；剩余 1/3 属二轮带音轨/调色阶段，不卡粗剪定稿",
        "confirmed": ["3 处 0.5s 叠化（40/88/112s）", "176s / 184s 谷底硬切留满静",
                      "前 32s 序章记忆碎片式硬切保留", "片尾 3.0s 末帧定格、不硬切黑"],
        "must_fix_round2": [
            "必改1 二轮压 shot01/03 高光，并复测 8/16/24s 接缝落差 <10",
            "必改3 shot26→27 L-cut 声桥、shot25 前 2s 节奏，二轮上音轨后复核，不破 8s 规格",
        ],
        "seam_qc_correction": "前一轮以「每镜首帧亮度」误判 shot26→27 落差 110；"
                              "按评审要求尾帧→首帧口径实测仅 0.2，不存在闪黑",
    }
    t["remaining_for_round2"] = [
        "shot01/03 调色压高光，复测 8/16/24s 接缝落差 <10（观聆必改 1）",
        "shot26→27 L-cut 声桥：音乐于 shot26 尾 0.5–1s 先入、画面硬切，二轮上音轨后验收（观聆必改 3）",
        "shot25 前 2s 节奏二轮带音轨复核，不破 8s 规格",
        "配乐 70BPM 下 8s = 9.33 拍非整小节，末镜 3/4 需按 217.5s 成片重对齐卡点（交绿野）",
        "跨镜道具 / 四代角色一致性、叠化重影逐镜检查",
    ]
    t.pop("pending_decision", None)
    t["editor_note"] = (
        "剪映导入按 8s 网格排 27 段；3 处叠化前后镜各让出 0.5s；"
        "片尾 214.5–217.5s 为 3.0s 末帧定格，不是新镜头，且之后不加黑帧"
    )
    with io.open(v8.TIMELINE, "w", encoding="utf-8") as f:
        json.dump(t, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(
            "\n## 全片粗剪 v0.7 → v0.9（无配乐初版，寻帧 / 观聆评审）\n\n"
            "- v0.7：27 镜成片按 `finals` 映射顺序纯硬切，216.0s / 5184 帧 / 0 解码错误 / 无音轨。"
            "脚本 `tools/roughcut_v07.py`，时间线 `tmp_qc/roughcut_v07_timeline.json`。\n"
            "- 观聆首轮「有条件通过」5 条意见；v0.8 落地 3 处 0.5s 叠化（40/88/112s）、"
            "176/184s 谷底保持硬切、片尾 1.5s 末帧定格，总长仍 216.0s。"
            "脚本 `tools/roughcut_v08.py`（分步 xfade 每步校验，避开链式 filter 截断坑）。\n"
            "- **QC 口径纠错**：判断接缝跳变必须用「前镜尾帧→次镜首帧」，不能用每镜首帧互比。"
            "实测 208s 落差仅 0.2（shot26 镜内已从 173 渐暗到 61），此前误判的「落差 110」不成立；"
            "真正落差在前 32 秒 8/16/24s = 40.4/37.9/35.8，属序章记忆碎片式硬切，观聆认可保留。\n"
            "- **用户拍板（2026-11-15）**：片尾留白放宽到 3.0s，成片总长 **217.5 秒**；"
            "**27 镜素材总长仍 216 秒，Ron 决策不变**，变化只在片尾空场。v0.9 脚本 "
            "`tools/roughcut_v09.py`，成片 `assets/h3_video/roughcut_v09_no_bgm.mp4`，"
            "定格后不硬切黑。\n"
            "- 二轮待办：压 shot01/03 高光并复测接缝落差 <10；接 70BPM 配乐后做 shot26→27 的 "
            "L-cut 声桥；按 217.5s 重对齐末镜 3/4 卡点（交绿野）。\n"
        )
    print("LOG appended:", os.path.relpath(LOG, ROOT), flush=True)
    print("ROUGHCUT_V09_DONE", flush=True)


if __name__ == "__main__":
    main()
