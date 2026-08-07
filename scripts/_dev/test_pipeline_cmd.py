import subprocess, sys, os
sys.path.insert(0, r"C:/Users/luyicheng/Desktop/3dscanner/scripts")
import upload_server
print("CMD:", upload_server.PIPELINE_CMD)
env = dict(os.environ)
env.pop("CUDA_HOME", None)
try:
    r = subprocess.run(upload_server.PIPELINE_CMD, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    print("rc:", r.returncode)
    print("stdout len:", len(r.stdout), "stderr len:", len(r.stderr))
    print("--- stdout tail ---")
    print(r.stdout[-800:])
except Exception as e:
    print("EXCEPTION:", type(e).__name__, e)
