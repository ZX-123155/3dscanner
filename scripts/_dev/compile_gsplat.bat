@echo off
rem 加载 MSVC 环境并编译 gsplat CUDA 扩展
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
set "CUDA_HOME=C:\Users\luyicheng\miniconda3\envs\3dscanner"
set "TORCH_CUDA_ARCH_LIST=8.6"
set "FAST_COMPILE=1"
set "PYTHONPATH="
set "NVCC_PREPEND_FLAGS=-allow-unsupported-compiler"
set "PATH=C:\Users\luyicheng\miniconda3\envs\3dscanner;C:\Users\luyicheng\miniconda3\envs\3dscanner\Scripts;C:\Users\luyicheng\miniconda3\envs\3dscanner\Library\bin;%PATH%"
"C:\Users\luyicheng\miniconda3\envs\3dscanner\python.exe" "C:\Users\luyicheng\Desktop\3dscanner\scripts\_dev\compile_gsplat.py"
echo EXIT_CODE=%ERRORLEVEL%
