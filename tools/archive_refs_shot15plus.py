# -*- coding: utf-8 -*-
"""shot15+ 参考图：目检结论回填台账 + 过程素材归档（含弃用稿，保留返修轨迹）。

Ron 2026-11-13 要求「注意过程素材的记录」：不合格稿不删除、不覆盖，
连同判定原因一起归档，保证每一版定稿都可追溯到为什么被换掉。

Run:
  py -3.12 tools/archive_refs_shot15plus.py
"""
import json
import os
import shutil

ROOT = r"."
REF = os.path.join(ROOT, "assets", "ref")
FACE = os.path.join(ROOT, "assets", "ref_face")
P03 = os.path.join(ROOT, "progress", "03_场景建模")
P02 = os.path.join(ROOT, "progress", "02_角色建模")
LEDGER = os.path.join(ROOT, "progress", "01_剧本分镜", "shot15+_参考图台账.json")

# version -> (verdict, visual_check, note)
VERDICTS = {
    "E02_v02": ("accepted_final", "passed",
                "水彩重绘定稿。绿白分色墙/三扇窗+暖气片/金属病床+床头柜+暖壶/输液架/木衣柜+挂钟/浅地砖全部保留；细墨线水彩纸纹，无人物无水印，与 E09 同族。"),
    "E11_v01": ("accepted_final", "passed",
                "定稿。防盗格栅、头顶竹竿、两把并排小木凳、一篮豆角、窗台盆栽与搪瓷盆、春日斜光齐全；两凳并排可容纳并排择豆角。无人物无文字。"),
    "E12_v01": ("accepted_final", "passed",
                "定稿。深靛红幕布垂褶、侧幕、后台叠椅、暖顶光、前景观众席椅背、木地板；偏暗但仍保持纸感，无镜头光晕/照片感。视角为观众席看向闭合舞台，供 H3 锁物件与画风。"),
    "E13_v01": ("accepted_final", "passed",
                "定稿。收摊早点摊（布罩/叠凳/塑料保温箱）、暖壶与盖锅、低围墙、可通行婴儿车的窄巷、晨光长影；无人物无招牌文字无水印。"),
    "C06b_v01": ("rejected_cartoon", "failed",
                 "不合格。动漫大眼、腮红、咧嘴微笑、波波头，被画成三十岁卡通角色，与 v07 写实水彩成人脸不同族。文件保留作过程素材，不进 H3/Lux3D 素材池。"),
    "C07b_v01": ("rejected_cartoon", "failed",
                 "不合格。卡通卷发老奶奶、大眼腮红、咧嘴笑，与 v07 写实老人脸不同族。保留作过程素材。"),
    "C18_v01": ("rejected_cartoon", "failed",
                "不合格。卡通老爷爷、大圆眼腮红卡通笑，虽保留圆框眼镜/米色毛衣但与 C15_v02 写实青年脸不同族。保留作过程素材。"),
    "C06b_v02": ("rejected_layout", "passed_face_failed_layout",
                 "脸部已修复为写实成熟水彩脸（保留价值高），但三视图被画成正/正/背，中间缺严格 90° 侧视，违反三视图一致性。由 v03 取代。"),
    "C07b_v02": ("accepted_final", "passed",
                 "定稿。正/侧/背标准三视图，写实老人脸（深法令纹、眼角纹、自然小眼、闭口中性表情），米色开衫+深灰裤+白软拖鞋，区别于 C07 病号服。"),
    "C18_v02": ("rejected_layout", "passed_face_failed_layout",
                "脸部已修复为写实老人水彩脸，但三视图被画成正/正/背，缺严格侧视。由 v03 取代。"),
    "C06b_v03": ("accepted_final", "passed",
                 "定稿。正/侧/背标准三视图，成熟写实水彩脸（灰黑发、眼角细纹、法令纹、闭口中性表情），灰针织开衫+深靛裤+黑软底鞋，与 v07 同族。"),
    "C18_v03": ("accepted_final", "passed",
                "定稿。正/侧/背标准三视图，写实老人脸，圆框黑眼镜/米色毛衣+浅蓝衬衫领/深灰裤/白球鞋识别点齐全，与 C15_v02 同源。毛衣领口为 V 领（青年版为圆领），属非阻断偏差。"),
}

# (源文件相对 assets/ref, 归档目标相对 progress/, 是否重命名)
ARCHIVE = [
    ("E02/E02_v02.png",   "03_场景建模/E02_病房/E02_v02.png", False),
    ("E11/E11_v01.png",   "03_场景建模/E11_阳台/E11_v01.png", False),
    ("E12/E12_v01.png",   "03_场景建模/E12_学校舞台/E12_v01.png", False),
    ("E13/E13_v01.png",   "03_场景建模/E13_楼下晨景/E13_v01.png", False),
    ("C06b/C06b_v03.png", "02_角色建模/C06b_许宁·中老年居家/C06b_v03.png", False),
    ("C06b/C06b_v02.png", "02_角色建模/C06b_许宁·中老年居家/C06b_v02_版式偏差_弃用.png", True),
    ("C06b/C06b_v01.png", "02_角色建模/C06b_许宁·中老年居家/C06b_v01_卡通化_弃用.png", True),
    ("C07b/C07b_v02.png", "02_角色建模/C07b_许宁·老年居家/C07b_v02.png", False),
    ("C07b/C07b_v01.png", "02_角色建模/C07b_许宁·老年居家/C07b_v01_卡通化_弃用.png", True),
    ("C18/C18_v03.png",   "02_角色建模/C18_周远·老年/C18_v03.png", False),
    ("C18/C18_v02.png",   "02_角色建模/C18_周远·老年/C18_v02_版式偏差_弃用.png", True),
    ("C18/C18_v01.png",   "02_角色建模/C18_周远·老年/C18_v01_卡通化_弃用.png", True),
]

ASSET_TIERS = {
    "成片画风锚（进 H3 ref_images）":
        "水彩场景图 + 水彩头肩面容图。Ron 2026-11-13 决策：绝对不要出现现实画风。",
    "建模中间素材（仅进 Lux3D，不进 H3）":
        "写实 T-pose 单视图。gen_c15_tpose.py 记录的踩坑：水彩画不出严格 T-pose 会触发 "
        "RIG_ELIGIBILITY_FAILED，故建模输入必须用写实图；它不进 H3 ref_images，不影响成片画风。",
    "运动参考（进 H3 LoadVideo）":
        "Blender 哑光白模预演 mp4，只提供运动，不提供画风。",
}


def main():
    with open(LEDGER, encoding="utf-8") as f:
        ledger = json.load(f)

    # 回填生成稿目检结论
    missing = []
    for job in ledger.get("jobs", []):
        v = job["version"]
        if v not in VERDICTS:
            missing.append(v)
            continue
        verdict, check, note = VERDICTS[v]
        job["verdict"] = verdict
        job["visual_check"] = check
        job["qc_note"] = note
    if missing:
        print("!! 台账中缺判定:", missing)

    # 回填面容图目检结论
    for item in ledger.get("face_crops", {}).get("items", []):
        item["visual_check"] = "passed"
        item["verdict"] = "accepted_final"
        item["qc_note"] = ("联系表目检通过：单人正面头肩，头顶/下巴/肩上缘完整，"
                           "未混入侧背视图、右侧色卡或文字，构图与 C05_v07_head / C15_v02_head 一致。")

    ledger["style_policy"]["asset_tiers"] = ASSET_TIERS
    ledger["style_policy"]["rework_trace"] = (
        "三张角色稿 v01 因动漫卡通化判退 → v02 用『成熟面部结构/中性闭口/自然小窄眼』正向描述修回写实水彩脸"
        "（Z-Image Turbo 在 CFG 1.0 下负向词权重极低，卡通化只能靠正面描述压）→ "
        "C06b/C18 的 v02 三视图为正/正/背缺严格侧视，v03 补『strict ninety degree side profile view』修正。"
        "C07b 的 v02 一次通过。弃用稿全部保留归档。"
    )
    ledger["final_assets"] = {
        "scenes": ["assets/ref/E02/E02_v02.png", "assets/ref/E11/E11_v01.png",
                   "assets/ref/E12/E12_v01.png", "assets/ref/E13/E13_v01.png"],
        "character_sheets": ["assets/ref/C06b/C06b_v03.png", "assets/ref/C07b/C07b_v02.png",
                             "assets/ref/C18/C18_v03.png"],
        "face_refs": ["assets/ref_face/" + os.path.basename(i["output"])
                      for i in ledger.get("face_crops", {}).get("items", [])],
    }

    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
    print("LEDGER 已回填:", len(ledger.get("jobs", [])), "条生成稿 /",
          len(ledger.get("face_crops", {}).get("items", [])), "条面容图")

    # 归档（已存在则跳过，不覆盖）
    copied = skipped = 0
    for rel, target_rel, _ in ARCHIVE:
        src = os.path.join(REF, rel.replace("/", os.sep))
        dst = os.path.join(ROOT, "progress", target_rel.replace("/", os.sep))
        if not os.path.isfile(src):
            print("MISSING", src)
            continue
        if os.path.isfile(dst):
            skipped += 1
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
        print("ARCHIVE", target_rel)

    # 面容图联系表归档为目检证据
    contact_src = os.path.join(FACE, "_contact_shot15plus.jpg")
    contact_dst = os.path.join(P02, "_shot15plus_面容图联系表.jpg")
    if os.path.isfile(contact_src) and not os.path.isfile(contact_dst):
        shutil.copy2(contact_src, contact_dst)
        copied += 1
        print("ARCHIVE 02_角色建模/_shot15plus_面容图联系表.jpg")

    print(f"归档完成：新增 {copied} / 跳过 {skipped}")


if __name__ == "__main__":
    main()
