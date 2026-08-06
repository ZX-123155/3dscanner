"""验证修复：重名文件自动加序号 + 大批量上传"""
import io
import json
import subprocess
import sys
import time
import urllib.request

PY = r"C:\Users\luyicheng\miniconda3\envs\3dscanner\python.exe"
SERVER = r"C:\Users\luyicheng\Desktop\3dscanner\scripts\upload_server.py"
PORT = 8126
jpg = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9"

proc = subprocess.Popen([PY, SERVER, "--port", str(PORT)],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(2)


def post_files(files):
    boundary = "----WB" + str(int(time.time() * 1000))
    buf = io.BytesIO()
    for name, data in files:
        buf.write(f"--{boundary}\r\n".encode())
        buf.write(f'Content-Disposition: form-data; name="files"; filename="{name}"\r\n'.encode())
        buf.write(b"Content-Type: application/octet-stream\r\n\r\n")
        buf.write(data)
        buf.write(b"\r\n")
    buf.write(f"--{boundary}--\r\n".encode())
    body = buf.getvalue()
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/upload", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


# 测试 1: 重复文件名上传两次（验证不覆盖）
r1 = post_files([("phone_capture.jpg", jpg), ("phone_capture.jpg", jpg + b"diff")])
print("T1 重名上传:", r1)
assert r1["saved"] == 2, "应保存 2 张（不覆盖）"

# 测试 2: 模拟大批量（30 张不同毫秒时间戳）
files = [(f"1786028074{i:03d}.jpg", jpg) for i in range(30)]
r2 = post_files(files)
print(f"T2 大批量 ({len(files)} 张):", r2)
assert r2["saved"] == 30, "应保存 30 张"

# 测试 3: 验证 count
with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/count", timeout=5) as r:
    r3 = json.loads(r.read().decode())
print("T3 count:", r3)
assert r3["count"] == 32, f"应为 32 张，实际 {r3['count']}"

proc.kill()
print("ALL TESTS PASSED ✅")