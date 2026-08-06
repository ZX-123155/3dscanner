"""验证子进程中文输出编码"""
import subprocess, os
env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
env["PYTHONUTF8"] = "1"
r = subprocess.run(
    [r"C:/Users/luyicheng/miniconda3/envs/3dscanner/python.exe", "-c",
     "from loguru import logger; logger.info('测试中文日志：COLMAP 模型 108 图'); print('普通 print 中文')"],
    capture_output=True, text=True, encoding="utf-8", env=env)
print("STDOUT:", r.stdout)
print("STDERR:", r.stderr)
print("OK ✅" if "测试中文" in r.stdout else "❌ 中文仍乱码")
