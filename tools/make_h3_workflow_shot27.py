# -*- coding: utf-8 -*-
"""以 shot23 工作流为底生成 shot27「幕布拉开」的 MiniMax H3 Ref2VA 工作流。

两人镜头 + 一张场景图 = 3 张 ref_images，17 节点，与 shot15/17/18/19/21/22/23 同构：
  <Video 1>  previs_shot27.mp4            （只给运动）
  <Picture 1> SHOT27_C16_face.png          （妈妈·成年，锁脸）
  <Picture 2> SHOT27_C17_face.png          （小满·双辫，锁脸）
  <Picture 3> SHOT27_E12_stage.png         （E12 学校舞台，锁物件布局）

剧本七 L419–439 / 方案 §3 §4，P0，shot15–27 十三镜收束镜。核心是**三代红发带
结构呼应收束**：D09 遗物盒里 P01 姥姥与 P02 妈妈的两条褪色旧红发带（末端带小白花）
全程恒存；妈妈把 P03 一对鲜红、末端无白花的新红发带系到小满两条辫梢。
P03 是「位移型 + 状态型混合」道具：f001 起就在妈妈手里可见，必须给出
「手中 → 举起 → 绕到辫梢 → 系好」完整连续链，不凭空出现（§5.19/§5.25）；
旧带不得被拿走/消失/变成新带（§5.18 的反面：本镜**没有任何物体允许消失**）。

关键变化（换新带 + 幕布开始拉开）前置 f001–f048（§5.21）：幕布从首帧就缓慢
连续向两侧分开并贯穿全片，末段完全拉开，幕布板片恒在两侧不消失。
暖顶光用真实连续光源渐亮渐暖，禁几何光斑板（§3 D5）。
L419 许宁去世与 L421–428 整理遗物属前序叙事，全片只画同一舞台侧幕空间，
显式禁 flashback / 葬礼 / 病房 / 遗物整理闪回 / 第二个时空。

风格段从 shot13 起逐字复制，绝不改写（§5.2）。

⚠️ 本脚本只做纯文件操作；真正提交前须校验 4 路输入 MD5 与队列空闲。

Run: py -3.12 tools/make_h3_workflow_shot27.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot23.json")
STYLE_SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot19.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot27.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> <Picture 3> On a school auditorium stage seen from the "
    "wings, with heavy deep indigo-red stage curtains drawn closed in soft vertical folds, "
    "three warm amber overhead stage lights, side curtains, a few stacked wooden chairs "
    "backstage, a narrow glimpse of blurred empty dark-red audience seat backs beyond the "
    "front edge, and a simple wooden stage floor, all arranged as in the reference "
    "<Picture 3>. Two people only. A Chinese adult woman with the same face exactly matching "
    "the reference portrait <Picture 1>, dark shoulder-length hair, wearing a plain cream "
    "cardigan, the mother. A Chinese little girl with the same face exactly matching the "
    "reference portrait <Picture 2>, two neat dark braids, wearing a pale cream dress with "
    "red shoulder straps, her daughter. On a small wooden table beside the stacked chairs "
    "backstage there is an open keepsake box containing two faded old red hair ribbons with "
    "tiny white flowers at their ends; these two old ribbons are dull dark red, clearly "
    "different from the new ones, and they remain inside the open box, visible and untouched, "
    "in exactly the same place for the whole shot. They are never picked up, never replaced, "
    "never turned into a new ribbon and never disappear. At the very start of the shot the "
    "mother is already holding a pair of fresh bright red hair ribbons with no white flowers "
    "at their ends, clearly visible in her hands; this new pair never appears out of nowhere. "
    "In the first second of the shot, in one continuous slow gentle sequence, she raises the "
    "new pair, reaches to the girl's two braids, and ties one fresh red ribbon around the end "
    "of each braid, the ribbons moving continuously from her hands to the two braid tips with "
    "no jump, no cut and no teleporting. From that moment on the two fresh red ribbons stay "
    "tied at the braid tips, while the two faded old ribbons with white flowers stay in the "
    "open box; the old and the new are never mixed up and never swapped. The girl then touches "
    "one braid and her face grows quiet and close to tears. The mother crouches down slowly in "
    "front of her and smooths the hem of her dress flat with both hands, without asking her to "
    "hold back her tears. The girl wipes her own face with her hand and looks up. The heavy "
    "curtains begin to part slowly from the very first frames and continue to open toward both "
    "sides smoothly and continuously through the whole shot, gradually revealing warm stage "
    "light and a soft blurred glimpse of the audience seats beyond, with no sudden opening, no "
    "jump and no cut; the curtain panels stay visible at both sides and never vanish. She walks "
    "forward a few steps through the widening gap toward the stage front and glances once "
    "toward the audience seats. The warm overhead light grows gently warmer and brighter, "
    "continuous with no step, no hard-edged light patch and no lens flare. At the end she "
    "slowly lifts one arm, and the fresh red ribbons at her braid tips catch the warm light "
    "and give one soft brief flash as they move. Throughout the shot there is no flashback, no "
    "memory image, no funeral, no hospital room, no sickbed, no sorting-through-belongings "
    "scene, no hard cut, no cross-space transition and no other time or place shown at any "
    "point. No third person appears, no audience faces are shown, and the stacked chairs "
    "remain empty. Both faces are clear and detailed and remain stable, the mother's face "
    "exactly matching <Picture 1> and the girl's face exactly matching <Picture 2>; neither "
    "face changes, ages, or swaps with the other. No object in this shot disappears from view, "
    "no object appears out of nowhere, and no object changes into another. All movements are "
    "gradual and continuous with no sudden movement, no abrupt pose changes and no "
    "teleporting. "
    + STYLE
)


def main():
    wf = json.load(io.open(SRC, encoding="utf-8"))
    base19 = json.load(io.open(STYLE_SRC, encoding="utf-8"))["7"]["inputs"]["prompt"]
    base23 = wf["7"]["inputs"]["prompt"]
    assert STYLE in base19, "风格段与 shot19 原文不一致"
    assert STYLE in base23, "风格段与 shot23 原文不一致"
    assert len(wf) == 17, f"底稿节点数异常 {len(wf)}"

    wf["6"]["inputs"]["file"] = "previs_shot27.mp4"
    wf["16"]["inputs"]["image"] = "SHOT27_C16_face.png"
    wf["17"]["inputs"]["image"] = "SHOT27_C17_face.png"
    wf["18"]["inputs"]["image"] = "SHOT27_E12_stage.png"
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111432
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot27"

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
    for s in ("Two people only",
              "two faded old red hair ribbons with tiny white flowers",
              "a pair of fresh bright red hair ribbons with no white flowers",
              "moving continuously from her hands to the two braid tips",
              "never mixed up and never swapped",
              "crouches down slowly in front of her",
              "smooths the hem of her dress flat",
              "wipes her own face with her hand",
              "begin to part slowly from the very first frames",
              "the curtain panels stay visible at both sides and never vanish",
              "glances once toward the audience seats",
              "give one soft brief flash",
              "no funeral, no hospital room",
              "no flashback", "no hard cut", "No third person appears",
              "no hard-edged light patch",
              "No object in this shot disappears from view"):
        assert s in PROMPT, f"缺失关键短语: {s}"

    with io.open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)
    print("saved", os.path.relpath(DST, ROOT))
    print("nodes", len(wf), "prompt", len(PROMPT), "seed", wf["9"]["inputs"]["noise_seed"])
    print("STYLE 逐字一致:", STYLE in base19 and STYLE in base23 and STYLE in PROMPT)
    print("ref_images", wf["7"]["inputs"]["ref_images"])


if __name__ == "__main__":
    main()
