# -*- coding: utf-8 -*-
"""以 shot22 工作流为底生成 shot23「地址纸与盒子」的 MiniMax H3 Ref2VA 工作流。

两人镜头 + 一张场景图 = 3 张 ref_images，17 节点，与 shot15/17/18/19/21/22 同构：
  <Video 1>  previs_shot23.mp4            （只给运动）
  <Picture 1> SHOT23_C06b_face.png         （许宁·中老年，锁脸）
  <Picture 2> SHOT23_C18_face.png          （周远·老年，锁脸）
  <Picture 3> SHOT23_E08_desk.png          （E08 朝北小屋书桌，锁物件布局）

剧本六 L353-359 / 方案 §3 §4，P0。核心叙事是「在妈妈抽屉里找到旧作业本、
录取通知书复印件和一张改过两次地址的纸 → 用指腹抹平、折好又展开 → 放进盒子
与姥姥的红发带收在一起 → 合盖坐到天黑 → 周远端饭进来，她慢慢吃几口」。

这里的核心道具是「状态型 + 位移型混合」：地址纸先在桌面被抹平/折/展开（状态），
再必须**完整连续地抬离桌面、横移到盒口、落进盒里**（位移）。shot16 两版判退
的根因就是白模里发带从未离桌、从未到过包口（HANDOFF §5.19 根因更正）；
纸被盒盖遮住是全片唯一允许从视野消失的物体，prompt 里显式豁免（§5.18），
关键变化前置 f001–f024（§5.21）。

天黑光影用真实渐弱光源由白模给出，prompt 只锁「连续无阶跃」；参考图只锁布局
（§5.8）。风格段从 shot13 起逐字复制，绝不改写（§5.2）。

⚠️ 本脚本只做纯文件操作；真正提交前须校验 4 路输入 MD5 与队列空闲。

Run: py -3.12 tools/make_h3_workflow_shot23.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot22.json")
STYLE_SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot19.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot23.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> <Picture 3> In a small north-facing Chinese bedroom "
    "with cool blue-grey walls, a single bed on the left with a folded quilt, a stack of old "
    "books on the floor beside it, a window with a gauzy white curtain, a wooden desk with a "
    "drawer beneath it, a small warm desk lamp, a white mug and a kettle, and one plain wooden "
    "chair, all arranged as in the reference <Picture 3>. Two people only. A Chinese woman in "
    "her late fifties with the same face exactly matching the reference portrait <Picture 1>, "
    "short dark hair with silver streaks, wearing a plain dove-grey knit cardigan, sitting on "
    "the wooden chair at the desk. An elderly Chinese man with the same face exactly matching "
    "the reference portrait <Picture 2>, wavy silver-grey hair, round black-framed glasses, "
    "wearing a beige V-neck sweater over a pale blue collared shirt. At the very start of the "
    "shot, spread out on the desktop in front of her, there is an old school exercise book, "
    "a photocopy of a university admission letter, and one sheet of warm cream paper with a "
    "handwritten address that has been changed twice, the old address not crossed out and the "
    "new address written beside it, the last line shakier and slightly crooked. That address "
    "sheet is large, bright and clearly readable in the very first frames. Beside these papers "
    "an open keepsake box sits on the desktop with a faded old red hair ribbon already lying "
    "inside it, clearly visible. In the first second of the shot, in one continuous slow "
    "gentle sequence, she smooths the address sheet flat with her fingertips, folds it in "
    "half, then unfolds it again, then lifts the whole sheet up off the desktop with both "
    "hands, carries it sideways above the open box, lowers it into the box and lays it down "
    "beside the faded red hair ribbon, and then slowly closes the lid of the box. The sheet of "
    "paper is continuously visible moving from the desktop into her hands, across the air "
    "above the box, and down into the box, with no jump and no cut. That address sheet is the "
    "only object in the whole shot that is allowed to disappear from view, and only because "
    "it has been placed inside the box and the lid has been closed over it; it must never "
    "vanish earlier, never float away, never be teleported and never change into another "
    "object. The old exercise book, the admission letter photocopy, the keepsake box, the "
    "faded red hair ribbon, the desk lamp, the mug and every other object stay where they are "
    "and never disappear or move abruptly. After the lid is closed she stays sitting quietly "
    "at the desk. The pale late afternoon light from the window fades slowly, gradually and "
    "continuously into blue-grey evening dusk, the small warm desk lamp becoming the only "
    "warm light in the room, with no sudden brightness change, no hard-edged light patch and "
    "no step. Near the end of the shot the elderly man comes quietly in from the doorway "
    "carrying a bowl of rice, sets it on the desk beside the closed box, does not urge her, "
    "and she takes the bowl and slowly eats a few mouthfuls. Throughout the shot there is no "
    "flashback, no memory image, no hard cut, no cross-space transition and no other time or "
    "place shown at any point. She remains seated on the chair with her feet on the ground, "
    "all movements are gradual and continuous with no sudden movement, no abrupt pose "
    "changes, no teleporting and no hard cuts, and no third person appears. Both faces are "
    "clear and detailed and remain stable, the woman's face exactly matching <Picture 1> and "
    "the elderly man's face exactly matching <Picture 2>; neither face changes, ages, or "
    "swaps with the other. Cool blue-grey north room light grading gently into evening dusk, "
    "warm cream paper and pale wood tones, a single small warm desk lamp, no harsh spotlight, "
    "no lens flare. "
    + STYLE
)


def main():
    wf = json.load(io.open(SRC, encoding="utf-8"))
    base19 = json.load(io.open(STYLE_SRC, encoding="utf-8"))["7"]["inputs"]["prompt"]
    base22 = wf["7"]["inputs"]["prompt"]
    assert STYLE in base19, "风格段与 shot19 原文不一致"
    assert STYLE in base22, "风格段与 shot22 原文不一致"
    assert len(wf) == 17, f"底稿节点数异常 {len(wf)}"

    wf["6"]["inputs"]["file"] = "previs_shot23.mp4"
    wf["16"]["inputs"]["image"] = "SHOT23_C06b_face.png"
    wf["17"]["inputs"]["image"] = "SHOT23_C18_face.png"
    wf["18"]["inputs"]["image"] = "SHOT23_E08_desk.png"
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111428
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot23"

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
    for s in ("In the first second of the shot",
              "smooths the address sheet flat with her fingertips",
              "folds it in half, then unfolds it again",
              "lifts the whole sheet up off the desktop with both hands",
              "carries it sideways above the open box",
              "lowers it into the box",
              "slowly closes the lid of the box",
              "only object in the whole shot that is allowed to disappear from view",
              "fades slowly, gradually and continuously into blue-grey evening dusk",
              "no hard-edged light patch",
              "no third person", "no hard cut", "comes quietly in from the doorway"):
        assert s in PROMPT, f"缺失关键短语: {s}"

    with io.open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)
    print("saved", os.path.relpath(DST, ROOT))
    print("nodes", len(wf), "prompt", len(PROMPT), "seed", wf["9"]["inputs"]["noise_seed"])
    print("STYLE 逐字一致:", STYLE in base19 and STYLE in base22 and STYLE in PROMPT)
    print("ref_images", wf["7"]["inputs"]["ref_images"])


if __name__ == "__main__":
    main()
