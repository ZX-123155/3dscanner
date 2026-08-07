@echo off
rem Generic wrapper: load MSVC + CUDA env then run python script
rem Usage: run_env.bat <script.py> [args...]
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
set "CUDA_HOME=C:\Users\luyicheng\miniconda3\envs\3dscanner"
set "TORCH_CUDA_ARCH_LIST=8.6"
set "PYTHONPATH="
set "NVCC_PREPEND_FLAGS=-allow-unsupported-compiler"
set "PATH=C:\Users\luyicheng\miniconda3\envs\3dscanner;C:\Users\luyicheng\miniconda3\envs\3dscanner\Scripts;C:\Users\luyicheng\miniconda3\envs\3dscanner\Library\bin;%PATH%"
"C:\Users\luyicheng\miniconda3\envs\3dscanner\python.exe" %*
echo EXIT_CODE=%ERRORLEVEL%
