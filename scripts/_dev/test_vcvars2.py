"""用 bat 内 call 的方式测试 vcvars64（与 run_env.bat 一致）"""
import subprocess

bat = r'''@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
echo AFTER_VCVARS_ERRCODE=%ERRORLEVEL%
where cl >nul 2>&1 && echo CL_OK || echo CL_MISSING
'''
import tempfile, os
with tempfile.NamedTemporaryFile("w", suffix=".bat", delete=False, encoding="utf-8") as f:
    f.write(bat)
    bat_path = f.name

r = subprocess.run(['cmd.exe', '/c', bat_path], capture_output=True, timeout=120)
print('rc:', r.returncode)
print('out:', r.stdout.decode('utf-8', errors='replace')[-500:])
print('err:', r.stderr.decode('utf-8', errors='replace')[-500:])
os.unlink(bat_path)
