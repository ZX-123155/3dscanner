"""删除 pip cache 内容（可再生成的下载缓存，非个人文件）"""
from pathlib import Path
from loguru import logger

cache = Path(r"C:/Users/luyicheng/AppData/Local/pip/cache")
removed = failed = 0
for f in cache.rglob("*"):
    if f.is_file():
        try:
            f.unlink()
            removed += 1
        except Exception as e:
            failed += 1
logger.info(f"pip cache 删除: 成功 {removed}, 失败 {failed}")
# 清理空的子目录
for d in sorted(cache.rglob("*"), key=lambda p: len(p.parts), reverse=True):
    if d.is_dir():
        try:
            d.rmdir()
        except OSError:
            pass
logger.info(f"剩余大小: {sum(f.stat().st_size for f in cache.rglob('*') if f.is_file()) / 1e6:.1f} MB")
