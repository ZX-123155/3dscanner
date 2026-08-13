# 3D 物体扫描仪 (3D Scanner)

用手机/相机拍摄一组照片 **或一段视频** → COLMAP 重建点云 → 3D Gaussian Splatting 渲染，生成可交互的 3D 场景。

## 流程总览

```
路线 A（照片）: 拍摄照片 → input/ → COLMAP 稀疏重建 → 3DGS 训练 → 渲染视频/点云
路线 B（视频）: 拍摄视频 → 抽帧 → COLMAP(sequential) 重建 → 3DGS/Brush 训练 → 渲染视频/点云
```

## 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Windows 11 | - | 已测试 |
| NVIDIA GPU | RTX 3060 6GB | 需要 CUDA |
| conda | 26.1.1 | 环境名: `3dscanner` |
| COLMAP | 4.1.1 (CUDA) | `C:\Users\luyicheng\colmap-x64-windows-cuda` |
| PyTorch | 2.5.1+cu121 | conda 环境内 |
| gsplat | 1.5.3 | conda 环境内 |

## 快速开始

### 1. 创建环境（一次性）

```bash
conda create -n 3dscanner python=3.10 -y
conda run -n 3dscanner pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 --index-url https://download.pytorch.org/whl/cu121
conda run -n 3dscanner pip install gsplat scipy opencv-python-headless imageio imageio-ffmpeg tqdm loguru
```

### 2. 拍摄照片

手机拍摄照片，通过任一方式放入 `input/` 目录：

- **方式 A（推荐）：局域网直传**——手机连同一 WiFi，电脑启动上传服务，手机浏览器传照片并一键触发重建：
  ```bash
  C:\Users\luyicheng\miniconda3\envs\3dscanner\python.exe scripts/upload_server.py
  # 手机浏览器打开 http://<电脑局域网IP>:8000
  ```
- **方式 B**：微信/QQ 文件传输助手另存到 `input/`
- **方式 C**：数据线复制到 `input/`

**拍摄建议**：
- 围绕物体转一圈，相邻照片重叠 60% 以上
- 保持光照均匀，避免过曝/过暗
- 物体放在纹理丰富的背景前（不要纯白/纯黑）
- 30~150 张效果最好

### 3. 一键重建（COLMAP + 3DGS）

```bash
# 先激活环境（注意：不能用 conda run，该环境带 CUDA 激活脚本会报错）
conda activate 3dscanner

# 方式一：分步执行
python scripts/run_colmap.py --input input --output output
python scripts/train_3dgs.py --colmap output --out models/3dgs

# 方式二：一键全流程（推荐）
python scripts/pipeline.py --input input --output output --model models/3dgs
```

> 如果 `conda activate` 也报 "Did not find VSINSTALLDIR"，那是环境里 CUDA 激活脚本在查 VS2017，不影响后续命令执行，直接忽略即可。

> 训练 3DGS 时如遇 CUDA 编译问题，用 `scripts/_dev/run_env.bat` 封装脚本运行（详见 docs/开发日志.md）

### 4. 查看结果

| 产物 | 路径 | 说明 |
|------|------|------|
| 稀疏点云 | `output/sparse.ply` | COLMAP 稀疏重建点云 |
| 稠密点云 | `output/fused.ply` | 稠密重建（需 `--dense`） |
| 3DGS 模型 | `models/3dgs/model.ply` | 标准 3DGS 格式（SuperSplat/antimatter15 等查看器） |
| 3DGS 模型 | `models/3dgs/model_brush.ply` | **Brush 兼容格式**（scale 存 log、opacity 存 logit，拖进 Brush GUI 用这个） |
| 渲染视频 | `models/3dgs/orbit.mp4` | 环绕视角渲染视频 |

> ⚠️ **PLY 格式说明**：3DGS 的 PLY 没有统一标准。gsplat/原版导出存**真实 scale**，Brush 加载时把 scale 当 **log(scale)**——直接用标准 PLY 打开 Brush 会"光球"（高斯膨胀）。`model_brush.ply` 已自动转换，用 Brush 时选它即可。

## 手机拍摄工作流

1. 手机拍摄（建议开启网格线辅助构图）
2. 通过微信/QQ/数据线把照片传到电脑
3. 放入 `input/` 目录（覆盖旧照片前先备份）
4. 运行一键重建命令

详细说明见 `docs/手机拍摄指南.md`

## 视频重建（路线 B）

不需要逐张拍照——**手机绕物体拍一段视频**，脚本自动抽帧 + 重建：

```bash
# 一键全流程（默认 gsplat 训练，自动抽帧 + COLMAP + 3DGS + 轻量版导出）
scripts\_dev\run_env_light.bat scripts\video_pipeline.py --video 视频.mp4

# 常用参数
--fps 2            # 抽帧帧率（默认 2 = 每 0.5 秒一帧；视频短可调 1）
--max-steps 30000  # 训练步数
--engine brush     # 换 Brush 训练（需 --brush-cli 指定 brush-cli.exe）
--skip-colmap      # 复用已有 colmap/ 目录，只重训
--skip-train       # 只抽帧 + COLMAP，不训练
```

**为什么要经 `run_env_light.bat` 运行？** gsplat 训练需要 MSVC + CUDA 环境（JIT 编译 CUDA 扩展）。`run_env_light.bat` 只注入编译器路径、不污染 DLL（完整 vcvars 会与 torch 冲突导致段错误）。

**拍摄建议**：
- 手机**慢速**绕物体转一圈（30-60 秒），尽量稳，不要甩动
- 环境光照均匀、物体纹理丰富
- 14 秒视频 ≈ 28 帧，30-60 秒视频效果最佳

**视频 vs 照片路线差异**（脚本已自动处理）：
| 环节 | 照片路线 | 视频路线 |
|---|---|---|
| 输入 | `input/` 目录 | 单个 `.mp4` |
| 特征匹配 | exhaustive（两两全匹配） | **sequential**（相邻帧匹配 + 回环检测） |
| 前置处理 | 无 | ffmpeg 抽帧（`fps=2`） |

## 项目结构

```
3dscanner/
├── input/          # 拍摄的照片（上传服务器/手动放入）
├── output/         # COLMAP 重建结果（自动生成）
├── models/         # 3DGS 模型（自动生成）
├── scripts/
│   ├── upload_server.py  # 局域网照片上传服务器（手机 WiFi 直传）
│   ├── run_colmap.py     # COLMAP 重建管线（--matcher 可选 exhaustive/sequential）
│   ├── train_3dgs.py     # 3DGS 训练
│   ├── video_pipeline.py # 视频一键重建（抽帧 → COLMAP → 训练）
│   ├── export_light.py   # 3DGS 降采样（浏览器流畅查看）
│   ├── convert_to_brush.py # 标准 PLY → Brush 兼容格式
│   └── pipeline.py       # 照片一键全流程
└── docs/           # 文档
```

## 常见问题

- **CUDA 不可用**：确认 `nvidia-smi` 有输出，且 PyTorch 是 cu121 版本
- **重建失败/点数太少**：检查照片重叠率、光照；增加照片数量
- **训练很慢**：`--max-steps` 调小（默认 30000），或 `--max-size` 降低分辨率（默认 1024）

### Windows + gsplat 特殊说明

gsplat 需要 JIT 编译 CUDA 扩展（首次运行需 5-10 分钟），需要：
1. conda 环境内安装 CUDA 编译工具：
   ```bash
   conda install -n 3dscanner -c nvidia cuda-nvcc=12.6 cuda-cudart-dev=12.6 cuda-cccl=12.6
   ```
   > 注意：MSVC 14.44+ 需要 CUDA ≥ 12.6（12.4 会报 STL1002）
2. 运行训练时需先加载 MSVC 环境（`scripts/_dev/run_env.bat` 已封装）：
   ```bash
   # 方式一：直接调用封装脚本
   scripts\_dev\run_env.bat scripts\train_3dgs.py --colmap output --out models/3dgs

   # 方式二：手动加载环境后运行
   call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
   set CUDA_HOME=C:\Users\luyicheng\miniconda3\envs\3dscanner
   python scripts\train_3dgs.py --colmap output --out models/3dgs
   ```
3. 若报 `fatal error C1083: crt/host_config.h 找不到`，说明 conda 的 CUDA 头文件被损坏（safe-delete 干扰），从 `Library/include` 复制到环境根 `include/`
