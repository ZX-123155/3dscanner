@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
set "PATH=C:\Users\luyicheng\miniconda3\envs\3dscanner;C:\Users\luyicheng\miniconda3\envs\3dscanner\Scripts;C:\Users\luyicheng\miniconda3\envs\3dscanner\Library\bin;%PATH%"
set "CUDA_HOME=C:\Users\luyicheng\miniconda3\envs\3dscanner"
set "NVCC_PREPEND_FLAGS=-allow-unsupported-compiler"
cd /d "C:\Users\luyicheng\AppData\Local\torch_extensions\torch_extensions\Cache\py310_cu121\gsplat_cuda"
ninja -v > "C:\Users\luyicheng\Desktop\3dscanner\output\ninja_build.log" 2>&1
echo NINJA_EXIT=%ERRORLEVEL%
