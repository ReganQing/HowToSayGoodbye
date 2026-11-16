# -*- coding: utf-8 -*-
"""生成 shot20「妈，你晚上吃什么」的 H3 Ref2VA 工作流。

与 shot19 的差别：本镜只有许宁一人、两张参考图（面容 + E10 厨房），
所以回到 shot13 原始的 2-ref_image 结构：删掉第三张 LoadImage 节点与
ref_image_3，工作流 16 节点。其余采样参数、风格段逐字沿用。

Run: py -3.12 tools/make_h3_workflow_shot20.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot19.json")
OUT = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot20.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> In a modest Chinese apartment kitchen in soft late "
    "afternoon light, a small folding dining table with one wooden chair, a sink and counter, "
    "shelves with bowls, a window with a pale curtain, and a gas stove with a lidded soup pot, "
    "the table and the chair and the stove and the window arranged as in the reference "
    "<Picture 2>. One person only. A Chinese woman in her late fifties with the same face "
    "exactly matching the reference portrait <Picture 1>, short dark hair with silver streaks, "
    "wearing a plain dove-grey knit cardigan. At the start of the shot she is sitting alone "
    "beside the small table, having just ended a phone call, the telephone resting on the table "
    "beside her hand; on the stove a covered soup pot is simmering, its lid lifting and settling "
    "very slightly with a thin thread of steam, and she has been quiet for a long moment. "
    "Over the course of the shot, in one continuous slow gentle sequence: she slowly rises from "
    "the chair and walks the short distance to the stove with unhurried steps, reaches out one "
    "hand and gently turns the stove knob down so the flame grows smaller and the lid gradually "
    "settles and the steam thins; then she turns back, walks to the table, picks up the telephone "
    "and dials the number again, and lifts it slowly to her ear; she speaks one quiet line as if "
    "asking her mother what she will have for dinner, with a very small sad and tender smile. "
    "By the end of the shot she is standing beside the table holding the telephone to her ear, "
    "the covered pot still on the stove with only a faint wisp of steam, and the chair, the table, "
    "the sink, the shelves and the window are unchanged in the same positions. "
    "Throughout the shot the telephone never disappears, never floats away and never changes into "
    "another object; the pot and its lid stay on the stove all the time and only the amount of "
    "steam changes. There is no flashback, no memory image, no hard cut, no cross-space transition "
    "and no other time or place shown at any point. Both of her feet stay on the ground, her rising "
    "and walking are gradual and continuous with no sudden movement, no abrupt pose changes, no "
    "teleporting and no hard cuts, no second person appears. Her face is clear and detailed and "
    "remains stable, exactly matching <Picture 1>; it does not change or age. Soft even indoor "
    "afternoon light through the window, cool blue-grey shade and a pale warm patch of sunlight "
    "on the wall, no harsh spotlight, no lens flare. " + STYLE
)


def main():
    wf = json.load(io.open(SRC, encoding="utf-8"))
    assert len(wf) == 17
    assert "18" in wf and wf["18"]["class_type"] == "LoadImage"

    # 回到 2-ref_image 结构
    del wf["18"]
    ri = wf["7"]["inputs"]["ref_images"]
    assert "ref_image_3" in ri
    del ri["ref_image_3"]
    assert set(ri) == {"ref_image_1", "ref_image_2"}

    wf["6"]["inputs"]["file"] = "previs_shot20.mp4"
    wf["16"]["inputs"]["image"] = "SHOT20_C06b_face.png"
    wf["17"]["inputs"]["image"] = "SHOT20_E10_kitchen.png"
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111425
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot20"

    # 逐字段校验：除上述 6 处，其余与 shot19 完全一致
    base = json.load(io.open(SRC, encoding="utf-8"))
    expected_diff = {"7", "9", "15", "6", "16", "17"}
    for nid in set(base) & set(wf):
        if nid in expected_diff:
            continue
        assert base[nid] == wf[nid], f"非预期差异 node {nid}"
    assert len(wf) == 16
    assert STYLE in wf["7"]["inputs"]["prompt"]
    for s in ("turns the stove knob down", "dials the number again",
              "lifts it slowly to her ear", "the pot and its lid stay on the stove",
              "no flashback", "no hard cut", "no second person"):
        assert s in PROMPT, f"缺失关键短语: {s}"

    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)
    print("saved", os.path.relpath(OUT, ROOT),
          "nodes", len(wf), "prompt", len(PROMPT), "seed", wf["9"]["inputs"]["noise_seed"])
    print("ref_images", wf["7"]["inputs"]["ref_images"])


if __name__ == "__main__":
    main()
