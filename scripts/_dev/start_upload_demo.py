"""演示：启动上传服务器并打印局域网地址"""
import subprocess
import sys
import time
import urllib.request

proc = subprocess.Popen(
    [sys.executable, r"C:/Users/luyicheng/Desktop/3dscanner/scripts/upload_server.py", "--port", "8000"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
)
time.sleep(2)

# 验证可访问
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/", timeout=3) as r:
        print("服务器在 8000 端口运行正常，页面:", r.status)
except Exception as e:
    print("服务器未启动:", e)
    out = proc.stdout.read() if proc.stdout else ""
    print(out[-1000:])
    proc.kill()
    sys.exit(1)

proc.kill()
print("验证完成")
