"""测试照片上传接口"""
import io
import json
import subprocess
import sys
import time
import urllib.request

# 构造一个假的 JPEG 文件
jpg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9"

proc = subprocess.Popen(
    [sys.executable, r"C:/Users/luyicheng/Desktop/3dscanner/scripts/upload_server.py", "--port", "8124"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
)
time.sleep(1.5)

# multipart/form-data 上传
boundary = "----TestBoundary123"
body = io.BytesIO()
for name in ["photo1.jpg", "photo2.png", "note.txt"]:
    body.write(f"--{boundary}\r\n".encode())
    body.write(f'Content-Disposition: form-data; name="files"; filename="{name}"\r\n'.encode())
    body.write(b"Content-Type: application/octet-stream\r\n\r\n")
    body.write(jpg_bytes)
    body.write(b"\r\n")
body.write(f"--{boundary}--\r\n".encode())
data = body.getvalue()

req = urllib.request.Request(
    "http://127.0.0.1:8124/upload", data=data, method="POST",
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
try:
    with urllib.request.urlopen(req, timeout=5) as r:
        resp = json.loads(r.read().decode("utf-8"))
    print("上传响应:", resp)
    assert resp["saved"] == 2, "应保存 2 张图片"
    assert resp["skipped"] == 1, "应跳过 1 个非图片"
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code, e.read().decode("utf-8", errors="ignore")[:500])
    proc.kill()
    sys.exit(1)

proc.kill()
print("UPLOAD TEST PASSED")
