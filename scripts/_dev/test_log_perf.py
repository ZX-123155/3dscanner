"""测试 /log 接口在日志很大时的响应性能"""
import subprocess, sys, time, urllib.request

PY = r"C:/Users/luyicheng/miniconda3/envs/3dscanner/python.exe"
SERVER = r"C:/Users/luyicheng/Desktop/3dscanner/scripts/upload_server.py"
PORT = 8128

proc = subprocess.Popen([PY, SERVER, "--port", str(PORT)],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(2)

# 先塞入一个大日志（模拟重建日志很大）
import upload_server_mod  # noqa
