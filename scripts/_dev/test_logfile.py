"""验证 start_build 日志落盘"""
import sys, time
sys.path.insert(0, r"C:/Users/luyicheng/Desktop/3dscanner/scripts")
import upload_server

# 用假命令模拟（打印几行后退出）
import tempfile, os
tmp = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8")
tmp.write("import time\nfor i in range(3):\n    print(f'重建进度: 第 {i+1} 步')\n    time.sleep(0.3)\n")
tmp.close()
upload_server.PIPELINE_CMD = [sys.executable, tmp.name]

msg = upload_server.start_build()
print("返回:", msg)

for _ in range(20):
    if not upload_server._build_state["running"]:
        break
    time.sleep(0.2)

# 检查日志文件是否生成且包含内容
import glob
logs = glob.glob(r"C:/Users/luyicheng/Desktop/3dscanner/output/rebuild_*.log")
print("日志文件:", logs)
if logs:
    content = open(logs[-1], encoding="utf-8").read()
    print("日志内容:", content.strip())
    assert "重建进度" in content, "日志文件内容缺失"
os.unlink(tmp.name)
print("LOG FILE TEST PASSED ✅")
