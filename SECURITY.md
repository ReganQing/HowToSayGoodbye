# 安全与凭据策略 / Security & Credentials

> 本文件说明 `HowToSayGoodbye` 公开仓库在上传前做了哪些清理，以及使用者需要自行配置什么。
> This document describes what was sanitised before publishing and what you must configure yourself.

## 1. 结论 / Summary

**仓库内不含任何明文凭据、令牌、邮箱、手机号或本地绝对路径。**
**No plaintext credentials, tokens, email addresses, phone numbers or local absolute paths are present.**

组装脚本 `tools/build_github_repo.py`（仅在本地运行，不随仓库发布）在复制阶段执行了 **8 项全量扫描**，并对 **41 处**硬编码本地路径做了可移植化替换。二次扫描对最终待推送目录重新执行同样检查，全部为 0 命中。

## 2. 扫描项与结果 / Checks and results

| # | 检查项 / Check | 命中 / Hits |
| --- | --- | ---: |
| 1 | `sk-` / `ms-` 样式明文密钥 | 0 |
| 2 | 硬编码 `Bearer` 令牌 | 0 |
| 3 | 键值型凭据赋值（`api_key=...` / `token=...` / `secret=...`） | 0 |
| 4 | 明文 oauth2 令牌 URL | 0 |
| 5 | 邮箱地址 | 0 |
| 6 | 中国大陆手机号 | 0 |
| 7 | 本地绝对路径（Windows 盘符形式） | 0 |
| 8 | 外部项目绝对路径引用 | 0 |

路径脱敏规则（为避免文档自身触发扫描，下表用占位符表示原路径形态）：

| 原始形态 | 处理后 |
| --- | --- |
| `<PROJECT_ROOT>`（原为盘符绝对路径常量） | `.`（项目根，脚本默认在此执行） |
| `<PROJECT_ROOT>/assets/ref/C14/...` | `assets/ref/C14/...` |
| `.../ffmpeg.exe` | `ffmpeg`（走 `PATH`） |
| `.../python.exe` | `python` |
| 外部风格规范文档路径（注释中的引用，含空格） | `<EXTERNAL_REF: 风格规范.md>` |

脱敏后对全部 160 个 `.py` 做了语法编译检查，**0 个语法错误**。

## 3. 主动排除的内容 / Deliberately excluded

| 内容 | 排除原因 |
| --- | --- |
| `deploy_modelscope_studio.py`、`sync_modelscope_studio.py` | 部署工具，含令牌化 git URL 拼接逻辑；与建模 / Blender / 剪辑无关 |
| `build_studio_demo.py`、`build_xhs_note.py`、`build_report.py` | 文档与传播物料生成工具，不属于本次收录范围 |
| `tools/aholo-lux3d-ref/`（第三方参考包） | 内含**示例密钥字符串**与独立第三方许可，48+ 文件；整体排除 |
| `__pycache__/`、`*.pyc`、`*.zip` | 编译缓存与二进制包 |
| `assets/`、`progress/`、`output/`、`tmp_qc/`、`*.mp4`、`*.glb` | 大体量素材与成片（合计 12+ GB），只在本地保存 |

## 4. 需要你自行配置的凭据 / Credentials you provide

仓库内部分脚本会访问云端或本地服务，**凭据一律从环境变量或本机凭据存储读取**，代码中不含任何值：

| 环境变量名 | 用途 | 是否必需 |
| --- | --- | --- |
| `LUX3D_CN_API_KEY` | Lux3D 云端建模 / 绑骨 / 重定向（`lux3d*.py`、`build_models_shot15plus.py`） | 仅建模类脚本 |
| `PREVIS_RANGE`、`PREVIS_TEST` | Blender 白模预演的帧范围与测试开关 | 可选 |
| 本地 ComfyUI `127.0.0.1:8188` | H3 Ref2VA 生成（`submit_h3.py` / `wait_h3.py`） | 仅生成类脚本，无需密钥 |

> 部署到魔搭创空间使用的 `MODELSCOPE_API_KEY` 仅存在于本机的部署脚本中，该脚本**未**进入本仓库。

**请勿**把 `.env`、`*.key`、`*.pem` 或任何凭据文件提交进来；`.gitignore` 已配置拦截规则。

## 5. 自行复核 / Verify yourself

```bash
git clone https://github.com/ReganQing/HowToSayGoodbye.git
cd HowToSayGoodbye

# 简化版密钥扫描（完整模式定义见本地组装脚本）
grep -rInE 'sk-[A-Za-z0-9_-]{16,}|ms-[A-Za-z0-9]{20,}' . || echo "clean"

# 本地盘符路径扫描
grep -rInE '[A-Za-z]:[\\/](Projects|Users|Softwares|ProgramData)' . || echo "clean"
```

## 6. 发现问题 / Reporting

如发现任何疑似凭据或隐私信息，请通过 GitHub 私信或 Issue 联系仓库所有者，不要公开粘贴具体内容。

If you spot anything that looks like a leaked credential, please contact the repository owner privately rather than posting it in a public issue.
