"""逐文件移动 pip cache 到回收站"""
from pathlib import Path
from loguru import logger
from send2trash import send2trash

cache = Path(r"C:/Users/luyicheng/AppData/Local/pip/cache")
files = [f for f in cache.rglob("*") if f.is_file()]
moved = failed = 0
for f in files:
    try:
        send2trash(str(f))
        moved += 1
    except Exception as e:
        failed += 1
        if failed <= 5:
            logger.error(f"失败: {f} -> {e}")
logger.info(f"pip cache 逐文件清理: 成功 {moved}, 失败 {failed}")
