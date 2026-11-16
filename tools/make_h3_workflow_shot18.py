# -*- coding: utf-8 -*-
"""以 shot15 工作流为底生成 shot18「楼下晨光·婴儿车」的 MiniMax H3 Ref2VA 工作流。

shot18 两位角色 + 一张场景图 = 3 张 ref_images，17 节点，与 shot15/shot17 同构：
  <Video 1>  previs_shot18.mp4          （只给运动）
  <Picture 1> SHOT18_C06_face.png        （许宁·成年，复用 C06_v07_head.png）
  <Picture 2> SHOT18_C20_face.png        （婴儿·半岁，tools/gen_ref_shot18.py 生成后裁切）
  <Picture 3> SHOT18_E13_morning.png     （E13 楼下晨景，锁布局）

剧本五 L305-311 / 方案 §4。核心动作「弯腰擦口水 → 手指在小脸上停住 → 抬头静住 →
被女儿抓住手指往嘴边带 → 轻抽回手 → 俯身亲额头」，按 HANDOFF §5 第 19 条：
这条链必须在白模预演里给出完整可辨识的左臂手 K（tools/previs_shot18.py 用
每帧坐标下降求解，探针结论见 tmp_qc/shot18_arm_poses.json），
工作流文本只负责补细节、补不出位移。

沿用 shot16 v02 / shot17 的写法：核心动作提前到中段单独成句写全连续链、
By the end 三重声明终态、硬约束写死无闪回硬切 / 无第四人 / 道具位置不变。

风格段从 shot14/shot15/shot16/shot17 原文逐字复制，绝不改写（HANDOFF §5.2）。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot15.json")
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot18.json")

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")

PROMPT = (
    "<Video 1> <Picture 1> <Picture 2> <Picture 3> In the early morning at the foot of an old "
    "Chinese residential apartment building, a folded-up street breakfast stall with a plain "
    "cloth cover, stacked small stools and a few plastic crates beside it, a large thermos and "
    "a covered pot on a low table, a low plaster wall with a patch of pale gold morning "
    "sunlight, a narrow paved path wide enough for a baby stroller, long soft shadows, the "
    "layout of the stall, the low wall, the crates and the path matching the reference "
    "<Picture 3>. Two people only. A Chinese woman in her late twenties with the same face "
    "exactly matching the reference portrait <Picture 1>, neat dark shoulder-length hair, "
    "wearing a light cream short jacket over a plain blouse and dark indigo trousers. A "
    "six-month-old Chinese baby girl with the same face exactly matching the reference "
    "portrait <Picture 2>, wrapped snugly in a plain pale cream swaddle, lying awake in a "
    "simple baby stroller with her eyes open. At the start of the shot the young woman has "
    "just brought the stroller to a gentle stop beside the low wall and is standing upright "
    "beside it, looking down at the baby; the baby is awake and looking up at her, the stroller "
    "is firmly on the paved path, the morning sunlight and the long shadows are already there. "
    "Over the course of the shot, in one continuous slow gentle sequence: the young woman "
    "gradually bends forward and down toward the stroller, slowly raises one hand and gently "
    "wipes the corner of the baby's mouth with her fingertips, then lets her fingers come to "
    "rest for a quiet unhurried moment against the baby's soft cheek; she slowly lifts her "
    "gaze and becomes still for a moment as if quietly remembering something from many years "
    "ago, and only then does she gradually draw her hand back and straighten up a little with "
    "a very small quiet smile, while the baby reaches one tiny hand toward her finger and "
    "tugs it gently toward her mouth; she bends down once more to press a very light kiss on "
    "the baby's forehead and then slowly straightens up again. By the "
    "end of the shot the young woman is upright again with her two hands back at her own sides, "
    "the baby is still awake in the stroller with her eyes open, the stroller is still in the "
    "same place on the path, the morning sunlight and the long soft shadows are unchanged, and "
    "the two of them are quiet together in the early light. Throughout the shot there is no "
    "flashback, no memory image, no hard cut, no cross-space transition and no other time or "
    "place shown at any point; the memory is suggested only by her stillness and her gaze. The "
    "stroller never disappears, never floats, never moves away and never changes shape; the "
    "folded breakfast stall, the cloth cover, the stacked stools, the plastic crates, the "
    "thermos, the covered pot and the low wall stay in the same positions and keep the same "
    "appearance; both the woman's feet stay on the ground and the baby stays inside the "
    "stroller; every movement of her head, her arms and her hand is gradual and continuous "
    "with no sudden movement, no abrupt pose changes and no hard cuts, no third person "
    "appears. Both faces are clear and detailed and remain stable, the young woman's face "
    "exactly matching <Picture 1>, the baby's face exactly matching <Picture 2>; neither face "
    "changes, ages, or swaps with the other. Early morning lighting: pale gold low sunlight, "
    "long soft shadows, cool blue-grey shade under the wall, no harsh spotlight, no lens flare. "
    + STYLE
)


def main():
    with open(SRC, encoding="utf-8") as f:
        wf = json.load(f)
    base_prompt = wf["7"]["inputs"]["prompt"]
    assert STYLE in base_prompt, "风格段与 shot15 原文不一致，需核对"
    assert len(wf) == 17, f"底稿节点数异常 {len(wf)}"

    wf["6"]["inputs"]["file"] = "previs_shot18.mp4"
    wf["16"]["inputs"]["image"] = "SHOT18_C06_face.png"        # ref_image_1 许宁
    wf["17"]["inputs"]["image"] = "SHOT18_C20_face.png"        # ref_image_2 婴儿
    wf["18"]["inputs"]["image"] = "SHOT18_E13_morning.png"     # ref_image_3 场景
    wf["7"]["inputs"]["prompt"] = PROMPT
    wf["9"]["inputs"]["noise_seed"] = 2026111420
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot18"

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
    assert len(wf) == 17
    assert set(wf["7"]["inputs"]["ref_images"]) == {
        "ref_image_1", "ref_image_2", "ref_image_3"}
    assert STYLE in PROMPT
    assert PROMPT.startswith("<Video 1> <Picture 1> <Picture 2> <Picture 3>")
    for s in ("no flashback", "no hard cut", "never disappears", "no third person",
              "long soft shadows are unchanged", "come to rest for a quiet unhurried moment",
              "tugs it gently toward her mouth", "press a very light kiss"):
        assert s in PROMPT, f"缺失关键短语: {s}"

    with open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=1)
    print(f"写出 {DST}")
    print(f"节点 {len(wf)} 个，非预期差异 {len(diff)}，prompt {len(PROMPT)} 字符")
    print("风格段逐字一致:", STYLE in base_prompt and STYLE in PROMPT)
    print("seed:", wf["9"]["inputs"]["noise_seed"], "prefix:", wf["15"]["inputs"]["filename_prefix"])
    print("四路标注:", PROMPT[:50])


if __name__ == "__main__":
    main()
