"""单独测试 vcvars64.bat 是否正常加载"""
import subprocess

r = subprocess.run(
    ['cmd.exe', '/c',
     r'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && where cl && echo VCVARS_OK'],
    capture_output=True, timeout=120)
print('rc:', r.returncode)
out = r.stdout.decode('utf-8', errors='replace')
err = r.stderr.decode('utf-8', errors='replace')
print('--- out ---')
print(out[-800:])
print('--- err ---')
print(err[-800:])
print('CL FOUND:', 'cl.exe' in out)
