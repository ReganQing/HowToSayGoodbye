# -*- coding: utf-8 -*-
"""以 shot25 的 18 节点工作流为底生成 shot26「跳一点给外婆看」的 H3 Ref2VA 工作流。

4 张 ref_images / 18 节点（H3 `ref_images` AUTOGROW 上限 9 张已确认）：
  <Video 1>    previs_shot26.mp4
  <Picture 1>  SHOT26_C07_face.png   （许宁·老年病房）
  <Picture 2>  SHOT26_C16_face.png   （女儿·成年）
  <Picture 3>  SHOT26_C17_face.png   （小满·双辫）
  <Picture 4>  SHOT26_E02_ward.png   （E02_v02 水彩病房）

剧本七 L391–417 / 方案 §3 §4，P0。核心链：妈妈挪椅腾地 → 小满数拍子跳舞、
转身忘动作停下、从头再来 → 许宁看完 → 碰辫梢交代两条白花红发带 →
掖被角、窗帘鼓起、慢慢睡着。

硬约束：两条带白花的褪色红发带全程恒存（P01 姥姥旧发带，与 shot16 P02、
shot27 P03 三代呼应）；椅子从床边连续挪开后恒存；跳舞链连续无闪切；
剧本 L413 回忆与 L417 走廊推车**不得画成闪回/第二空间**，只用同一病房的
连续白光与静默表达（§5）。风格段从 shot13 起逐字复制。

⚠️ 只做纯文件操作；提交前须校验 5 路输入 MD5 与队列空闲。

Run: py -3.12 tools/make_h3_workflow_shot26.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot25.json")
STYLE_SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot19.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot26.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> <Picture 3> <Picture 4> In the same quiet Chinese "
    "hospital ward as before, with pale green lower walls and cool white upper walls, three "
    "tall windows with a radiator beneath them and pale curtains, a metal hospital bed with "
    "white bedding and a blue blanket, a wooden bedside cabinet, an IV stand, a tall wooden "
    "wardrobe and a round wall clock, all arranged as in the reference <Picture 4>. "
    "Three people only. An elderly Chinese woman with the same face exactly matching the "
    "reference portrait <Picture 1>, short silver-white hair, wearing a pale blue hospital "
    "gown, lying propped up on pillows in the bed. An adult Chinese woman with the same face "
    "exactly matching the reference portrait <Picture 2>, shoulder-length dark hair, wearing "
    "a plain cream knit cardigan, standing beside the bed. A little Chinese girl with the same "
    "face exactly matching the reference portrait <Picture 3>, two dark braids, wearing a white "
    "shirt with red suspenders, beside the bed. At the very start of the shot the little girl "
    "stands close to the bed holding her grandmother's hand with tears on her cheeks, one plain "
    "wooden chair stands beside the bed, and on the bedside cabinet there is a small keepsake "
    "box with two faded red hair ribbons with tiny white flowers lying inside, both clearly "
    "visible. In the first second of the shot, in one continuous slow gentle sequence, the adult "
    "mother moves that wooden chair away from the bedside to one side with both hands to clear a "
    "small space, the chair staying visible the whole time and never disappearing, and then the "
    "little girl begins to dance in that small space, quietly counting the beats to herself, "
    "raising her arms and turning around; at the turn she forgets the step and stops, her face "
    "still wet; the grandmother smiles gently and signals her to start again, and the girl begins "
    "again from the first step and completes the little dance while the grandmother watches it "
    "all the way to the end. The dance is one continuous unbroken movement with no jump, no cut "
    "and no sudden pose change. Then the child leans back over the bedside and the old woman "
    "gently touches the end of one of her braids with her fingertips; the two faded red hair "
    "ribbons with tiny white flowers stay inside the keepsake box the whole time, never "
    "disappearing, never being taken away, never being worn by anyone and never changing into a "
    "plain new ribbon. The adult mother tucks the blanket corner neatly, the curtain at the "
    "window lifts and settles slowly and continuously in a soft breeze, and the old woman closes "
    "her eyes and gradually falls asleep while the little girl still holds her hand. The pale "
    "white ward light stays soft and even throughout, with no sudden brightness change, no "
    "hard-edged light patch and no step. Throughout the shot there is no flashback, no memory "
    "image, no corridor, no cart, no younger version of any character, no superimposed image, "
    "no hard cut, no cross-space transition and no other time or place shown at any point. The "
    "hospital bed, the bedside cabinet, the wooden chair, the keepsake box, the two ribbons, the "
    "IV stand, the three windows, the radiator, the curtains, the wooden wardrobe and the wall "
    "clock stay where they are and never disappear or move abruptly. All three faces are clear "
    "and detailed and remain stable, exactly matching <Picture 1>, <Picture 2> and <Picture 3>; "
    "none of them changes, ages, or swaps with another. All movements are gradual and continuous "
    "with no sudden movement, no abrupt pose changes, no teleporting and no hard cuts, and no "
    "fourth person appears. Soft even white hospital light, cool green-white walls and warm "
    "cream wood tones, no harsh spotlight, no lens flare, no hard-edged light patch. " + STYLE
)


def main():
    wf = json.load(io.open(SRC, encoding="utf-8"))
    base = json.load(io.open(SRC, encoding="utf-8"))
    p19 = json.load(io.open(STYLE_SRC, encoding="utf-8"))["7"]["inputs"]["prompt"]
    assert STYLE in p19 and STYLE in base["7"]["inputs"]["prompt"], "风格段基准不一致"
    assert len(wf) == 18 and "19" in wf

    wf["6"]["inputs"]["file"] = "previs_shot26.mp4"
    wf["16"]["inputs"]["image"] = "SHOT26_C07_face.png"
    wf["17"]["inputs"]["image"] = "SHOT26_C16_face.png"
    wf["18"]["inputs"]["image"] = "SHOT26_C17_face.png"
    wf["19"]["inputs"]["image"] = "SHOT26_E02_ward.png"
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111431
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot26"

    skip = {("6", "file"), ("16", "image"), ("17", "image"), ("18", "image"),
            ("19", "image"), ("7", "prompt"),
            ("9", "noise_seed"), ("15", "filename_prefix")}
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
    ri = wf["7"]["inputs"]["ref_images"]
    assert ri == {"ref_image_1": ["16", 0], "ref_image_2": ["17", 0],
                  "ref_image_3": ["18", 0], "ref_image_4": ["19", 0]}
    assert wf["7"]["inputs"]["ref_videos"] == {"ref_video_1": ["6", 0]}
    assert PROMPT.startswith("<Video 1> <Picture 1> <Picture 2> <Picture 3> <Picture 4>")
    assert STYLE in PROMPT and PROMPT.count(STYLE) == 1
    for s in ("Three people only", "moves that wooden chair away from the bedside",
              "two faded red hair ribbons with tiny white flowers",
              "begins to dance in that small space", "at the turn she forgets the step",
              "begins again from the first step", "watches it all the way to the end",
              "touches the end of one of her braids", "tucks the blanket corner",
              "curtain at the window lifts and settles slowly",
              "gradually falls asleep", "no flashback", "no corridor", "no hard cut",
              "no fourth person appears", "no hard-edged light patch"):
        assert s in PROMPT, f"缺失关键短语: {s}"

    with io.open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)
    print("saved", os.path.relpath(DST, ROOT))
    print("nodes", len(wf), "prompt", len(PROMPT), "seed", wf["9"]["inputs"]["noise_seed"])
    print("STYLE 逐字一致:", STYLE in p19 and STYLE in PROMPT, "| len", len(STYLE))
    print("ref_images", ri)


if __name__ == "__main__":
    main()
