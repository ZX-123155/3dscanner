#!/bin/sh
# nvcc 包装：自动注入 -allow-unsupported-compiler（兼容新版 MSVC）
REAL_NVCC="C:/Users/luyicheng/miniconda3/envs/3dscanner/bin/nvcc.exe"
exec "$REAL_NVCC" -allow-unsupported-compiler "$@"
