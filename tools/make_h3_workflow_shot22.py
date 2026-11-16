# -*- coding: utf-8 -*-
"""以 shot21 工作流为底生成 shot22「阳台择豆角」的 MiniMax H3 Ref2VA 工作流。

双人镜头 + 一张场景图 = 3 张 ref_images，17 节点，与 shot15/17/18/19/21 同构：
  <Video 1>  previs_shot22.mp4             （只给运动）
  <Picture 1> SHOT22_C06b_face.png         （许宁·中老年，锁脸）
  <Picture 2> SHOT22_C11_face.png          （妈妈·老年，锁脸）
  <Picture 3> SHOT22_E11_balcony.png       （E11 阳台，锁物件布局）

剧本六 L339-351 / 方案 §3 §4，P0。核心叙事是「妈妈择到一半睡着了，手里还捏着
一截没掐断的豆角；许宁没有拿走，坐在旁边把剩下的慢慢择完；阳光一点点移过膝盖」。

这里的核心道具是「状态保持」而非「位移」：那截豆角从 f001 到 f192 都必须挂在
妈妈手骨骼上、位置不动，且许宁的手不能进入妈妈手部区域（台账 risk_note ②）。
唯一状态变化（妈妈头垂下睡着）前置到 f001–f024（§5.21）。许宁「择完」的物理链
（篮里 → 手 → 掐断 → 膝前小盆）与连续移动的阳光光斑由白模预演给出（§5.19）。

风格段从 shot13 起逐字复制，绝不改写（§5.2）。春日斜光写进 prompt，
参考图只锁布局（§5.8）。

⚠️ 本脚本只做纯文件操作；真正提交前须校验 4 路输入 MD5 与队列空闲。

Run: py -3.12 tools/make_h3_workflow_shot22.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot21.json")
STYLE_SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot19.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot22.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> <Picture 3> On a narrow Chinese apartment balcony "
    "in warm gentle spring afternoon sunlight, with a metal security grille and a glimpse "
    "of neighbouring rooftops and green trees on the left, a bamboo pole spanning overhead, "
    "a windowsill on the right with a potted plant, a folded cloth and a white enamel basin, "
    "two small wooden stools side by side, and a woven basket of fresh green long beans, all "
    "arranged as in the reference <Picture 3>. Two people only, sitting side by side on the "
    "two small wooden stools. A Chinese woman in her late fifties with the same face exactly "
    "matching the reference portrait <Picture 1>, short dark hair with silver streaks, wearing "
    "a plain dove-grey knit cardigan. An elderly Chinese woman aged eighty with the same face "
    "exactly matching the reference portrait <Picture 2>, short silver-grey hair, thin "
    "wire-framed glasses, wearing a dark navy knit cardigan. At the very start of the shot the "
    "elderly woman is already holding one single unbroken green long bean clearly visible in "
    "her hand, large and brightly coloured and clearly readable in the first frames, and the "
    "younger woman is holding another green long bean above the basket. In one continuous slow "
    "gentle sequence: during the first second the elderly woman's head slowly droops forward "
    "and her eyes close as she falls asleep, while her hand and the single green long bean in "
    "it stay perfectly still; the younger woman notices her, does not take the bean from her "
    "hand, and keeps her own hands away from the elderly woman's hand for the whole shot; then "
    "the younger woman quietly and slowly continues snapping the ends off the remaining long "
    "beans one by one, taking each bean from the woven basket, lifting it into both hands, "
    "snapping it and placing it into a small pale enamel bowl resting beside the stools, so "
    "that the pile of prepared beans in the bowl grows gradually and continuously. A soft "
    "warm patch of slanting spring sunlight travels slowly and continuously across the floor "
    "and across both pairs of knees from left to right throughout the shot, with no jump and "
    "no step. By the end of the shot the woven basket is nearly empty, the small enamel bowl "
    "holds the prepared beans, the elderly woman is still asleep with her head lowered and "
    "the same single unbroken green long bean still held in her hand, and the younger woman "
    "sits beside her looking at her quietly; at the very last moment the elderly woman slowly "
    "lifts her head and wakes, and the younger woman gently moves the basket aside. "
    "Throughout the shot that one green long bean in the elderly woman's hand never falls, "
    "never is taken away by anyone, never disappears, never changes into another object and "
    "never moves away from her hand; it is the only object that must remain exactly where it "
    "is, and no other hand ever touches it. The basket, the bowl and every other bean never "
    "disappear or float away, and every bean taken from the basket is clearly seen moving from "
    "the basket to her hands and then into the bowl. There is no flashback, no memory image, "
    "no hard cut, no cross-space transition and no other time or place shown at any point. "
    "Both people remain seated on their stools with their feet on the ground, all movements "
    "are gradual and continuous with no sudden movement, no abrupt pose changes, no "
    "teleporting and no hard cuts, no third person appears. Both faces are clear and detailed "
    "and remain stable, the younger woman's face exactly matching <Picture 1> and the elderly "
    "woman's face exactly matching <Picture 2>; neither face changes, ages, or swaps with the "
    "other. Warm gentle slanting spring afternoon sunlight from the left, cool blue-grey shade "
    "on the walls, a soft slowly moving pale golden patch of light across their knees, no "
    "harsh spotlight, no lens flare. "
    + STYLE
)


def main():
    wf = json.load(io.open(SRC, encoding="utf-8"))
    base19 = json.load(io.open(STYLE_SRC, encoding="utf-8"))["7"]["inputs"]["prompt"]
    base21 = wf["7"]["inputs"]["prompt"]
    assert STYLE in base19, "风格段与 shot19 原文不一致"
    assert STYLE in base21, "风格段与 shot21 原文不一致"
    assert len(wf) == 17, f"底稿节点数异常 {len(wf)}"

    wf["6"]["inputs"]["file"] = "previs_shot22.mp4"
    wf["16"]["inputs"]["image"] = "SHOT22_C06b_face.png"
    wf["17"]["inputs"]["image"] = "SHOT22_C11_face.png"
    wf["18"]["inputs"]["image"] = "SHOT22_E11_balcony.png"
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111427
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot22"

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
    for s in ("already holding one single unbroken green long bean",
              "never is taken away by anyone", "keeps her own hands away",
              "grows gradually and continuously", "travels slowly and continuously",
              "no third person", "no hard cut", "still held in her hand"):
        assert s in PROMPT, f"缺失关键短语: {s}"

    with io.open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)
    print("saved", os.path.relpath(DST, ROOT))
    print("nodes", len(wf), "prompt", len(PROMPT), "seed", wf["9"]["inputs"]["noise_seed"])
    print("STYLE 逐字一致:", STYLE in base19 and STYLE in base21 and STYLE in PROMPT)
    print("ref_images", wf["7"]["inputs"]["ref_images"])


if __name__ == "__main__":
    main()
