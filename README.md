<div align="center">

# HowToSayGoodbye

**27 镜水彩 AI 动画短片《我们总要学会告别，并在告别中成长》· 创作脚本集**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Blender](https://img.shields.io/badge/Blender-4.x-F5792A?logo=blender&logoColor=white)](https://www.blender.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-7.x-007808?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Scripts](https://img.shields.io/badge/Scripts-148-26364F)](#脚本地图)
[![No Credentials](https://img.shields.io/badge/Credentials-none-brightgreen)](SECURITY.md)
[![Version](https://img.shields.io/badge/Version-Demo%20V1.0-C9A227)](#版本与出处)

[简体中文](README.md) · [English](README.en.md) · [在线报告书](https://ron567-howtosaygoodbye.ms.show/) · [魔搭创空间](https://modelscope.cn/studios/Ron567/HowtoSayGoodbye)

</div>

---

> **本仓库收录的，是把「不可控」拆成可验收工程的那部分代码。**
> 它不是成片，也不是一键复现的成品工具包，而是一次真实创作留下的 148 个脚本、41 份逐镜工作流参数与完整的返修路径。所有内容按 **Demo V1.0** 正式提交版整理。

## 目录

| | |
| --- | --- |
| [项目背景](#项目背景) · [流水线总览](#流水线总览) · [脚本地图](#脚本地图) | [快速开始](#快速开始) · [目录结构](#目录结构) |
| [数据与素材](#数据与素材) · [安全与凭据](#安全与凭据) | [版本与出处](#版本与出处) · [许可](#许可) |

## 项目背景

《我们总要学会告别，并在告别中成长》是一部长 **3 分 36 秒**的水彩概念动画短片。一条末端绣白花的红发带贯穿三代人：姥姥买下的旧带 → 婚礼上叠好放进小包 → 与地址纸一起收进遗物盒 → 病房里交代给女儿 → 舞台上换成一对无白花的新带系到辫梢。道具自己完成叙事，不靠台词解释。

| 指标 | 数值 |
| --- | --- |
| 镜头 / 时长 | 27 镜 × 8.0s = **216.0 秒** |
| 帧数 / 规格 | 5184 帧 · 1280×720 · 24fps · H.264 |
| 叙事结构 | 七段落，来自约 9.6 千字的七章文学剧本 |
| 质检留痕 | 28 份 `qc_report.json`（预演 14 / 成片 14），14 份成片报告全 pass |
| 过程归档 | `progress/` 下 6973 个过程文件，按六类归档 |
| 后期收敛 | shot17–shot27 连续 11 镜，H3 一次提交过审 |

## 流水线总览

```mermaid
flowchart LR
    A["文学剧本<br/>9.6 千字 / 七章"] --> B["分镜与参考图<br/>gen_* / 资产台账"]
    B --> C["3D 建模<br/>Lux3D / build_models_*"]
    C --> D["Blender 白模预演<br/>previs_shot*"]
    D --> E["逐帧 QC<br/>qc_* / 联系表"]
    E --> F["AI 生成<br/>ComfyUI H3 / submit_h3"]
    F --> G["成片质检<br/>判定书 / 返修"]
    G --> H["剪辑与粗剪<br/>roughcut_v0.4 → v0.9"]
    H --> I["六类归档<br/>build_progress"]

    style D fill:#e8eef5,stroke:#334b6b,stroke-width:2px
    style E fill:#fdf0e3,stroke:#c0453b,stroke-width:2px
    style H fill:#e8eef5,stroke:#334b6b,stroke-width:2px
```

**全片画风不漂移的关键：三通道分离。**

| 通道 | 锁定内容 | 不承担的任务 |
| --- | --- | --- |
| 文字提示词 | 光照、画风、纸感 | 大幅位移动作 |
| 水彩参考图 | 布局、人物长相 | 画风锚（写实 T-pose 不得混入） |
| 白模预演视频 | 运动拓扑、道具物理链 | 最终画面质感 |

> 绝大多数返修不是模型不听话，而是提交生成之前没把动作讲清楚。shot16「旧发带放进小包」返修三版、shot17「手机贴手」白模返修六轮，最终都靠先修预演解决，而不是加长 prompt。

## 脚本地图

所有脚本保持项目内**原始文件名与平铺结构**，放在 [`tools/`](tools/) 下；按文件名前缀区分类别。完整逐文件索引见 [`docs/SCRIPTS_INDEX.md`](docs/SCRIPTS_INDEX.md)。

| 类别 | 数量 | 前缀 / 代表脚本 | 作用 |
| --- | ---: | --- | --- |
| **建模与资产生成** | 65 | `gen_*`、`build_models_shot15plus.py`、`probe_*`、`rig_*`、`lux3d_*`、`comfy_ref_gen.py` | 水彩参考图与 T-pose 生成、Lux3D 建模 / 绑骨 / 重定向流水线、骨骼探针与 GLB 检查 |
| **Blender 白模预演** | 45 | `previs_shot*.py`、`blender_render.py`、`pack_previs*.py`、`make_previs09.py` | 逐镜相机调度与动作链、四视图渲染、预演帧打包 |
| **剪辑与粗剪** | 7 | `roughcut_v04.py` → `roughcut_v09.py`、`build_previs_compare.py` | 逐版叠化与声桥、片尾定格、白模 × 成片 1:1 对比片 |
| **质检与归档** | 14 | `qc_allframes.py`、`qc_final_stats.py`、`anim_qc.py`、`build_progress.py` | 每镜 192 帧全覆盖数值检查、联系表、判定书、六类归档索引 |
| **生成工作流参数** | 17 | `make_h3_workflow_*.py`、`submit_h3.py`、`wait_h3.py` | 逐镜 prompt / seed / 参考图映射、ComfyUI 单次提交与轮询 |

<details>
<summary><b>为什么保持平铺而不拆目录？</b></summary>

15 个 `previs_shot*.py` 会 `import previs_shot14`，`roughcut_v09.py` 复用 v0.8 的分步叠化流程，建模脚本之间也互相引用台账与辅助函数。重排目录会让这些相对引用失效。因此仓库选择「原样平铺 + 前缀分类 + 索引文档」，优先保证可读性与可追溯性。

</details>

## 快速开始

### 环境要求

| 依赖 | 用途 | 是否必需 |
| --- | --- | --- |
| Python 3.12+ | 全部脚本运行时 | ✅ 必需 |
| Pillow / NumPy / imageio | 联系表、抽帧、裁切 | ✅ 必需 |
| Blender 4.x（命令行） | `bpy` 白模预演与四视图渲染 | 仅 Blender 类脚本 |
| FFmpeg / ffprobe | 粗剪、叠化、对比片、数值探测 | 仅剪辑 / QC 类脚本 |
| ComfyUI（本地 `127.0.0.1:8188`） | H3 Ref2VA 生成 | 仅生成类脚本 |
| Lux3D API 凭据 | 云端建模 / 绑骨 | 仅建模类脚本，见 [SECURITY.md](SECURITY.md) |

### 命令示例

> 所有脚本默认**在项目根目录执行**。仓库内硬编码的本地绝对路径已统一改为相对路径，`FFMPEG` / `blender` 等可执行文件走 `PATH` 或自行配置。

```bash
# 1. 生成水彩参考图 / T-pose
python tools/gen_c14_tpose.py

# 2. 建模流水线（可续跑，付费任务绝不重复提交）
python tools/build_models_shot15plus.py --only C06
python tools/build_models_shot15plus.py --resume

# 3. Blender 白模预演（1280×720 / 24fps / 192 帧）
blender --background --python tools/previs_shot16b.py

# 4. 逐帧质检
python tools/qc_allframes.py

# 5. 粗剪 v0.9（27 镜 / 217.5s / 片尾 3.0s 定格）
python tools/roughcut_v09.py

# 6. 白模 × 成片 逐镜 1:1 对比片
python tools/build_previs_compare.py
```

## 目录结构

```text
HowToSayGoodbye/
├── README.md                     # 简体中文（本文件）
├── README.en.md                  # English
├── SECURITY.md                   # 凭据策略与扫描结果
├── .gitignore                    # 拦截密钥、素材、缓存
├── docs/
│   ├── SCRIPTS_INDEX.md          # 148 个脚本的完整分类索引
│   └── manifest.json             # 文件数 / 分类 / 脱敏统计
└── tools/                        # 原始平铺结构
    ├── gen_*.py                  # 参考图与资产生成
    ├── previs_shot*.py           # Blender 白模预演
    ├── roughcut_v0*.py           # 逐版粗剪
    ├── qc_*.py                   # 逐帧质检
    ├── h3_r2v_workflow_*.json    # 41 份逐镜生成参数
    ├── contracts/                # 场景交付契约
    └── lux3d_runtime/            # 建模运行时辅助模块
```

## 数据与素材

| 内容 | 是否在本仓库 | 说明 |
| --- | --- | --- |
| 脚本与工作流参数 | ✅ 已收录 | 148 个 `.py` + 41 份 `.json` |
| 角色 / 场景 / 道具参考图 | ❌ 未收录 | 原始 `assets/` 约 7.3 GB |
| 成片与预演视频 | ❌ 未收录 | 成片 552 MB、预演 45.9 MB |
| 全量过程归档 | ❌ 未收录 | `progress/` 约 4.5 GB / 6973 个文件 |
| 精选过程证据 | 🔗 在线可查 | 创空间 `evidence/` 下 107 个文件、198 处可点出处 |

工作流 JSON 记录了每镜的 prompt、seed、模型与参考图**文件名**，足以核对参数，但不包含素材本体。若需要完整证据链，请访问[在线报告书](https://ron567-howtosaygoodbye.ms.show/)中的附录 A.4。

## 安全与凭据

**本仓库不含任何明文凭据。** 组装时执行了 8 项全量扫描，结果均为 0 命中：

| 扫描项 | 结果 |
| --- | --- |
| `sk-` / `ms-` 样式密钥、硬编码 Bearer、键值型凭据赋值、oauth2 明文 | 0 |
| 邮箱、手机号 | 0 |
| 本地绝对路径（Windows 盘符形式） | 0（已脱敏 **41** 处） |

- 凭据只通过**环境变量或本机凭据存储**注入，代码中不出现具体值；详见 [SECURITY.md](SECURITY.md)。
- 以下文件**主动排除**：部署 / 同步脚本（涉及令牌 URL 拼接）、第三方参考包 `aholo-lux3d-ref/`（含示例密钥与独立许可）、文档生成工具、缓存与二进制素材。
- `.gitignore` 额外拦截 `.env`、`*.key`、`*.pem`、凭据文件与全部素材目录。

## 版本与出处

| 项目 | 内容 |
| --- | --- |
| 版本 | **Demo V1.0**（2026-11-16 正式提交） |
| 创作过程报告书 | https://ron567-howtosaygoodbye.ms.show/ |
| 魔搭创空间 | https://modelscope.cn/studios/Ron567/HowtoSayGoodbye |
| 归档基准日 | 2026-11-15 |
| 数据口径 | `HANDOFF.md`、`progress/README.md`、粗剪时间线 v0.7 / v0.9、28 份 `qc_report.json` |

脚本是**过程留痕**，不是通用库：部分脚本为单次批处理而写，含特定镜号与项目内相对路径，复用到其他项目时需要相应调整。这一点刻意保留，因为它正是「怎么做」的证据。

## 许可

本仓库用于创作过程展示与评审核验，**未指定开源许可**（默认保留所有权利）。如需复用或二次发布，请先与作者联系。

---

<div align="center">

<sub>Built from a 9.6k-word essay, 27 shots, and every rejected version we kept.</sub>

</div>
