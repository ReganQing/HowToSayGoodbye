# -*- coding: utf-8 -*-
"""以 shot14 工作流为底生成 shot15 的 MiniMax H3 Ref2VA 工作流。

只改 6 处：LoadVideo、三个 LoadImage、seed、filename_prefix，以及节点 7 的 prompt。
其余节点逐字段保持不变，风格段从 shot14 原文逐字复制。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot14.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot15.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> <Picture 3> At night, interior of a small modest "
    "north-facing rented room in a northern Chinese city in the 2010s, a plain folding wooden "
    "dining table with two wooden chairs, a single window on the back wall with dark blue night "
    "outside and a simple curtain, a small lamp sitting on the windowsill, a thermos and a sheet "
    "of paper covered with handwritten numbers and a pen on the tabletop, a shallow drawer under "
    "the table, a folded damp-proof mat in the corner, warm lamplight with soft shadows and a "
    "faint cool bounce from the dark window, the layout of table, chairs, window and windowsill "
    "matching the reference <Picture 3>. A Chinese woman in her late twenties with the same face "
    "exactly matching the reference portrait <Picture 1>, neat dark shoulder-length hair, wearing "
    "a light cream short jacket over a plain blouse, dark indigo trousers and flat black shoes. "
    "A young Chinese man in his mid-twenties with the same face exactly matching the reference "
    "portrait <Picture 2>, short black hair, distinctive slim round black-framed glasses, a cream "
    "V-neck sweater over a pale blue collared shirt, dark grey trousers, white sneakers. "
    "At the start of the shot the two of them are already seated facing each other across the small "
    "table, the woman on the left and the man on the right, both leaning slightly forward with "
    "their heads lowered over the sheet of paper, the woman holding a pen and making small writing "
    "and counting movements with it, the man pointing at the numbers with one hand. "
    "Over the course of the shot, in one continuous slow gentle sequence: her pen strokes gradually "
    "slow and stop, and she lays the pen down flat on the paper, then slowly raises her head and "
    "looks across at him; she speaks one quiet sentence while the man keeps studying the paper for "
    "a moment, then his own hand gradually stops and he lifts his head until the two of them are "
    "looking at each other; she then gathers the sheet of paper, slides it toward the near edge of "
    "the table, pulls the shallow drawer under the table open a little, puts the paper inside and "
    "closes the drawer again, the paper disappearing into the drawer only at that moment; toward the "
    "end the small lamp on the windowsill gradually glows warmer and brighter, until a soft round "
    "halo of warm light rests on the wall beside the window, and the two of them sit still and quiet "
    "in the lamplight. By the end of the shot the table holds only the thermos and the pen lying "
    "flat, the sheet of paper is inside the closed drawer, the small lamp is lit, both people remain "
    "seated facing each other across the table. "
    "Throughout the shot the table, both chairs, the window, the curtain, the thermos, the pen and "
    "the windowsill lamp stay in the same positions and keep the same appearance; the paper and pen "
    "never float in the air, the drawer opens and closes smoothly, both people's feet stay on the "
    "floor and their seated height matches the chair seats, their hands and arms move gradually with "
    "no sudden movement, no abrupt pose changes and no hard cuts, every transition is gradual and "
    "continuous, no other person appears. Both faces are clear and detailed, the woman's face exactly "
    "matching <Picture 1>, the man's face exactly matching <Picture 2> with his round black-framed "
    "glasses present at all times, neither face changes or swaps with the other. "
    "Night lighting: dark blue evening outside the window, steady warm light over the table, and the "
    "small windowsill lamp gradually brightening at the end to cast one soft circle of warm light on "
    "the wall, no harsh spotlight, no lens flare. "
    + STYLE
)


def main():
    with open(SRC, encoding="utf-8") as f:
        wf = json.load(f)
    base_prompt = wf["7"]["inputs"]["prompt"]
    assert STYLE in base_prompt, "风格段与 shot14 原文不一致，需核对"

    wf["6"]["inputs"]["file"] = "previs_shot15.mp4"
    wf["16"]["inputs"]["image"] = "SHOT15_C06_face.png"      # ref_image_1 许宁
    wf["17"]["inputs"]["image"] = "SHOT15_C15_face.png"      # ref_image_2 周远
    wf["18"]["inputs"]["image"] = "SHOT15_E09_table.png"     # ref_image_3 场景
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111415
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot15"

    # 与底稿逐字段比对，除预期 6 处外必须零差异
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
    assert STYLE in PROMPT
    assert len(wf) == len(a) == 17

    with open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=1)
    print(f"写出 {DST}")
    print(f"节点 {len(wf)} 个，非预期差异 {len(diff)}，prompt {len(PROMPT)} 字符")
    print("风格段逐字一致:", STYLE in base_prompt and STYLE in PROMPT)
    print("四路标注:", PROMPT[:52])


if __name__ == "__main__":
    main()
