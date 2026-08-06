"""验证 img_NNN 顺序命名"""
import io
import json
import subprocess
import sys
import time
import urllib.request

PY = r"C:\Users\luyicheng\miniconda3\envs\3dscanner\python.exe"
SERVER = r"C:\Users\luyicheng\Desktop\3dscanner\scripts\upload_server.py"
PORT = 8127
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


# 上传 3 个不同文件名的照片
r1 = post_files([("1786028074253.jpg", jpg), ("photo.png", jpg), ("a.JPEG", jpg)])
print("T1 上传:", r1)
names = [m for m in r1["messages"]]
print("  保存为:", names)
assert "img_001.jpg" in names[0] and "img_002.png" in names[1], f"命名异常: {names}"

# 再传 1 个，应该 img_003
r2 = post_files([("same_name.jpg", jpg)])
print("T2 再传:", r2["messages"])
assert "img_003" in r2["messages"][0], f"编号未递增: {r2}"

proc.kill()
print("ALL TESTS PASSED ✅")
