# -*- coding: utf-8 -*-
"""以 shot20 的 16 节点工作流为底生成 shot24「两碗面」的 MiniMax H3 Ref2VA 工作流。

单人镜头 = 2 张 ref_images + 1 个 LoadVideo，16 节点，与 shot13/shot20 同构：
  <Video 1>    previs_shot24.mp4            （只给运动）
  <Picture 1>  SHOT24_C07b_face.png         （许宁·老年居家，锁脸）
  <Picture 2>  SHOT24_E09_table.png         （E09 折叠餐桌，锁物件布局）

剧本七 L363–367 / 方案 §3 §4，P0。**硬约束：对面椅子全程空**——全片只有一位
老人，不得出现第二个人、人影，也不得让 H3 把空椅补成有人；prompt 里写死。

核心是「状态保持型」双碗 + 空椅：两只面碗 f001 起就在桌上、全程恒存同位，
唯一变化是热气从可见连续渐弱到无（关键变化前置 f001–f024）；末段手机是
位移型道具，必须给出桌面 → 手 → 贴耳的完整连续位移，不得凭空出现。
剧本含「第二天」，但按 §5 禁止硬切/回忆/跨空间，用连续光照渐变 + 手机拿起
在同一空间内表达。风格段从 shot13 起逐字复制，绝不改写（§5.2）。

⚠️ 本脚本只做纯文件操作；真正提交前须校验 3 路输入 MD5 与队列空闲。

Run: py -3.12 tools/make_h3_workflow_shot24.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot20.json")
STYLE_SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot19.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot24.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> In a small modest Chinese apartment room with cool "
    "blue-grey walls, a folding dining table with pale wood top and dark crossed legs, two plain "
    "wooden chairs one on the near side and one on the far side of the table, a north window with "
    "a gauzy white curtain, a low wooden cabinet against the right wall with a lidded cooking pot "
    "and a stack of small bowls and a white mug on it, and a tall thermos flask, all arranged as "
    "in the reference <Picture 2>. One person only. An elderly Chinese woman with the same face "
    "exactly matching the reference portrait <Picture 1>, wavy silver-white hair, wearing a "
    "cream knit cardigan over a white collared shirt, sitting alone on the near-side wooden chair "
    "at the folding table. The wooden chair on the far side of the table, directly opposite her, "
    "is empty and stays completely empty for the entire shot: no one ever sits on it, no second "
    "person appears anywhere, no human silhouette, no shadow of a person, no figure in the "
    "doorway and no reflection of a person; that empty chair never moves and is never occupied. "
    "At the very start of the shot there are two bowls of noodles on the table, one in front of "
    "her and one in front of the empty chair, both large, clearly readable and steaming with "
    "thin visible wisps of hot steam, with a pair of chopsticks beside each bowl; the two bowls "
    "are the most important objects in the frame. In the first second of the shot, in one "
    "continuous slow gentle sequence, the thin steam above both bowls begins to fade, growing "
    "weaker and thinner gradually and continuously until the noodles have gone completely cold "
    "and there is no steam at all, while both bowls stay exactly where they are, never moved, "
    "never eaten from, never refilled, never covered and never disappearing. She sits quietly "
    "without getting up, says one short quiet line and then stops and waits as if listening for "
    "a response that does not come, her hands resting near the table edge. The pale warm "
    "afternoon light from the window fades slowly, gradually and continuously into cool "
    "blue-grey early evening within this same room, with no sudden brightness change, no "
    "hard-edged light patch, no step and no change of place or time jump; the passage of time "
    "until the next day is suggested only by this continuous light change and by her quiet "
    "stillness, never by a cut or a flashback. Near the end of the shot a mobile phone is "
    "resting on the table beside her hand, clearly visible; she slowly reaches for it, picks it "
    "up with one hand in one continuous movement, lifts it gradually to her ear and holds it "
    "there, making a quiet phone call to her daughter, with a small sad and tender expression. "
    "The phone is continuously visible moving from the table into her hand and up to her ear "
    "with no jump and no cut; it never vanishes earlier, never floats away, never teleports and "
    "never changes into another object. Both bowls of noodles, both pairs of chopsticks, the "
    "empty chair opposite, the thermos, the low cabinet, the lidded pot, the stack of bowls, "
    "the white mug, the window and the curtain stay where they are for the whole shot and never "
    "disappear or move abruptly. Throughout the shot there is no flashback, no memory image, no "
    "hard cut, no cross-space transition, no second location and no other time or place shown "
    "at any point, and only one person is ever present. She remains seated on the near chair "
    "with both feet on the ground, all movements are gradual and continuous with no sudden "
    "movement, no abrupt pose changes and no teleporting, and no third person appears. Her face "
    "is clear and detailed and remains stable, exactly matching <Picture 1>; it does not change, "
    "age or swap with another face. Soft cool north window light grading gently into quiet "
    "blue-grey evening, warm cream wood tones, no harsh spotlight, no lens flare. "
    + STYLE
)


def main():
    wf = json.load(io.open(SRC, encoding="utf-8"))
    base19 = json.load(io.open(STYLE_SRC, encoding="utf-8"))["7"]["inputs"]["prompt"]
    base20 = wf["7"]["inputs"]["prompt"]
    assert STYLE in base19, "风格段与 shot19 原文不一致"
    assert STYLE in base20, "风格段与 shot20 原文不一致"
    assert len(wf) == 16, f"底稿节点数异常 {len(wf)}"
    assert set(wf["7"]["inputs"]["ref_images"]) == {"ref_image_1", "ref_image_2"}

    wf["6"]["inputs"]["file"] = "previs_shot24.mp4"
    wf["16"]["inputs"]["image"] = "SHOT24_C07b_face.png"
    wf["17"]["inputs"]["image"] = "SHOT24_E09_table.png"
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111429
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot24"

    base = json.load(io.open(SRC, encoding="utf-8"))
    skip = {("6", "file"), ("16", "image"), ("17", "image"),
            ("7", "prompt"), ("9", "noise_seed"), ("15", "filename_prefix")}
    diff = []
    for k in base:
        assert base[k]["class_type"] == wf[k]["class_type"], k
        for field, val in base[k]["inputs"].items():
            if (k, field) in skip:
                continue
            if val != wf[k]["inputs"].get(field, "<缺失>"):
                diff.append((k, field))
    assert not diff, f"非预期差异: {diff}"
    assert len(wf) == 16
    assert PROMPT.startswith("<Video 1> <Picture 1> <Picture 2>")
    assert STYLE in PROMPT and PROMPT.count(STYLE) == 1
    for s in ("One person only",
              "stays completely empty for the entire shot",
              "no second person appears anywhere",
              "no human silhouette, no shadow of a person",
              "two bowls of noodles on the table",
              "steaming with thin visible wisps of hot steam",
              "gradually and continuously until the noodles have gone completely cold",
              "never moved, never eaten from, never refilled, never covered and never disappearing",
              "fades slowly, gradually and continuously into cool blue-grey early evening",
              "no hard-edged light patch",
              "picks it up with one hand in one continuous movement",
              "lifts it gradually to her ear",
              "no flashback", "no hard cut", "no third person appears"):
        assert s in PROMPT, f"缺失关键短语: {s}"

    with io.open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=2)
    print("saved", os.path.relpath(DST, ROOT))
    print("nodes", len(wf), "prompt", len(PROMPT), "seed", wf["9"]["inputs"]["noise_seed"])
    print("STYLE 逐字一致:", STYLE in base19 and STYLE in base20 and STYLE in PROMPT,
          "| len", len(STYLE))
    print("ref_images", wf["7"]["inputs"]["ref_images"])


if __name__ == "__main__":
    main()
