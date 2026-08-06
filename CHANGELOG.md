# 修订日志 (CHANGELOG)

## [0.1.0] - 2026-08-06

### 新增
- COLMAP 重建管线 `scripts/run_colmap.py`：特征提取 → 穷举匹配 → 稀疏重建 → 模型转换 → 稠密重建（可选）
- 3DGS 训练脚本 `scripts/train_3dgs.py`：pycolmap 加载 COLMAP 模型 → gsplat 训练 → 环绕视频渲染 → PLY 导出
- 一键全流程 `scripts/pipeline.py`
- 手机拍摄指南 `docs/手机拍摄指南.md`
- 项目文档（README、开发日志）

### 技术要点
- COLMAP 4.1.1（CUDA 版）用于重建，参数名与旧版不同（FeatureExtraction.use_gpu）
- gsplat 1.5.3 + pycolmap 4.1.1 用于 3DGS
- Windows 下 gsplat JIT 编译需 CUDA 12.6+（兼容 MSVC 14.44），详见 README

### 修复
- gsplat JIT 编译的多项 Windows 兼容问题（详见 docs/开发日志.md）
- COLMAP 4.x 新格式与 3DGS 兼容问题（pycolmap 直接加载，无需格式转换）

### 验证
- 108 张测试图：COLMAP 稀疏重建成功（94818 点，108 图全部注册）
- gsplat CUDA 渲染验证通过
- GitHub: https://github.com/ZX-123155/3dscanner
