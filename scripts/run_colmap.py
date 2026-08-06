"""
COLMAP 重建管线：图片 -> 稀疏点云 -> 稠密点云
用法: python scripts/run_colmap.py --input <图片目录> --output <输出目录>
"""

import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

COLMAP_BIN = Path(r"C:\Users\luyicheng\colmap-x64-windows-cuda\bin\colmap.exe")


def backup_dir(path: Path) -> None:
    """将已存在的目录重命名备份（避免删除，保证可回溯）"""
    if not path.exists():
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.name}_bak_{ts}")
    path.rename(backup)
    print(f"旧目录已备份: {path} -> {backup}")


def run_cmd(cmd: list[str], desc: str) -> None:
    """执行外部命令并打印输出"""
    print(f"\n=== {desc} ===")
    print(" ".join(str(c) for c in cmd))
    result = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        raise RuntimeError(f"步骤失败: {desc} (exit={result.returncode})")
    # 只打印最后几行，避免刷屏
    tail = (result.stdout or result.stderr).strip().splitlines()[-5:]
    print("\n".join(tail))


def build_dense(workspace: Path, colmap: Path = COLMAP_BIN, sparse_model: Optional[Path] = None) -> Optional[Path]:
    """稠密重建：patch_match_stereo + stereo_fusion"""
    print("\n=== 稠密重建（patch_match_stereo + stereo_fusion）===")
    dense_dir = workspace / "dense"
    backup_dir(dense_dir)
    dense_dir.mkdir(parents=True)

    input_model = sparse_model if sparse_model else workspace / "sparse" / "0"
    run_cmd(
        [
            colmap,
            "image_undistorter",
            "--image_path", workspace / "images",
            "--input_path", input_model,
            "--output_path", dense_dir,
            "--output_type", "COLMAP",
        ],
        "图像去畸变 (image_undistorter)",
    )

    run_cmd(
        [
            colmap,
            "patch_match_stereo",
            "--workspace_path", dense_dir,
            "--workspace_format", "COLMAP",
            "--PatchMatchStereo.geom_consistency", "true",
        ],
        "深度估计 (patch_match_stereo)",
    )

    fused_ply = workspace / "fused.ply"
    run_cmd(
        [
            colmap,
            "stereo_fusion",
            "--workspace_path", dense_dir,
            "--workspace_format", "COLMAP",
            "--input_type", "geometric",
            "--output_path", fused_ply,
        ],
        "点云融合 (stereo_fusion)",
    )
    return fused_ply


def main() -> None:
    parser = argparse.ArgumentParser(description="COLMAP 三维重建管线")
    parser.add_argument("--input", type=Path, required=True, help="输入图片目录")
    parser.add_argument("--output", type=Path, required=True, help="输出目录")
    parser.add_argument("--no-dense", action="store_true", help="跳过稠密重建（只需稀疏模型）")
    parser.add_argument("--colmap", type=Path, default=COLMAP_BIN, help="COLMAP 可执行文件路径")
    args = parser.parse_args()

    input_dir: Path = args.input
    workspace: Path = args.output
    colmap: Path = args.colmap

    if not colmap.exists():
        raise FileNotFoundError(f"COLMAP 不存在: {colmap}")

    # 准备目录结构
    workspace.mkdir(parents=True, exist_ok=True)
    images_dir = workspace / "images"
    backup_dir(images_dir)
    # 复制图片（COLMAP 需要 image_path 与数据库路径分开）
    images_dir.mkdir(parents=True)
    for img in sorted(input_dir.iterdir()):
        if img.suffix.lower() in (".jpg", ".jpeg", ".png"):
            shutil.copy2(img, images_dir / img.name)
    print(f"已复制 {len(list(images_dir.iterdir()))} 张图片")

    database_path = workspace / "database.db"
    backup_dir(database_path)
    sparse_dir = workspace / "sparse"
    backup_dir(sparse_dir)
    sparse_dir.mkdir(parents=True)

    # 1. 特征提取（GPU）
    run_cmd(
        [
            colmap, "feature_extractor",
            "--database_path", database_path,
            "--image_path", images_dir,
            "--ImageReader.single_camera", "true",
            "--FeatureExtraction.use_gpu", "true",
        ],
        "特征提取 (feature_extractor)",
    )

    # 2. 特征匹配（108 张图，使用穷举匹配）
    run_cmd(
        [
            colmap, "exhaustive_matcher",
            "--database_path", database_path,
            "--FeatureMatching.use_gpu", "true",
        ],
        "特征匹配 (exhaustive_matcher)",
    )

    # 3. 稀疏重建
    run_cmd(
        [
            colmap, "mapper",
            "--database_path", database_path,
            "--image_path", images_dir,
            "--output_path", sparse_dir,
        ],
        "稀疏重建 (mapper)",
    )

    # 4. 找出最佳模型（mapper 可能输出多个子模型）
    model_dirs = [d for d in sorted(sparse_dir.iterdir()) if d.is_dir()]
    if not model_dirs:
        raise RuntimeError("稀疏重建失败：没有生成模型")
    best_model = model_dirs[0]
    print(f"\n使用模型: {best_model}")

    # 5. 模型转换：COLMAP 4.x 新格式 -> 标准格式（3DGS 兼容）
    standard_model = workspace / "sparse_standard"
    backup_dir(standard_model)
    standard_model.mkdir(parents=True)
    run_cmd(
        [
            colmap, "model_converter",
            "--input_path", best_model,
            "--output_path", standard_model,
            "--output_type", "BIN",
        ],
        "模型格式转换 (model_converter)",
    )

    # 6. 导出稀疏点云 PLY
    sparse_ply = workspace / "sparse.ply"
    run_cmd(
        [
            colmap, "model_converter",
            "--input_path", best_model,
            "--output_path", sparse_ply,
            "--output_type", "PLY",
        ],
        "导出稀疏点云 (sparse.ply)",
    )

    # 7. 稠密重建（可选）
    fused_ply = None
    if not args.no_dense:
        fused_ply = build_dense(workspace, colmap, sparse_model=best_model)

    # 总结
    print("\n" + "=" * 50)
    print("重建完成！产出文件：")
    print(f"  稀疏模型: {standard_model}")
    print(f"  稀疏点云: {sparse_ply}")
    if fused_ply and fused_ply.exists():
        print(f"  稠密点云: {fused_ply}")
    print("=" * 50)


if __name__ == "__main__":
    main()
