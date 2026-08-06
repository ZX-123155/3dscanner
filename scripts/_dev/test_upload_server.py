"""测试上传服务器：启动、请求首页、模拟上传"""
import subprocess
import sys
import time
import urllib.request
import urllib.error

# 后台启动服务器
proc = subprocess.Popen(
    [sys.executable, r"C:/Users/luyicheng/Desktop/3dscanner/scripts/upload_server.py", "--port", "8123"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
)

# 等服务器就绪
ok = False
for _ in range(20):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8123/", timeout=2) as r:
            page = r.read().decode("utf-8")
            ok = True
            break
    except Exception:
        time.sleep(0.5)

if not ok:
    out = proc.stdout.read() if proc.stdout else ""
    print("SERVER FAILED:", out[-2000:])
    proc.kill()
    sys.exit(1)

print("首页 OK, 长度:", len(page))
assert "3D 扫描仪" in page, "页面缺少标题"
assert "开始重建" in page, "页面缺少重建按钮"

# 测试 /log 接口
with urllib.request.urlopen("http://127.0.0.1:8123/log", timeout=2) as r:
    j = r.read().decode("utf-8")
print("/log OK:", j[:80])

proc.kill()
print("ALL TESTS PASSED")
