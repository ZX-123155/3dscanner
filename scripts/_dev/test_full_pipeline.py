"""完整测试 PIPELINE_CMD（流式输出，观察是否卡住）"""
import subprocess, sys, os
sys.path.insert(0, r"C:/Users/luyicheng/Desktop/3dscanner/scripts")
import upload_server
print("CMD:", upload_server.PIPELINE_CMD)
env = dict(os.environ)
env.pop("CUDA_HOME", None)
proc = subprocess.Popen(upload_server.PIPELINE_CMD, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                        errors="replace", env=env)
lines = []
for line in proc.stdout:
    lines.append(line.rstrip())
    if len(lines) % 200 == 0:
        print(f"... {len(lines)} lines, last: {line.rstrip()[:100]}")
proc.wait()
print("rc:", proc.returncode)
print("total lines:", len(lines))
print("--- 最后 15 行 ---")
for l in lines[-15:]:
    print(l[:120])
