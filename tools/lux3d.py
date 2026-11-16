# -*- coding: utf-8 -*-
"""Lux3D CLI 启动器：从注册表读取 LUX3D_CN_API_KEY 后转调官方运行时。

用法与 lux3d_client.py 完全一致，例如：
  python tools/lux3d.py image --img <url> --version G1-Turbo --face-count 100000
  python tools/lux3d.py auto-rig --model-url <glb_url>
  python tools/lux3d.py retarget --rig-model-url <url> --animation-id Walk_Loop --animate-in-place
  python tools/lux3d.py query --task-id 4543824
  python tools/lux3d.py list

密钥读取顺序：进程 env -> HKCU\\Environment -> HKLM Session Manager\\Environment，
只进请求头，不打印不落盘。国内区（cn），对应 api.aholo3d.cn。
"""
import os
import sys
import winreg

KEY_NAME = "LUX3D_CN_API_KEY"


def load_key():
    key = os.environ.get(KEY_NAME, "").strip()
    if key:
        return key
    for hive, path in ((winreg.HKEY_CURRENT_USER, r"Environment"),
                       (winreg.HKEY_LOCAL_MACHINE,
                        r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")):
        try:
            with winreg.OpenKey(hive, path) as k:
                v, _ = winreg.QueryValueEx(k, KEY_NAME)
                if v and v.strip():
                    return v.strip()
        except OSError:
            continue
    raise SystemExit(f"{KEY_NAME} not found in process env / HKCU / HKLM")


def main():
    os.environ[KEY_NAME] = load_key()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from lux3d_runtime import lux3d_client  # noqa: E402
    lux3d_client.main()


if __name__ == "__main__":
    main()
