# -*- coding: utf-8 -*-
"""以 shot15 工作流为底生成 shot17「我自己来」的 MiniMax H3 Ref2VA 工作流。

shot17 两位角色 + 一张场景图 = 3 张 ref_images，17 节点，与 shot15 同构：
  <Video 1>  previs_shot17b.mp4       （v6 过审预演，只给运动；v4 预演已判退）
  <Picture 1> SHOT17_C06_face.png      （许宁·成年，C06）
  <Picture 2> SHOT17_C11_face.png      （妈妈·老年，C11）
  <Picture 3> SHOT17_E09_table.png     （E09 折叠餐桌，锁布局）

剧本六 L285-303 / 方案 §4。核心叙事动作是「妈妈把手机往回一收、许宁收回手重说一遍」。
沿用 shot16 v02 的返修经验：核心动作提前到中段单独成句、写全连续物理链、
By the end 三重声明终态、硬约束写死 never handed over / never placed on the table，
不把关键动作埋在长句末尾。

2026-11-14 换参考视频：previs_shot17.mp4（v4）已判退——手机前 137 帧平躺在桌面
中央，与 prompt 的 never placed on the table 冲突。改用 previs_shot17b.mp4（v6，
手机逐帧贴妈妈左手骨骼、从 f001 起就在手里）。**prompt / seed / prefix 逐字不改**，
只换 LoadVideo，构成只换参考视频的单变量验证（HANDOFF §5 第 19 条）。

风格段从 shot14/shot15/shot16 原文逐字复制，绝不改写（HANDOFF §5.2）。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot15.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot17.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> <Picture 3> In daytime, interior of a small modest "
    "north-facing rented room in a northern Chinese city in the 2010s, a plain folding wooden "
    "dining table covered with a light cream tablecloth, wooden chairs, a single window on the "
    "back wall with soft daylight and a simple curtain, a small lamp on the windowsill, a pair "
    "of bowls and a thermos on the table, and a plain interior door at the far edge of the room "
    "slightly ajar suggesting that someone is about to leave; the layout of table, chairs, "
    "window, curtain and sideboard matching the reference <Picture 3>. Two people only. A "
    "Chinese woman in her late twenties with the same face exactly matching the reference "
    "portrait <Picture 1>, neat dark shoulder-length hair, wearing a light cream short jacket "
    "over a plain blouse and dark indigo trousers. An elderly Chinese woman with the same face "
    "exactly matching the reference portrait <Picture 2>, short dark hair with visible grey "
    "strands, fine wrinkles, wearing a sober dark jacket and dark trousers, no apron. At the "
    "start of the shot the two of them are already sitting side by side at the table, the "
    "young woman on the left of the frame and the elderly mother on the right, both turned "
    "slightly toward each other; the mother holds a small smartphone in her own hand with its "
    "screen tilted so both of them can see it, a neatly folded pile of the baby's small clothes "
    "rests on the tablecloth, and the young woman is leaning a little toward the screen showing "
    "her how to find the train information. Over the course of the shot, in one continuous slow "
    "gentle sequence: the young woman points gently at the screen once to demonstrate, and the "
    "mother lowers her eyes and taps the screen with one finger; the mother then taps a second "
    "time but still in the wrong place, and the young woman leans a little further forward and "
    "lowers her head slightly. Then, well before the shot ends, the single most important "
    "action happens in one clear uninterrupted chain: the young woman slowly raises one hand "
    "and reaches toward the phone as if to take over and do it for her; the mother calmly draws "
    "the phone back a short distance toward her own body, keeping it firmly in her own hand the "
    "whole time, and lifts her head a little to look at her daughter; the young woman's "
    "outstretched hand stops in mid air, then slowly draws back to her own side, and she turns "
    "her head back to her mother and begins to explain it again with a very small quiet nod. "
    "By the end of the shot the smartphone is still in the mother's hand, still lit, held "
    "slightly closer to her than at the start, the young woman's two hands are back at her own "
    "sides and her posture is upright again, the mother is looking at her daughter, and the two "
    "of them sit quietly side by side in the soft daylight. Throughout the shot the smartphone "
    "stays in the mother's hand from the first frame to the last and is never placed on the "
    "table, never set down anywhere, never handed over to the young woman, never taken by the "
    "young woman and never disappears; the phone only moves gradually a short distance toward "
    "the mother, the table, the tablecloth, the chairs, the window, the curtain, the bowls, the "
    "thermos, the windowsill lamp and the folded baby clothes stay in the same positions and "
    "keep the same appearance, both people remain seated with their feet on the floor, their "
    "heads and hands and arms move gradually with no sudden movement, no abrupt pose changes "
    "and no hard cuts, every transition is gradual and continuous, no third person appears. "
    "Both faces are clear and detailed and remain stable, the young woman's face exactly "
    "matching <Picture 1>, the mother's face exactly matching <Picture 2>; neither face "
    "changes, ages, or swaps with the other. Daytime lighting: soft cool daylight through the "
    "window, steady gentle warm light over the table, no harsh spotlight, no lens flare. "
    + STYLE
)


def main():
    with open(SRC, encoding="utf-8") as f:
        wf = json.load(f)
    base_prompt = wf["7"]["inputs"]["prompt"]
    assert STYLE in base_prompt, "风格段与 shot15 原文不一致，需核对"
    assert len(wf) == 17, f"底稿节点数异常 {len(wf)}"

    wf["6"]["inputs"]["file"] = "previs_shot17b.mp4"
    wf["16"]["inputs"]["image"] = "SHOT17_C06_face.png"      # ref_image_1 许宁
    wf["17"]["inputs"]["image"] = "SHOT17_C11_face.png"      # ref_image_2 妈妈
    wf["18"]["inputs"]["image"] = "SHOT17_E09_table.png"     # ref_image_3 场景
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111419
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot17"

    with open(SRC, encoding="utf-8") as f:
        a = json.load(f)
    skip = {("6", "file"), ("16", "image"), ("17", "image"), ("18", "image"),
            ("7", "prompt"), ("9", "noise_seed"), ("15", "filename_prefix")}
    diff = []
    for k in a:
        assert a[k]["class_type"] == wf[k]["class_type"], k
        for field, val in a[k]["inputs"].items():
            if (k, field) in skip:
                continue
            if val != wf[k]["inputs"].get(field, "<缺失>"):
                diff.append((k, field))
    assert not diff, f"非预期差异: {diff}"
    assert len(wf) == 17
    assert set(wf["7"]["inputs"]["ref_images"]) == {
        "ref_image_1", "ref_image_2", "ref_image_3"}
    assert STYLE in PROMPT
    assert PROMPT.startswith("<Video 1> <Picture 1> <Picture 2> <Picture 3>")
    for s in ("never placed on the table", "never handed over to the young woman",
              "still in the mother's hand", "slowly draws back to her own side",
              "draws the phone back a short distance"):
        assert s in PROMPT, f"缺失关键短语: {s}"

    with open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=1)
    print(f"写出 {DST}")
    print(f"节点 {len(wf)} 个，非预期差异 {len(diff)}，prompt {len(PROMPT)} 字符")
    print("风格段逐字一致:", STYLE in base_prompt and STYLE in PROMPT)
    print("seed:", wf["9"]["inputs"]["noise_seed"], "prefix:", wf["15"]["inputs"]["filename_prefix"])
    print("四路标注:", PROMPT[:50])


if __name__ == "__main__":
    main()
