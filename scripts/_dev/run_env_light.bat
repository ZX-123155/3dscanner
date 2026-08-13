@echo off
rem Minimal MSVC env: only compiler + headers/libs (avoid vcvars DLL pollution that crashes torch)
set "MSVC_ROOT=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207"
set "SDK_ROOT=C:\Program Files (x86)\Windows Kits\10"
set "PATH=C:\Users\luyicheng\miniconda3\envs\3dscanner\Library\bin;%MSVC_ROOT%\bin\Hostx64\x64;%PATH%"
set "INCLUDE=%MSVC_ROOT%\include;C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0\ucrt;%INCLUDE%"
set "LIB=%MSVC_ROOT%\lib\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64;%LIB%"
set "CUDA_HOME=C:\Users\luyicheng\miniconda3\envs\3dscanner"
set "TORCH_CUDA_ARCH_LIST=8.6"
"C:\Users\luyicheng\miniconda3\envs\3dscanner\python.exe" %*
echo EXIT_CODE=%ERRORLEVEL%
