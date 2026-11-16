# -*- coding: utf-8 -*-
"""以 shot15 工作流为底生成 shot19「报纸后面」的 MiniMax H3 Ref2VA 工作流。

shot19 两位角色 + 一张场景图 = 3 张 ref_images，17 节点，与 shot15/17/18 同构：
  <Video 1>  previs_shot19.mp4            （只给运动）
  <Picture 1> SHOT19_C06b_face.png        （许宁·中老年居家）
  <Picture 2> SHOT19_C18_face.png         （周远·老年，需先跑 tools/gen_ref_c18_head.py 重绘）
  <Picture 3> SHOT19_E09_table.png        （E09 折叠餐桌，锁布局）

剧本六 L315-319 / 方案 §4。核心动作「周远在报纸后半天没应 → 许宁走过去把报纸
往下按一按 → 他抬头看她，她忘了刚才要说什么」。按 HANDOFF §5 第 19 条，
报纸的完整物理链（举着挡脸 → 被按下 → 露出脸、始终在手里）必须在白模预演里
用道具逐帧驱动给出，prompt 补不出位移；这里只负责写清三态与终态。

风格段从 shot13/14/15/16/17/18 原文逐字复制，绝不改写（HANDOFF §5.2）。

⚠️ 生成工作流是纯文件操作；真正提交前必须确认 4 路输入 MD5 与队列空闲。
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot15.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot19.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> <Picture 3> In a modest Chinese apartment in soft "
    "daylight, a small folding dining table with two wooden chairs, a window with a pale "
    "curtain, a thermos, a bowl and a small covered pot on a low sideboard, the table and the "
    "chairs and the window arranged as in the reference <Picture 3>. Two people only. A Chinese "
    "woman in her late fifties with the same face exactly matching the reference portrait "
    "<Picture 1>, short dark hair with silver streaks, wearing a plain dove-grey knit cardigan. "
    "An elderly Chinese man aged seventy-two with the same face exactly matching the reference "
    "portrait <Picture 2>, neat short silver-grey hair, slim round black-framed glasses, wearing "
    "a soft beige knit sweater over a light blue collared shirt. At the start of the shot the "
    "old man is sitting upright in one of the wooden chairs holding an open folded newspaper "
    "up in front of his face so that the newspaper hides most of his face, and he has been "
    "quiet for a long moment; the woman is standing a short distance away beside the table, "
    "looking toward him, the newspaper is fully open and clearly visible in both of his hands. "
    "Over the course of the shot, in one continuous slow gentle sequence: the woman walks the "
    "short distance over to him with unhurried steps and stops beside his chair, slowly reaches "
    "out one hand and gently presses the top edge of the newspaper downward, the newspaper "
    "gradually lowering in his hands until his face is revealed above it; he slowly lifts his "
    "head and looks up at her over the lowered newspaper, and she pauses with a very small quiet "
    "amused smile as if she has forgotten what she was going to say. By the end of the shot the "
    "newspaper is still open and still held in both of his hands, now resting low enough that "
    "his whole face is visible, the woman is standing beside his chair with her hand drawn back "
    "to her own side, both of them are quiet together in the soft daylight, and the table, the "
    "two chairs, the window, the thermos, the bowl and the covered pot are unchanged in the same "
    "positions. Throughout the shot the newspaper never disappears, never floats away, never "
    "changes shape, never turns into another object and is never placed on the table; it stays "
    "in his two hands from the first frame to the last and only its height changes. There is no "
    "flashback, no memory image, no hard cut, no cross-space transition and no other time or "
    "place shown at any point. Both of their feet stay on the ground, the old man stays seated "
    "in the same chair and the woman's approach is gradual and continuous with no sudden "
    "movement, no abrupt pose changes, no teleporting and no hard cuts, no third person appears. "
    "Both faces are clear and detailed and remain stable once revealed, the woman's face exactly "
    "matching <Picture 1> and the old man's face exactly matching <Picture 2>; neither face "
    "changes, ages, or swaps with the other. Soft even indoor daylight through the window, "
    "cool blue-grey shade and a pale warm patch of sunlight on the wall, no harsh spotlight, "
    "no lens flare. "
    + STYLE
)


def main():
    wf = json.load(io.open(SRC, encoding="utf-8"))
    base_prompt = wf["7"]["inputs"]["prompt"]
    assert STYLE in base_prompt, "风格段与 shot15 原文不一致，需核对"
    assert len(wf) == 17, f"底稿节点数异常 {len(wf)}"

    wf["6"]["inputs"]["file"] = "previs_shot19.mp4"
    wf["16"]["inputs"]["image"] = "SHOT19_C06b_face.png"
    wf["17"]["inputs"]["image"] = "SHOT19_C18_face.png"
    wf["18"]["inputs"]["image"] = "SHOT19_E09_table.png"
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111424
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot19"

    a = json.load(io.open(SRC, encoding="utf-8"))
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
    for s in ("presses the top edge of the newspaper downward", "never placed on the table",
              "no flashback", "no hard cut", "no third person", "still held in both of his hands"):
        assert s in PROMPT, f"缺失关键短语: {s}"

    with io.open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=1)
    print(f"写出 {DST}")
    print(f"节点 {len(wf)} 个，非预期差异 {len(diff)}，prompt {len(PROMPT)} 字符")
    print("风格段逐字一致:", STYLE in base_prompt and STYLE in PROMPT)
    print("seed:", wf["9"]["inputs"]["noise_seed"], "prefix:", wf["15"]["inputs"]["filename_prefix"])
    print("前置条件: SHOT19_C18_face.png 需由 tools/gen_ref_c18_head.py 目检通过后裁出")


if __name__ == "__main__":
    main()
