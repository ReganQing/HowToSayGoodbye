# -*- coding: utf-8 -*-
"""以 shot23 的 17 节点工作流为底生成 shot25「病房·跳舞之约」的 18 节点 H3 Ref2VA 工作流。

**4 张 ref_images / 18 节点**（H3 `ref_images` AUTOGROW 上限 9 张，用户 2026-11-14 确认；
历史记录 `.workbuddy/memory/2026-11-12.md` L19、`2026-11-01.md` L145）：
  <Video 1>    previs_shot25.mp4            （只给运动）
  <Picture 1>  SHOT25_C07_face.png          （许宁·老年病房，锁脸）
  <Picture 2>  SHOT25_C16_face.png          （女儿·成年，锁脸）
  <Picture 3>  SHOT25_C17_face.png          （小满·双辫小女孩，锁脸）
  <Picture 4>  SHOT25_E02_ward.png          （E02_v02 水彩病房，锁物件布局）

新增 `LoadImage` 节点 19 + `ref_image_4: ['19', 0]`；其余采样参数与风格段逐字沿用。

剧本七 L369–389 / 方案 §3 §4，P0。核心是「女儿揭开保温桶 → 热气连续升起 → 小满伏床边握手 →
许宁嘴唇动了动又停下」。**剧本 L379–381 有回忆段，但按 §5 全片禁 flashback / 记忆画面 /
硬切 / 跨空间**，只能用同一病房的连续白光与静默表达，prompt 里写死。

⚠️ 本脚本只做纯文件操作；提交前须校验 5 路输入（1 video + 4 image）MD5 与队列空闲。

Run: py -3.12 tools/make_h3_workflow_shot25.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot23.json")
STYLE_SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot19.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot25.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> <Picture 3> <Picture 4> In a quiet Chinese hospital ward "
    "with pale green lower walls and cool white upper walls, three tall windows with a radiator "
    "beneath them and pale gauzy curtains, a metal hospital bed with white bedding and a blue "
    "blanket, a wooden bedside cabinet with a thermos flask and a white mug, an IV stand, a tall "
    "wooden wardrobe and a round wall clock, all arranged as in the reference <Picture 4>. "
    "Three people only. An elderly Chinese woman with the same face exactly matching the reference "
    "portrait <Picture 1>, short silver-white hair, wearing a pale blue hospital gown, lying "
    "propped up on pillows in the hospital bed. An adult Chinese woman with the same face exactly "
    "matching the reference portrait <Picture 2>, shoulder-length dark hair, wearing a plain cream "
    "knit cardigan, standing beside the bed. A little Chinese girl with the same face exactly "
    "matching the reference portrait <Picture 3>, two dark braids, wearing a white shirt with red "
    "suspenders, beside the bed. At the very start of the shot a lidded thermal food container sits "
    "on the bedside cabinet, large and clearly readable, with its lid on. In the first second of the "
    "shot, in one continuous slow gentle sequence, the adult daughter lowers her gaze and lifts the "
    "lid off the thermal food container with one hand, carries the lid sideways and sets it down "
    "beside the container, and thin wisps of hot steam rise continuously from the open container and "
    "grow slightly stronger, carrying the warmth of chicken soup. The lid stays visible on the "
    "cabinet for the whole shot, never vanishing and never changing into another object; the "
    "container and the lid only do this one continuous movement. Then the little girl leans over the "
    "bedside and gently takes her grandmother's hand with both hands, her braids falling forward so "
    "the ends of her hair brush the back of the old woman's hand; she looks up and says one quiet "
    "line as if asking her grandmother to come and see her dance. The elderly woman looks at the "
    "child, her lips move as if about to answer, then she stops and stays quiet, with a small tender "
    "and sad expression. The pale white ward light stays soft and even, with the child's hair and the "
    "steam as the only gentle motion; any passage of time or memory is suggested only by this "
    "continuous quiet light and by the stillness of the three faces, never shown as another place "
    "or another time. Throughout the shot there is no flashback, no memory image, no old ward, no "
    "younger version of any character, no superimposed image, no hard cut, no cross-space transition "
    "and no other time or place shown at any point. The hospital bed, the bedside cabinet, the "
    "thermos flask, the white mug, the IV stand, the three windows, the radiator, the curtains, the "
    "wooden wardrobe, the wall clock, the thermal food container and its lid stay where they are "
    "and never disappear or move abruptly. All three faces are clear and detailed and remain stable, "
    "exactly matching <Picture 1>, <Picture 2> and <Picture 3>; none of them changes, ages, or "
    "swaps with another. All movements are gradual and continuous with no sudden movement, no "
    "abrupt pose changes, no teleporting and no hard cuts, and no fourth person appears. Soft even "
    "white hospital light, cool green-white walls and warm cream wood tones, no harsh spotlight, "
    "no lens flare, no hard-edged light patch. " + STYLE
)


def main():
    wf = json.load(io.open(SRC, encoding="utf-8"))
    base = json.load(io.open(SRC, encoding="utf-8"))
    p19 = json.load(io.open(STYLE_SRC, encoding="utf-8"))["7"]["inputs"]["prompt"]
    assert STYLE in p19, "风格段与 shot19 原文不一致"
    assert STYLE in base["7"]["inputs"]["prompt"], "风格段与 shot23 原文不一致"
    assert len(wf) == 17, f"底稿节点数异常 {len(wf)}"
    assert "19" not in wf, "底稿已有节点 19"

    # 第 4 张参考图：新增 LoadImage 19 + ref_image_4
    wf["19"] = {"class_type": "LoadImage",
                "inputs": {"image": "SHOT25_E02_ward.png"}}
    wf["7"]["inputs"]["ref_images"]["ref_image_4"] = ["19", 0]

    wf["6"]["inputs"]["file"] = "previs_shot25.mp4"
    wf["16"]["inputs"]["image"] = "SHOT25_C07_face.png"
    wf["17"]["inputs"]["image"] = "SHOT25_C16_face.png"
    wf["18"]["inputs"]["image"] = "SHOT25_C17_face.png"
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111430
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot25"

    # 逐字段校验：除 7 处已知改动 + 新增节点 19，其余与 shot23 完全一致
    skip = {("6", "file"), ("16", "image"), ("17", "image"), ("18", "image"),
            ("7", "prompt"), ("7", "ref_images"),
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
    assert len(wf) == 18, f"节点数异常 {len(wf)}"
    ri = wf["7"]["inputs"]["ref_images"]
    assert set(ri) == {"ref_image_1", "ref_image_2", "ref_image_3", "ref_image_4"}
    assert ri == {"ref_image_1": ["16", 0], "ref_image_2": ["17", 0],
                  "ref_image_3": ["18", 0], "ref_image_4": ["19", 0]}
    assert wf["19"]["class_type"] == "LoadImage"
    assert wf["7"]["inputs"]["ref_videos"] == {"ref_video_1": ["6", 0]}
    assert PROMPT.startswith("<Video 1> <Picture 1> <Picture 2> <Picture 3> <Picture 4>")
    assert STYLE in PROMPT and PROMPT.count(STYLE) == 1
    for s in ("Three people only", "as in the reference <Picture 4>",
              "exactly matching the reference portrait <Picture 1>",
              "exactly matching the reference portrait <Picture 2>",
              "exactly matching the reference portrait <Picture 3>",
              "lifts the lid off the thermal food container",
              "thin wisps of hot steam rise continuously",
              "The lid stays visible on the cabinet for the whole shot",
              "leans over the bedside and gently takes her grandmother's hand",
              "her lips move as if about to answer, then she stops",
              "no flashback", "no memory image", "no hard cut",
              "no cross-space transition", "no fourth person appears",
              "no hard-edged light patch"):
        assert s in PROMPT, f"缺失关键短语: {s}"

    with io.open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)
    print("saved", os.path.relpath(DST, ROOT))
    print("nodes", len(wf), "prompt", len(PROMPT), "seed", wf["9"]["inputs"]["noise_seed"])
    print("STYLE 逐字一致:", STYLE in p19 and STYLE in PROMPT, "| len", len(STYLE))
    print("ref_images", ri)


if __name__ == "__main__":
    main()
