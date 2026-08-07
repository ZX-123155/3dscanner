"""验证修复后的 run_env.bat 无 MSVC 报错"""
import subprocess
import os

# 模拟 upload_server 调用方式
cmd = ['cmd.exe', '/c', r'C:\Users\luyicheng\Desktop\3dscanner\scripts\_dev\run_env.bat',
       r'C:\Users\luyicheng\Desktop\3dscanner\scripts\_dev\echo_test.py']
open(r'C:\Users\luyicheng\Desktop\3dscanner\scripts\_dev\echo_test.py', 'w', encoding='utf-8').write(
    'import sys\nprint("python runs, encoding:", sys.stdout.encoding)\n')

r = subprocess.run(cmd, capture_output=True, timeout=120)
out = r.stdout.decode('utf-8', errors='replace')
err = r.stderr.decode('utf-8', errors='replace')
print('rc:', r.returncode)
print('--- out ---')
print(out[-400:])
print('--- err ---')
print(err[-400:] if err.strip() else '(empty - no errors!)')
print()
print('MSVC ERROR PRESENT:', 'MSVC' in err or 'MSVC' in out)
print('PYTHON RAN:', 'python runs' in out)
