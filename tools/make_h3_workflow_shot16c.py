# -*- coding: utf-8 -*-
"""shot16 v03：只换白模预演参考视频，验证「运动通道缺失」这一根因。

以 v02 工作流 h3_r2v_workflow_shot16b.json 为底，**只改 3 处**：
  node 6  LoadVideo.file        previs_shot16.mp4 → previs_shot16b.mp4
  node 9  noise_seed            2026111417 → 2026111418
  node 15 filename_prefix      h3_r2v_shot16b → h3_r2v_shot16c

prompt 从 v02 文件逐字读入、原样写回，一字不改；风格段亦逐字沿用 shot13/14/15。
这是刻意的单变量实验：v01（原 prompt + 原预演）、v02（强化 prompt + 原预演）
两版都没能生成「发带放进小包」，v03 只改预演，用来判定根因是 prompt 权重
还是参考视频缺少运动通道。

v02 判退依据（progress/06_质检返修/shot16_v02_发带仍未入包_弃用/v02_verdict.json）：
  发带确实从桌面消失了，但 f130-192 手全程只在桌面中央活动，从未移向左侧
  椅面上的小包；包口 f001/f137/f160/f192 四帧对比零变化。仍是「被收走 /
  凭空消失」，不是剧本 L283「叠好，放进随身的小包」。

复核发现 previs_shot16.py 里发带 f137-160 只在桌布上折短、滑到
RIBBON_FOLD_END=(0.98,0.62,0.782)，f161-176 原地缩小到不可见，位置始终在
桌面，从未离桌、从未到过 BAG_MOUTH=(0.98,0.30,0.655)。H3 Ref2VA 以参考
视频锁运动拓扑，prompt 补不出大幅位移。v03 预演由
tools/previs_shot16b.py 补齐「折短 → 抬起 → 横移到包口上方 → 下沉入包 →
完全消失」五段链，并把发带做成白模里清晰可辨的鲜红色带。

原 v01 / v02 工作流与成片全部保留，过程素材不删不覆盖。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot16b.json")  # v02，判退但保留
DST = os.path.join(ROOT, "tools", "h3_r2v_workflow_shot16c.json")  # v03

STYLE = ("Refined watercolor concept-art animation style, delicate fine ink linework, "
         "loose transparent watercolor washes, granular cold-press paper texture, "
         "restrained indigo grey-green and warm cream palette, hand painted, "
         "quiet unhurried atmosphere, gentle seamless motion. "
         "Slow subtle camera push-in, very slight handheld sway.")


def main():
    with open(SRC, encoding="utf-8") as f:
        base = json.load(f)
    assert len(base) == 18, f"v02 节点数异常 {len(base)}"
    assert STYLE in base["7"]["inputs"]["prompt"], "v02 风格段异常，需核对"
    assert base["6"]["inputs"]["file"] == "previs_shot16.mp4"

    wf = json.loads(json.dumps(base))            # 深拷贝，绝不改动 v02 文件
    wf["6"]["inputs"]["file"] = "previs_shot16b.mp4"
    wf["9"]["inputs"]["noise_seed"] = 2026111418
    wf["15"]["inputs"]["filename_prefix"] = "h3_r2v_shot16c"

    # 逐字段比对：除 3 个预期字段外必须零差异，prompt 逐字相同
    skip = {("6", "file"), ("9", "noise_seed"), ("15", "filename_prefix")}
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
    assert wf["7"]["inputs"]["prompt"] == base["7"]["inputs"]["prompt"], "prompt 被改动了"
    assert set(wf["7"]["inputs"]["ref_images"]) == {
        "ref_image_1", "ref_image_2", "ref_image_3", "ref_image_4"}
    assert STYLE in wf["7"]["inputs"]["prompt"]
    assert wf["7"]["inputs"]["prompt"].startswith(
        "<Video 1> <Picture 1> <Picture 2> <Picture 3> <Picture 4>")
    for s in ("never set back down on the table", "must not reappear",
              "no ribbon anywhere on the tablecloth",
              "draws her hand back out of the bag empty",
              "completely hidden inside the handbag"):
        assert s in wf["7"]["inputs"]["prompt"], f"v02 关键短语丢失: {s}"

    with open(DST, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=1)
    print(f"写出 {DST}")
    print(f"节点 {len(wf)} 个，非预期差异 {len(diff)}，prompt {len(wf['7']['inputs']['prompt'])} 字符（逐字沿用 v02）")
    print("风格段逐字一致:", STYLE in base["7"]["inputs"]["prompt"])
    print("LoadVideo:", wf["6"]["inputs"]["file"],
          "seed:", wf["9"]["inputs"]["noise_seed"],
          "prefix:", wf["15"]["inputs"]["filename_prefix"])


if __name__ == "__main__":
    main()
