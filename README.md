# 3D 物体扫描仪 (3D Scanner)

用手机/相机拍摄一组照片 → COLMAP 重建点云 → 3D Gaussian Splatting 渲染，生成可交互的 3D 场景。

## 流程总览

```
拍摄照片 → input/ → COLMAP 稀疏重建 → 3DGS 训练 → 渲染视频/点云
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

把手机/相机拍摄的照片放入 `input/` 目录。**拍摄建议**：
- 围绕物体转一圈，相邻照片重叠 60% 以上
- 保持光照均匀，避免过曝/过暗
- 物体放在纹理丰富的背景前（不要纯白/纯黑）
- 30~150 张效果最好

### 3. 一键重建（COLMAP + 3DGS）

```bash
# 方式一：分步执行
conda run -n 3dscanner python scripts/run_colmap.py --input input --output output
conda run -n 3dscanner python scripts/train_3dgs.py --colmap output --out models/3dgs

# 方式二：一键全流程（推荐）
conda run -n 3dscanner python scripts/pipeline.py --input input --output output --model models/3dgs
```

### 4. 查看结果

| 产物 | 路径 | 说明 |
|------|------|------|
| 稀疏点云 | `output/sparse.ply` | COLMAP 稀疏重建点云 |
| 稠密点云 | `output/fused.ply` | 稠密重建（需 `--dense`） |
| 3DGS 模型 | `models/3dgs/` | 训练好的高斯泼溅模型 |
| 渲染视频 | `models/3dgs/renders/` | 环绕视角渲染结果 |

## 手机拍摄工作流

1. 手机拍摄（建议开启网格线辅助构图）
2. 通过微信/QQ/数据线把照片传到电脑
3. 放入 `input/` 目录（覆盖旧照片前先备份）
4. 运行一键重建命令

详细说明见 `docs/手机拍摄指南.md`

## 项目结构

```
3dscanner/
├── input/          # 拍摄的照片（手动放入）
├── output/         # COLMAP 重建结果（自动生成）
├── models/         # 3DGS 模型（自动生成）
├── scripts/
│   ├── run_colmap.py   # COLMAP 重建管线
│   ├── train_3dgs.py   # 3DGS 训练
│   └── pipeline.py     # 一键全流程
└── docs/           # 文档
```

## 常见问题

- **CUDA 不可用**：确认 `nvidia-smi` 有输出，且 PyTorch 是 cu121 版本
- **重建失败/点数太少**：检查照片重叠率、光照；增加照片数量
- **训练很慢**：`--max-steps` 调小（默认 30000），或 `--data-factor 2` 降分辨率
