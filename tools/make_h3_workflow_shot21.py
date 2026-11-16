# -*- coding: utf-8 -*-
"""以 shot19 工作流为底生成 shot21「一袋橘子」的 MiniMax H3 Ref2VA 工作流。

双人镜头 + 一张场景图 = 3 张 ref_images，17 节点，与 shot15/17/18/19 同构：
  <Video 1>  previs_shot21.mp4            （只给运动）
  <Picture 1> SHOT21_C06b_face.png        （许宁·中老年居家）
  <Picture 2> SHOT21_C11_face.png         （妈妈·老年）
  <Picture 3> SHOT21_E10_doorway.png      （E10 出租屋，锁物件布局）

剧本六 L327-337 / 方案 §4。核心动作「提一袋橘子上来递过去 → 妈妈分一半给她 →
临出门时妈妈说『晚上回来吃饭』」。按 HANDOFF §5 第 19 条，橘子袋的完整物理链
（许宁手 → 妈妈手 → 橘子从袋里逐个到桌面）必须在白模预演里用道具逐帧驱动给出，
prompt 补不出位移；这里只负责写清三态、连续动词链与终态（§5.18）。

风格段从 shot13 起逐字复制，绝不改写（HANDOFF §5.2）。
光照按剧本 L329-331 写清晨，不写夜晚；参考图只锁布局（§5.8）。

⚠️ 生成工作流是纯文件操作；真正提交前必须校验 4 路输入 MD5 与队列空闲。

Run: py -3.12 tools/make_h3_workflow_shot21.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot19.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot21.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> <Picture 3> At the open doorway of a modest Chinese "
    "apartment in soft early morning light, an open entrance door with a plain frame, a narrow "
    "console table just inside the door, and beyond it the same small kitchen with a sink and "
    "counter, a window with a pale curtain and shelves with bowls, the door and the table and "
    "the kitchen beyond arranged as in the reference <Picture 3>. Two people only. A Chinese "
    "woman in her late fifties with the same face exactly matching the reference portrait "
    "<Picture 1>, short dark hair with silver streaks, wearing a plain dove-grey knit cardigan. "
    "An elderly Chinese woman aged eighty with the same face exactly matching the reference "
    "portrait <Picture 2>, short silver-grey hair, thin wire-framed glasses, wearing a dark navy "
    "knit cardigan. At the start of the shot the younger woman is standing in the open doorway "
    "holding a clearly visible paper bag full of bright orange tangerines in one hand, having "
    "just come back upstairs, and the elderly woman is standing just inside the door facing her; "
    "the bag of tangerines is large, brightly coloured and clearly visible in the very first "
    "frames. Over the course of the shot, in one continuous slow gentle sequence: the younger "
    "woman holds the bag out and offers it, the elderly woman reaches out with both hands and "
    "takes the bag from her so that the bag passes visibly from one pair of hands into the "
    "other; the elderly woman then takes one tangerine out of the bag, peels it slowly with her "
    "fingers and breaks it in half, and holds one half out to the younger woman, who takes it "
    "and eats it quietly while standing in the doorway; then the elderly woman takes the "
    "remaining tangerines out of the bag one by one and sets them in a neat row on the narrow "
    "console table, choosing the softest one and placing it a little apart from the others. "
    "By the end of the shot the younger woman is turning to leave through the still open door, "
    "the elderly woman is standing behind her beside the console table with the tangerines laid "
    "out in a row and the emptied paper bag beside them, and the elderly woman quietly says that "
    "she should come back for dinner tonight; the younger woman gives a small quiet nod. "
    "Throughout the shot the paper bag and every tangerine never disappear, never float away "
    "and never change into other objects; the bag stays in someone's hands or rests on the "
    "console table, and every tangerine that is taken out of the bag is clearly seen moving "
    "from the bag to her hand and then to the table. There is no flashback, no memory image, "
    "no hard cut, no cross-space transition and no other time or place shown at any point. "
    "Both of their feet stay on the ground, the door stays open in the same position, all "
    "movements are gradual and continuous with no sudden movement, no abrupt pose changes, no "
    "teleporting and no hard cuts, no third person appears. Both faces are clear and detailed "
    "and remain stable, the younger woman's face exactly matching <Picture 1> and the elderly "
    "woman's face exactly matching <Picture 2>; neither face changes, ages, or swaps with the "
    "other. Soft even early morning light from the window, cool blue-grey shade and a pale warm "
    "patch of light near the doorway, no harsh spotlight, no lens flare. "
    + STYLE
)


def main():
    wf = json.load(io.open(SRC, encoding="utf-8"))
    base_prompt = wf["7"]["inputs"]["prompt"]
    assert STYLE in base_prompt, "风格段与 shot19 原文不一致，需核对"
    assert len(wf) == 17, f"底稿节点数异常 {len(wf)}"

    wf["6"]["inputs"]["file"] = "previs_shot21.mp4"
    wf["16"]["inputs"]["image"] = "SHOT21_C06b_face.png"
    wf["17"]["inputs"]["image"] = "SHOT21_C11_face.png"
    wf["18"]["inputs"]["image"] = "SHOT21_E10_doorway.png"
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111426
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot21"

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
    for s in ("passes visibly from one pair of hands into the other",
              "breaks it in half", "one by one and sets them in a neat row",
              "never disappear", "no flashback", "no hard cut",
              "no third person", "come back for dinner tonight"):
        assert s in PROMPT, f"缺失关键短语: {s}"

    with io.open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)
    print("saved", os.path.relpath(DST, ROOT))
    print("nodes", len(wf), "prompt", len(PROMPT), "seed", wf["9"]["inputs"]["noise_seed"])
    print("风格段逐字一致:", STYLE in base_prompt and STYLE in PROMPT)
    print("ref_images", wf["7"]["inputs"]["ref_images"])


if __name__ == "__main__":
    main()
