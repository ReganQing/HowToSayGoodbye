# -*- coding: utf-8 -*-
"""shot16 v02：重写发带段，修复 v01「旧发带没放进小包」的阻断问题。

以 v01 工作流 h3_r2v_workflow_shot16.json 为底，只改 3 处：
  node 7  prompt            —— 发带动作链重写（见下）
  node 9  noise_seed        —— 2026111417
  node 15 filename_prefix   —— h3_r2v_shot16b

v01 判退依据：progress/06_质检返修/shot16_v01_发带未入包_弃用/v01_verdict.json
  f149-168 许宁把红发带拿在手里，f175-192 又放回桌面，f192 发带仍摊在桌布上，
  小包全程空着。违反剧本 L283、方案 §4 与 HANDOFF §5.1 变化三态。

v02 三处强化：
  1. 发带动作提前到动作段中段单独成句，写成 拿起→折叠→移到包口→放入→松手→抽回空手
     的连续物理链，动词不省略、不只用一次 "puts it into"。
  2. By the end 段三重声明：桌面没有发带 / 发带完全在包内不可见 / 她的双手是空的。
  3. 硬约束补 never set back down on the table / must not reappear；
     并显式说明全片唯一允许从画面消失的物体就是这条发带，原因是被收进包里，
     以对抗 H3 的「物体恒存」先验。

风格段从 shot14/shot15/v01 原文逐字复制，绝不改写（HANDOFF §5.2）。
预演沿用 assets/previs/previs_shot16.mp4，不重渲（v01 已证明 prompt 文本足以驱动动作）。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot16.json")   # v01，判退但保留
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot16b.json")  # v02

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
    "slightly, the young woman looks at her, an old faded red hair ribbon lies flat on the "
    "tablecloth in front of her, and a small plain handbag with an open mouth rests empty on "
    "the seat of the chair beside her. Over the course of the shot, in one continuous slow "
    "gentle sequence: the young woman gradually leans toward her mother, turns her head and "
    "slowly raises one hand to the tilted brooch, and steadily straightens the brooch until "
    "it sits level, while the mother lowers her eyes to look at it; the young woman then lets "
    "her hand move down and gently takes and holds her mother's hand, giving a very small "
    "quiet nod, and the mother slowly raises her head until the two of them are looking at "
    "each other. Then, well before the shot ends, the young woman turns back toward the "
    "tabletop and performs one clear uninterrupted action with the old red hair ribbon: she "
    "reaches down and picks the ribbon up off the tablecloth with one hand, folds it neatly "
    "between both hands so it becomes visibly shorter, carries the folded ribbon in her hand "
    "across to the open mouth of the small handbag on the chair seat, lowers her hand and "
    "slips the folded ribbon down into the bag, opens her fingers to release it inside the "
    "bag, and slowly draws her hand back out of the bag empty. The ribbon goes from lying "
    "flat on the tablecloth, to being folded and held in her hand, to being completely hidden "
    "inside the handbag; from the moment it enters the bag it is never seen again. By the end "
    "of the shot the small handbag stays where it is beside the chair back within easy reach "
    "of her hand and now holds the ribbon, the ribbon is completely out of sight inside the "
    "bag, there is no ribbon anywhere on the tablecloth and the tabletop in front of her is "
    "bare, her two hands are empty and relaxed at her sides, the brooch is straight, and the "
    "three of them stand quietly together in the soft daylight. Throughout the shot the table, "
    "the tablecloth, the chairs, the window, the curtain, the bowls, the thermos, the "
    "windowsill lamp and the handbag stay in the same positions and keep the same appearance; "
    "the brooch only rotates gradually from tilted to straight, the ribbon never floats "
    "unsupported in the air and is always either lying on the tablecloth or held in her hand "
    "until it is put inside the bag, the ribbon is never set back down on the table and never "
    "placed back on the tablecloth after being picked up, the ribbon must not reappear after "
    "it is put into the bag, the only object allowed to disappear from view in this shot is "
    "the ribbon because it is tucked inside the handbag, the bag does not move, all three "
    "people's feet stay on the floor, their hands and arms move gradually with no sudden "
    "movement, no abrupt pose changes and no hard cuts, every transition is gradual and "
    "continuous, no fourth person appears. All three faces are clear and detailed and remain "
    "stable, the young woman's face exactly matching <Picture 1>, the young man's face exactly "
    "matching <Picture 2> with his round black-framed glasses present at all times, the "
    "mother's face exactly matching <Picture 3>; none of the three faces changes, ages, or "
    "swaps with another. Daytime lighting: soft cool daylight through the window, steady "
    "gentle warm light over the table, no harsh spotlight, no lens flare. "
    + STYLE
)


def main():
    with open(SRC, encoding="utf-8") as f:
        base = json.load(f)
    assert STYLE in base["7"]["inputs"]["prompt"], "v01 风格段异常，需核对"
    assert len(base) == 18, f"v01 节点数异常 {len(base)}"

    wf = json.loads(json.dumps(base))            # 深拷贝，绝不改动 v01 文件
    old_prompt = wf["7"]["inputs"]["prompt"]
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111417
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot16b"

    # 逐字段比对：除 3 个预期字段外必须零差异
    skip = {("7", "prompt"), ("9", "noise_seed"), ("15", "filename_prefix")}
    diff = []
    for k in base:
        assert base[k]["class_type"] == wf[k]["class_type"], k
        for field, val in base[k]["inputs"].items():
            if (k, field) in skip:
                continue
            if val != wf[k]["inputs"].get(field, "<缺失>"):
                diff.append((k, field))
    assert not diff, f"非预期差异: {diff}"
    assert len(wf) == 18
    assert set(wf["7"]["inputs"]["ref_images"]) == {
        "ref_image_1", "ref_image_2", "ref_image_3", "ref_image_4"}
    assert wf["6"]["inputs"]["file"] == "previs_shot16.mp4"
    assert STYLE in PROMPT
    assert PROMPT.startswith("<Video 1> <Picture 1> <Picture 2> <Picture 3> <Picture 4>")
    # 发带修复的关键短语必须在场
    for s in ("never set back down on the table", "must not reappear",
              "no ribbon anywhere on the tablecloth", "draws her hand back out of the bag empty",
              "completely hidden inside the handbag"):
        assert s in PROMPT, f"缺失关键短语: {s}"
    # v01 里权重不足的旧写法不再作为唯一表述
    assert "puts it into a small plain handbag" not in PROMPT

    with open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=1)
    print(f"写出 {DST}")
    print(f"节点 {len(wf)} 个，非预期差异 {len(diff)}，prompt v01 {len(old_prompt)} → v02 {len(PROMPT)} 字符")
    print("风格段逐字一致:", STYLE in old_prompt and STYLE in PROMPT)
    print("seed:", wf["9"]["inputs"]["noise_seed"], "prefix:", wf["15"]["inputs"]["filename_prefix"])
    print("五路标注:", PROMPT[:62])


if __name__ == "__main__":
    main()
