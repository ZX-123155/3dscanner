"""
3D Gaussian Splatting 训练与渲染（基于 gsplat）
用法: python scripts/run_3dgs.py --colmap_dir <COLMAP输出> --output <模型输出>

数据准备：将 COLMAP 标准格式组织为 gsplat 期望的结构
"""

import argparse
import shutil
import subprocess
from pathlib import Path


def prepare_data(colmap_workspace: Path, data_root: Path) -> None:
    """组织 COLMAP 输出为 gsplat/nerfstudio 兼容结构"""
    if data_root.exists():
        shutil.rmtree(data_root)
    # data/images/ -> 原图
    shutil.copytree(colmap_workspace / "images", data_root / "images")
    # data/colmap/sparse/0/ -> 标准稀疏模型
    sparse0 = data_root / "colmap" / "sparse" / "0"
    sparse0.mkdir(parents=True)
    for f in ("cameras.bin", "images.bin", "points3D.bin"):
        src = colmap_workspace / "sparse_standard" / f
        if src.exists():
            shutil.copy2(src, sparse0 / f)
    print(f"数据已组织到: {data_root}")


def main() -> None:
    parser = argparse.ArgumentParser(description="3DGS 训练（gsplat）")
    parser.add_argument("--colmap_dir", type=Path, required=True, help="COLMAP 工作目录")
    parser.add_argument("--output", type=Path, required=True, help="3DGS 模型输出目录")
    parser.add_argument("--max-steps", type=int, default=30000, help="训练步数")
    args = parser.parse_args()

    # 准备数据
    data_root = args.colmap_dir / "gsplat_data"
    prepare_data(args.colmap_dir, data_root)

    # 检查稀疏模型是否可用
    sparse0 = data_root / "colmap" / "sparse" / "0"
    if not (sparse0 / "cameras.bin").exists():
        raise RuntimeError("缺少 COLMAP 标准模型，请先运行 run_colmap.py")

    # 训练（gsplat simple_trainer）
    cmd = [
        "python", "-m", "gsplat.scripts.simple_trainer",
        "--data", str(data_root),
        "--result-dir", str(args.output),
        "--data-factor", "1",
        "--max-steps", str(args.max_steps),
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    print(f"\n3DGS 训练完成！模型输出: {args.output}")


if __name__ == "__main__":
    main()
