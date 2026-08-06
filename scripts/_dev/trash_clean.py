"""将指定的缓存/残留/废弃环境移动到回收站（可恢复）

处理:
  1. AppData/Local/Temp/pip-unpack-*  pip 安装残留的临时解压目录
  2. AppData/Local/pip/cache            pip 下载缓存
  3. miniconda3/pkgs/*.conda_trash     conda 删除残留
  4. miniconda3/envs/3dscanner_old     废弃的 conda 环境

用法: python _dev/trash_clean.py
"""
import sys
from pathlib import Path

from loguru import logger
from send2trash import send2trash

USER_HOME = Path.home()
TARGETS = {
    "pip_unpack": list((USER_HOME / "AppData/Local/Temp").glob("pip-unpack-*")),
    "pip_cache": [USER_HOME / "AppData/Local/pip/cache"] if (USER_HOME / "AppData/Local/pip/cache").exists() else [],
    "conda_trash": list((USER_HOME / "miniconda3/pkgs").glob("*.conda_trash")),
    "env_old": [USER_HOME / "miniconda3/envs/3dscanner_old"] if (USER_HOME / "miniconda3/envs/3dscanner_old").exists() else [],
}


def main():
    total_moved = 0
    total_failed = 0
    for label, items in TARGETS.items():
        logger.info(f"[{label}] 待清理 {len(items)} 项")
        moved = failed = 0
        for item in items:
            try:
                send2trash(str(item))
                moved += 1
            except Exception as e:  # noqa: BLE001
                failed += 1
                logger.error(f"失败: {item} -> {e}")
        total_moved += moved
        total_failed += failed
        logger.info(f"[{label}] 完成: 移动 {moved} 项, 失败 {failed} 项")
    logger.info(f"全部完成: 移动 {total_moved} 项, 失败 {total_failed} 项")


if __name__ == "__main__":
    main()
