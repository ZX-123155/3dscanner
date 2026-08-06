"""全面测试新版上传服务器：单/多文件、chunked、非图片、count"""
import io
import json
import subprocess
import sys
import time
import urllib.request

PY = r"C:\Users\luyicheng\miniconda3\envs\3dscanner\python.exe"
SERVER = r"C:\Users\luyicheng\Desktop\3dscanner\scripts\upload_server.py"
PORT = 8125
jpg = b"\xff\xd8\xff\xe0" + b"\x00" * 200 + b"\xff\xd9"

proc = subprocess.Popen([PY, SERVER, "--port", str(PORT)],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(2)


def post_files(files: list, chunked: bool = False):
    """构造 multipart 请求，files=[(filename, bytes)]"""
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

    if chunked:
        import socket
        # 手动构造 chunked 请求
        s = socket.create_connection(("127.0.0.1", PORT), timeout=5)
        head = (f"POST /upload HTTP/1.1\r\nHost: 127.0.0.1:{PORT}\r\n"
                f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
                "Transfer-Encoding: chunked\r\n\r\n").encode()
        s.sendall(head)
        for i in range(0, len(body), 4096):
            chunk = body[i:i + 4096]
            s.sendall(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
        s.sendall(b"0\r\n\r\n")
        resp = b""
        s.settimeout(5)
        try:
            while True:
                d = s.recv(4096)
                if not d:
                    break
                resp += d
        except socket.timeout:
            pass
        s.close()
        # 提取 JSON
        idx = resp.find(b"\r\n\r\n")
        return resp[idx + 4:].decode()
    else:
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/upload", data=body, method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode()


# 测试 1: 单文件（之前崩溃的场景）
r1 = json.loads(post_files([("single.jpg", jpg)]))
print("T1 单文件:", r1)
assert r1["saved"] == 1 and r1["skipped"] == 0, "单文件失败"

# 测试 2: 多文件 + 非图片混合
r2 = json.loads(post_files([("a.jpg", jpg), ("b.png", jpg), ("c.txt", jpg)]))
print("T2 多文件:", r2)
assert r2["saved"] == 2 and r2["skipped"] == 1, "多文件失败"

# 测试 3: chunked 编码
r3 = json.loads(post_files([("chunked.jpg", jpg)], chunked=True))
print("T3 chunked:", r3)
assert r3["saved"] == 1, "chunked 失败"

# 测试 4: /count
with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/count", timeout=5) as r:
    r4 = json.loads(r.read().decode())
print("T4 count:", r4)
assert r4["count"] >= 3, "count 接口异常"

# 测试 5: 首页
with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=5) as r:
    page = r.read().decode()
assert "拍照" in page and "上传全部" in page and "开始重建" in page, "首页缺少新按钮"
print("T5 首页: OK（含拍照/上传全部/开始重建）")

proc.kill()
print("ALL TESTS PASSED ✅")
