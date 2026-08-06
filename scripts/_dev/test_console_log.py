"""验证：子进程日志同时输出到终端"""
import subprocess, sys, time
sys.path.insert(0, r"C:/Users/luyicheng/Desktop/3dscanner/scripts")
import upload_server

# 用一个会打印多行中文的临时脚本模拟 pipeline
import tempfile, os
tmp = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8")
tmp.write("import time\n")
tmp.write("for i in range(5):\n")
tmp.write("    print(f'处理第 {i+1}/5 张照片，完成 20%')\n")
tmp.write("    time.sleep(0.2)\n")
tmp.close()
upload_server.PIPELINE_CMD = [sys.executable, tmp.name]

print("=== 终端实时输出（应逐行出现中文）===")
msg = upload_server.start_build()
print("start_build 返回:", msg)

# 等子进程跑完
for _ in range(30):
    if not upload_server._build_state["running"]:
        break
    time.sleep(0.2)

print("\n=== 手机页面日志（_build_state['log']）===")
print(upload_server._build_state["log"])
print("\nlast_result:", upload_server._build_state["last_result"])
os.unlink(tmp.name)
