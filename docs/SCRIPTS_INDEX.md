# 脚本索引（自动生成）

> 由 `tools/build_github_repo.py` 生成；全部脚本保持项目内原始文件名与平铺结构。

## 建模与资产生成 · 65 个

参考图生成、T-pose、Lux3D 建模流水线、骨骼探针与 GLB 检查

| 脚本 | 说明 |
| --- | --- |
| `anim_qc.py` | QC animated GLB files: sample frames across each clip and render them. |
| `archive_refs_shot15plus.py` | shot15+ 参考图：目检结论回填台账 + 过程素材归档（含弃用稿，保留返修轨迹）。 |
| `build_models_shot15plus.py` | shot15+ 八个角色的 Lux3D 独立建模流水线（可续跑、每步留痕）。 |
| `comfy_ref_gen.py` | Drive local ComfyUI (Z-Image Turbo) to render reference images for Lux |
| `diag_shot02.py` | 诊断 shot02 预演布局：打印各对象 world bbox + 从 shot01 机位渲染全局定位图。 |
| `face_crop.py` | 从水彩角色参考图裁出"头肩特写"，作为 H3 ref_images 面容锚定输入。 |
| `face_crop_shot15plus.py` | shot15+ 面容参考图裁切：从 8 张定稿设计稿的最左正面视图裁头肩。 |
| `gen_c14_tpose.py` | C14 工友叔叔 T-pose 单视图（水彩，参照 C05_v08 的做法，auto-rig 用）。 |
| `gen_c15_design.py` | C15 周远 三视图设计稿（水彩，对齐 C05_v07 版式：front/side/back + 右侧圆形色板）。 |
| `gen_c15_tpose.py` | C15 周远 写实 T-pose 单视图（auto-rig 用）。 |
| `gen_e06_bus.py` | E06 长途大巴车内参考图（写实风格，给 H3 当空间/质感锚；不做 Lux3D 重建，车内程序化）。 |
| `gen_e06e07_watercolor.py` | E06 大巴车内 / E07 宿舍夜景：重画为水彩版（与影片 freedom 风格同源，替代写实版当 H3 锚）。 |
| `gen_e07_dorm.py` | E07 大学宿舍夜景参考图（写实，H3 Picture 空间锚；宿舍不做 Lux3D 重建，程序化）。 |
| `gen_e08_room.py` | E08 朝北出租屋：水彩版环境参考图（freedom 风格，H3 Picture 锚）。 |
| `gen_e09_table.py` | E09 朝北出租屋：水彩版环境参考图（freedom 风格，H3 Picture 锚）。 |
| `gen_e10_kitchen.py` | E10 出租屋厨房：水彩版环境参考图（与 E09 同一套朝北出租屋，H3 Picture 锚）。 |
| `gen_p02_photo.py` | P02 老照片（道具图，非 Lux3D 资产）：爸爸和工友们围矮桌吃饭的照片内容。 |
| `gen_ref_c18_head.py` | 重绘 C18 周远·老年 的水彩头肩面容图（shot19 / shot23 第三张 ref_image）。 |
| `gen_ref_shot15plus.py` | shot15+ 参考图生成：4 张场景 + 3 张角色设计稿，全部锁定水彩概念动画风格。 |
| `gen_ref_shot18.py` | shot18 婴儿水彩头肩参考图（C20 半岁女儿）。 |
| `gen_tpose_shot15plus.py` | shot15+ 建模输入：8 个独立角色的严格 T-pose 单视图。 |
| `glb_inspect.py` | Inspect GLB files: meshes, triangles, materials, textures, bounding bo |
| `lux3d.py` | Lux3D CLI 启动器：从注册表读取 LUX3D_CN_API_KEY 后转调官方运行时。 |
| `lux3d_fetch.py` | Download Lux3D task result files (GLB/ZIP) to assets/models/. |
| `lux3d_upload.py` | Upload local files to Aholo Lux3D through the unified Asset/OUS chain. |
| `probe_actions.py` | bpy.ops.object.select_all(action="SELECT") |
| `probe_arm_axis.py` | 探针：C05 手臂绕 (0,1,0) ±90 后的手部位世界坐标，判定收臂/抬臂符号。 |
| `probe_assets_shot06.py` | 探针：实测 E04 站台 / C05 / C10 v08 的包围盒与关键尺寸。 |
| `probe_boundaries.py` | def dark_runs(path): |
| `probe_c05_arm12.py` | 探针：C05 tex_mesh_v08_animated 手臂/脊柱世界轴实测。 |
| `probe_c05_debris.py` | 定位 C05 模型里绑在脚骨上的碎部件（走路时甩到脚下的板条）。 |
| `probe_c05_foot_parts.py` | 列 C05 rest 姿势脚部高度（local z<-0.6）的全部松散部件。 |
| `probe_c14_arm.py` | 探针：C14 手臂轴向实测（抬臂/前伸/侧举的世界轴与符号）。 |
| `probe_c14_arm_anim.py` | 探针：C14 手臂轴向实测（抬臂/前伸/侧举的世界轴与符号）。 |
| `probe_c15_axis.py` | 探针：C15 周远 骨轴实测（auto-rig 骨架，勿假设与 C05 一致）。 |
| `probe_e02.py` | Probe E02 scaled ward model: vertex binned stats to locate mattress to |
| `probe_e02b.py` | Probe E02: vertex z (up) binned stats to locate mattress surface. |
| `probe_e02c.py` | ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) |
| `probe_e03_bbox.py` | 探针：打印 E03 卧室各网格的世界包围盒，校准床沿坐标。 |
| `probe_e03_bed.py` | ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) |
| `probe_e03_bins.py` | ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) |
| `probe_e03_topview.py` | 探针：E03 顶视 + 正视正交渲染，标出角色坐姿参考点，校准床沿。 |
| `probe_e04_topview.py` | 探针：E04 缩放后顶视/侧视渲染，确定站台面高度、列车门、雨棚位置。 |
| `probe_e05.py` | 探针：E05 原始尺寸 bbox 打印 + 顶视/正视渲染，判断重建出了哪些结构。 |
| `probe_f100_slab.py` | 在 previs_shot14 的 f100 场景里定位许宁脚下残留的贴地面片。 |
| `probe_feet_shot.py` | 渲染 C05 走路姿势的脚部特写，直接看滑雪板是什么。 |
| `probe_head_turn.py` | 探针：许宁坐姿，头部分别转 +28 / -28 度，对比哪边朝向车窗（+x）。 |
| `probe_labeled.py` | v05 = iio.imread("assets/h3_video/roughcut_v05.mp4", index=None) |
| `probe_pose05.py` | 探针：导入 C01/C09，分别套用 shot05 / shot04 姿态，打印关键骨骼世界坐标。 |
| `probe_pose07.py` | 探针：预演循环复现——animated glb + 切 idle + 剥通道 + frame_set + 手动赋值，打印手部位置。 |
| `probe_rig_shot06.py` | 探针：C05/C10 v08 rigged 骨架结构（骨骼命名、髋/头世界坐标、动画列表）。 |
| `probe_shot10_scene.py` | 探针：导入 shot10 场景 + C05 坐姿，从高处俯瞰渲染一张，打印关键坐标。 |
| `probe_skis.py` | 在动画姿势下找贴地大面片：求值后的网格里，世界 z<0.06 且面积>0.015 的面。 |
| `probe_skis2.py` | 在 rest 姿势的 C05 网格里找鞋印轮廓之外的贴地平面片（滑雪板候选）。 |
| `probe_unweighted.py` | 查 C05/C15 网格里零权重（未绑骨）的面——rest 姿势原地不动、脚一动就拖地的碎片。 |
| `probe_v05.py` | v05 = iio.imread("assets/h3_video/roughcut_v05.mp4", index=None) |
| `probe_v06_labeled.py` | v06 = iio.imread("assets/h3_video/roughcut_v06.mp4", index=None) |
| `probe_xu_frames.py` | 探针2：复现预演场景——C05 rot=180 + setup_xu 关键帧，frame_set 后看手部是否被覆盖。 |
| `rebuild_c11.py` | C11 重建：用 C11_tpose_v02.png（横版、双手完整）替换被裁切的 v01。 |
| `recover_mesh_shot15plus.py` | 取回 7 个「服务端已成功、本地下载失败」的 image-to-3d 产物。 |
| `render_e02_once.py` | Render QC views of Lux3D GLB models with local Blender (headless). |
| `render_e03_once.py` | Render QC views of Lux3D GLB models with local Blender (headless). |
| `render_progress_models.py` | 为比赛过程资料补渲染缺失的 Lux3D 模型四视图，直接输出到 progress/ 目录。 |
| `rig_inspect.py` | Inspect rigged GLB: bones, skin weights, dimensions. |
| `rig_qc.py` | QC rigged GLB models: rest-pose renders + a skinning deformation test. |

## Blender 白模预演 · 45 个

逐镜相机调度、动作链、渲染与预演帧打包

| 脚本 | 说明 |
| --- | --- |
| `blender_render.py` | Render QC views of Lux3D GLB models with local Blender (headless). |
| `make_previs09.py` | shot09 预演：P02 老照片的缓慢推近（Ken Burns），推向爸爸（画面右侧）。 |
| `pack_previs08.py` | d = "assets/previs/frames08 |
| `pack_previs10.py` | d = "assets/previs/frames10 |
| `pack_previs11.py` | d = "assets/previs/frames11 |
| `pack_previs14.py` | d = "assets/previs/frames14 |
| `pack_previs18.py` | 把 frames18 的 192 张 PNG 合成 assets/previs/previs_shot18.mp4。 |
| `pack_previs19.py` | 把 frames19 的 192 张 PNG 合成 assets/previs/previs_shot19.mp4。 |
| `pack_previs20.py` | 把 assets/previs/frames20 的 192 张 PNG 合成 assets/previs/previs_shot20.mp |
| `pack_previs21.py` | 把 assets/previs/frames21 的 192 张 PNG 合成 assets/previs/previs_shot21.mp |
| `pack_previs22.py` | 把 assets/previs/frames22 的 192 张 PNG 合成 assets/previs/previs_shot22.mp |
| `pack_previs23.py` | 把 assets/previs/frames23 的 192 张 PNG 合成 assets/previs/previs_shot23.mp |
| `pack_previs24.py` | shot24 预演 192 PNG → previs_shot24.mp4 + 规格校验 + ComfyUI input 登记。 |
| `pack_previs25.py` | shot25 预演 192 PNG → previs_shot25.mp4 + 规格校验 + ComfyUI input 登记。 |
| `pack_previs26.py` | shot26 预演 192 PNG → previs_shot26.mp4 + 规格校验 + ComfyUI input 登记。 |
| `pack_previs27.py` | shot27 预演 192 PNG → previs_shot27.mp4 + 规格校验 + ComfyUI input 登记。 |
| `previs_shot.py` | 白模预演：老厂区楼道口 · 结尾幻觉镜头（Blender 相机调度）。 |
| `previs_shot01_v2.py` | 白模预演 v2：老厂区楼道口 · 结尾幻觉镜头（shot01 重做）。 |
| `previs_shot02.py` | 白模预演：老厂区楼道口 · shot02「姥姥给许宁别上红发带」双人近景（Blender 相机调度）。 |
| `previs_shot03.py` | 白模预演：县医院病房 · shot03「许宁踮脚捧住姥姥的手」双人近景（Blender 相机调度）。 |
| `previs_shot04.py` | 白模预演：家中卧室镜前 · shot04「妈妈给许宁扎辫子」双人侧景（Blender 相机调度）。 |
| `previs_shot05.py` | 白模预演：家中卧室 · shot05「清晨枕下发带」双人床沿（Blender 相机调度）。 |
| `previs_shot06.py` | 白模预演：火车站 shot06「站台送别」（Blender 相机调度 + 走动动画）。 |
| `previs_shot07.py` | 白模预演：南方街道 shot07「找爸爸的工友」（Blender 相机调度 + 走动/指向动画）。 |
| `previs_shot08.py` | 白模预演：南方街道 shot08「老照片」（叔叔掏手机给许宁看）。 |
| `previs_shot10.py` | 白模预演：shot10「返校的车上」（大巴车内，许宁看照片又望窗外）。 |
| `previs_shot11.py` | 白模预演：shot11「夜里的电话」（宿舍夜戏，许宁贴窗站着打电话）。 |
| `previs_shot12.py` | 白模预演：shot12「晒书的人」（第五章定场，朝北小屋，许宁抱书到窗前）。 |
| `previs_shot13.py` | 白模预演：shot13「两只碗」（第五章，许宁摆第二只碗，周远不出镜）。 |
| `previs_shot14.py` | 白模预演：shot14「厨房的和好」（剧本五 L251-267）。 |
| `previs_shot15.py` | 白模预演：shot15「再攒两年」（剧本五 L269-275）。 |
| `previs_shot16.py` | 白模预演：shot16「婚礼·胸针与旧发带」（剧本五 L277-283）。 |
| `previs_shot16b.py` | 白模预演【v03】：shot16「婚礼·胸针与旧发带」（剧本五 L277-283）。 |
| `previs_shot17.py` | 白模预演：shot17「我自己来」（剧本六 L285-303，方案 §4）。 |
| `previs_shot17b.py` | 白模预演：shot17b「我自己来」v5 返修版（剧本六 L285-303，方案 §4）。 |
| `previs_shot18.py` | 白模预演：shot18「楼下晨光·婴儿车」（剧本五 L305-311，方案 §4）。 |
| `previs_shot19.py` | 白模预演：shot19「报纸后面」（剧本六 L315-319，方案 §4）。 |
| `previs_shot20.py` | 白模预演：shot20「妈，你晚上吃什么」（剧本六 L321-325，方案 §4）。 |
| `previs_shot21.py` | 白模预演：shot21「一袋橘子」（剧本六 L327-337，方案 §4）。 |
| `previs_shot22.py` | 白模预演：shot22「阳台择豆角」（剧本六 L339-351，方案 §3 §4，P0）。 |
| `previs_shot23.py` | 白模预演：shot23「地址纸与盒子」（剧本六 L353-359 / 方案 §3 §4，P0）。 |
| `previs_shot24.py` | shot24「两碗面」Blender 哑光白模预演（192 帧 / 1280×720 / 24fps）。 |
| `previs_shot25.py` | shot25「病房·跳舞之约」Blender 哑光白模预演（192 帧 / 1280×720 / 24fps）。 |
| `previs_shot26.py` | shot26「跳一点给外婆看」Blender 哑光白模预演（192 帧 / 1280×720 / 24fps）。 |
| `previs_shot27.py` | shot27「幕布拉开」Blender 哑光白模预演（192 帧 / 1280×720 / 24fps）。 |

## 剪辑与粗剪 · 7 个

逐版粗剪、叠化与声桥、白模 × 成片对比片

| 脚本 | 说明 |
| --- | --- |
| `build_previs_compare.py` | 《我们总要学会告别，并在告别中成长》 |
| `roughcut_v04.py` | 粗剪 v0.4 = v0.3（开头版本卡换 v0.4、尾部冻结裁短）+ 过场卡「第二天清晨」+ shot05。 |
| `roughcut_v05.py` | 粗剪 v0.5 = v0.4 + 过场卡「火车站」+ shot06 火车站送别。 |
| `roughcut_v06.py` | 粗剪 v0.6 = v0.5 + 过场卡「大二暑假」+ shot07 找爸爸的工友（南方线）。 |
| `roughcut_v07.py` | 全片粗剪 v0.7：27 镜成片按镜号顺序硬切拼接，无配乐、无字幕卡、无转场。 |
| `roughcut_v08.py` | 粗剪 v0.8 = v0.7 + 观聆评审意见 1/4/5 的结构性返修（仍无配乐）。 |
| `roughcut_v09.py` | 粗剪 v0.9 = v0.8 + 用户拍板「片尾留白放宽到 3.0s」（总长 216.0 → 217.5s）。 |

## 质检与归档 · 14 个

逐帧数值检查、联系表、判定书与六类归档索引

| 脚本 | 说明 |
| --- | --- |
| `build_progress.py` | 整理比赛过程资料到 progress/（分类：剧本/角色/场景/预演/成片/质检） |
| `qc_allframes.py` | 逐帧审查：把成片全部 192 帧拼成 8 张 24 格 contact sheet（每格带帧号）。 |
| `qc_c15_anim.py` | C15 动画 QC：分别截取 4 个动画的中段帧渲染。 |
| `qc_final_stats.py` | 成片程序化质检：亮度 / 突变帧 / 帧间差 / 每 24 帧亮度 / 首中末平均 RGB。 |
| `qc_frame_check.py` | Check QC renders: report the model's pixel bbox with noise tolerance. |
| `qc_previs08.py` | d = "assets/previs/frames08 |
| `qc_previs10.py` | d = "assets/previs/frames10 |
| `qc_previs11.py` | d = "assets/previs/frames11 |
| `qc_shot07.py` | frames = iio.imread("assets/h3_video/shot07_h3.mp4", index=None) |
| `qc_shot07b.py` | frames = iio.imread("assets/h3_video/shot07_h3.mp4", index=None) |
| `qc_shot08.py` | frames = iio.imread("assets/h3_video/shot08_h3.mp4", index=None) |
| `qc_shot08b.py` | frames = iio.imread("assets/h3_video/shot08_h3.mp4", index=None) |
| `qc_shot09.py` | frames = iio.imread("assets/h3_video/shot09_h3.mp4", index=None) |
| `qc_v06.py` | frames = iio.imread("assets/h3_video/roughcut_v06.mp4", index=None) |

## 生成工作流参数 · 17 个

逐镜 prompt / seed / 参考图与 ComfyUI 工作流 JSON

| 脚本 | 说明 |
| --- | --- |
| `make_h3_workflow_shot15.py` | 以 shot14 工作流为底生成 shot15 的 MiniMax H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot16.py` | 以 shot15 工作流为底生成 shot16 的 MiniMax H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot16b.py` | shot16 v02：重写发带段，修复 v01「旧发带没放进小包」的阻断问题。 |
| `make_h3_workflow_shot16c.py` | shot16 v03：只换白模预演参考视频，验证「运动通道缺失」这一根因。 |
| `make_h3_workflow_shot17.py` | 以 shot15 工作流为底生成 shot17「我自己来」的 MiniMax H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot18.py` | 以 shot15 工作流为底生成 shot18「楼下晨光·婴儿车」的 MiniMax H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot19.py` | 以 shot15 工作流为底生成 shot19「报纸后面」的 MiniMax H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot20.py` | 生成 shot20「妈，你晚上吃什么」的 H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot21.py` | 以 shot19 工作流为底生成 shot21「一袋橘子」的 MiniMax H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot22.py` | 以 shot21 工作流为底生成 shot22「阳台择豆角」的 MiniMax H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot23.py` | 以 shot22 工作流为底生成 shot23「地址纸与盒子」的 MiniMax H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot24.py` | 以 shot20 的 16 节点工作流为底生成 shot24「两碗面」的 MiniMax H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot25.py` | 以 shot23 的 17 节点工作流为底生成 shot25「病房·跳舞之约」的 18 节点 H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot26.py` | 以 shot25 的 18 节点工作流为底生成 shot26「跳一点给外婆看」的 H3 Ref2VA 工作流。 |
| `make_h3_workflow_shot27.py` | 以 shot23 工作流为底生成 shot27「幕布拉开」的 MiniMax H3 Ref2VA 工作流。 |
| `submit_h3.py` | 通用 H3 Ref2VA 提交器：校验输入素材 → 检查队列 → POST /prompt → 全程留痕。 |
| `wait_h3.py` | 等待 ComfyUI 的 H3 Ref2VA 任务完成，并打印输出文件名。 |
