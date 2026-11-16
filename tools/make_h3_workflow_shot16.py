# -*- coding: utf-8 -*-
"""以 shot15 工作流为底生成 shot16 的 MiniMax H3 Ref2VA 工作流。

shot16 有三位角色，需要 4 张 ref_images：在 shot15 的 17 节点上新增
LoadImage 节点 19 与 ref_image_4，其余节点逐字段保持不变。
风格段从 shot14/shot15 原文逐字复制，绝不改写（HANDOFF §5.2）。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot15.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot16.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> <Picture 3> <Picture 4> In daytime, interior of a "
    "small modest north-facing rented room in a northern Chinese city in the 2010s, a very "
    "simple home wedding celebration with no banquet hall and no party decorations, a plain "
    "folding wooden dining table covered with a light cream tablecloth, three wooden chairs, "
    "a single window on the back wall with soft daylight and a simple curtain, a small lamp "
    "sitting on the windowsill, a pair of bowls and a thermos on the table, a low wooden "
    "sideboard against the back right wall, the layout of table, chairs, window, curtain and "
    "sideboard matching the reference <Picture 4>. Three people only. A Chinese woman in her "
    "late twenties with the same face exactly matching the reference portrait <Picture 1>, "
    "neat dark shoulder-length hair, wearing a light cream short jacket over a plain blouse "
    "and dark indigo trousers. A young Chinese man in his mid-twenties with the same face "
    "exactly matching the reference portrait <Picture 2>, short black hair, distinctive slim "
    "round black-framed glasses, a cream V-neck sweater over a pale blue collared shirt, dark "
    "grey trousers, white sneakers. A middle-aged Chinese woman with the same face exactly "
    "matching the reference portrait <Picture 3>, short dark hair with a few grey strands, "
    "wearing a dark maroon formal jacket with one small brooch pinned on the left side of her "
    "chest, no apron, dark trousers. At the start of the shot the three of them are already "
    "standing around the table: the mother on the left of the frame, the young woman in the "
    "middle, the young man further back on the right; the mother's small brooch is visibly "
    "tilted at an angle, she has stopped halfway through a sentence and lowers her head "
    "slightly, the young woman looks at her, and an old faded red hair ribbon lies flat on the "
    "tablecloth. Over the course of the shot, in one continuous slow gentle sequence: the young "
    "woman gradually leans toward her mother, turns her head and slowly raises one hand to the "
    "tilted brooch, and steadily straightens the brooch until it sits level, while the mother "
    "lowers her eyes to look at it; the young woman then lets her hand move down and gently "
    "takes and holds her mother's hand, giving a very small quiet nod, and the mother slowly "
    "raises her head until the two of them are looking at each other; afterward the young woman "
    "straightens up and turns back toward the tabletop, picks up the old faded red hair ribbon, "
    "its colour washed out and its edges slightly frayed, folds it neatly in both hands so it "
    "becomes shorter, and puts it into a small plain handbag that rests on the seat of the chair "
    "beside her, the ribbon disappearing into the bag only at that moment. By the end of the shot "
    "the small handbag stays where it is beside the chair back within easy reach of her hand, "
    "the ribbon is no longer on the table, the brooch is straight, and the three of them stand "
    "quietly together in the soft daylight. Throughout the shot the table, the tablecloth, the "
    "chairs, the window, the curtain, the bowls, the thermos, the windowsill lamp and the handbag "
    "stay in the same positions and keep the same appearance; the brooch only rotates gradually "
    "from tilted to straight, the ribbon never floats in the air and stays on or just above the "
    "tablecloth until it is folded away, the bag does not move, all three people's feet stay on "
    "the floor, their hands and arms move gradually with no sudden movement, no abrupt pose "
    "changes and no hard cuts, every transition is gradual and continuous, no fourth person "
    "appears. All three faces are clear and detailed and remain stable, the young woman's face "
    "exactly matching <Picture 1>, the young man's face exactly matching <Picture 2> with his "
    "round black-framed glasses present at all times, the mother's face exactly matching "
    "<Picture 3>; none of the three faces changes, ages, or swaps with another. Daytime lighting: "
    "soft cool daylight through the window, steady gentle warm light over the table, no harsh "
    "spotlight, no lens flare. "
    + STYLE
)


def main():
    with open(SRC, encoding="utf-8") as f:
        wf = json.load(f)
    base_prompt = wf["7"]["inputs"]["prompt"]
    assert STYLE in base_prompt, "风格段与 shot15 原文不一致，需核对"
    assert len(wf) == 17, f"底稿节点数异常 {len(wf)}"

    wf["6"]["inputs"]["file"] = "previs_shot16.mp4"
    wf["16"]["inputs"]["image"] = "SHOT16_C06_face.png"      # ref_image_1 许宁
    wf["17"]["inputs"]["image"] = "SHOT16_C15_face.png"      # ref_image_2 周远
    wf["18"]["inputs"]["image"] = "SHOT16_C10_face.png"      # ref_image_3 妈妈
    wf["19"] = {"class_type": "LoadImage",                   # ref_image_4 场景
                "inputs": {"image": "SHOT16_E09_table.png"}}
    wf["7"]["inputs"]["ref_images"]["ref_image_4"] = ["19", 0]
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111416
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot16"

    # 与底稿逐字段比对：除预期字段外必须零差异；节点 19 是新增，不在底稿里
    with open(SRC, encoding="utf-8") as f:
        a = json.load(f)
    skip = {("6", "file"), ("16", "image"), ("17", "image"), ("18", "image"),
            ("7", "prompt"), ("7", "ref_images"), ("9", "noise_seed"),
            ("15", "filename_prefix")}
    diff = []
    for k in a:
        assert a[k]["class_type"] == wf[k]["class_type"], k
        for field, val in a[k]["inputs"].items():
            if (k, field) in skip:
                continue
            if val != wf[k]["inputs"].get(field, "<缺失>"):
                diff.append((k, field))
    assert not diff, f"非预期差异: {diff}"
    assert len(wf) == 18
    assert set(wf["7"]["inputs"]["ref_images"]) == {
        "ref_image_1", "ref_image_2", "ref_image_3", "ref_image_4"}
    assert STYLE in PROMPT
    assert PROMPT.startswith("<Video 1> <Picture 1> <Picture 2> <Picture 3> <Picture 4>")

    with open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=1)
    print(f"写出 {DST}")
    print(f"节点 {len(wf)} 个（新增 LoadImage 19），非预期差异 {len(diff)}，prompt {len(PROMPT)} 字符")
    print("风格段逐字一致:", STYLE in base_prompt and STYLE in PROMPT)
    print("五路标注:", PROMPT[:62])


if __name__ == "__main__":
    main()
