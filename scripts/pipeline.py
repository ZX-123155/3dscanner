# 一键全流程：照片 → COLMAP → 3DGS → 渲染

用法:
  python scripts/pipeline.py --input <照片目录> --output <COLMAP输出> --model <模型目录>

示例:
  conda run -n 3dscanner python scripts/pipeline.py --input input --output output --model models/3dgs
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(cmd: list[str], desc: str) -> None:
    print(f"\n{'='*60}\n[1/2] {desc}\n{'='*60}")
    result = subprocess.run([str(c) for c in cmd])
    if result.returncode != 0:
        raise RuntimeError(f"步骤失败: {desc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="3D 扫描一键全流程")
    parser.add_argument("--input", type=Path, required=True, help="照片目录")
    parser.add_argument("--output", type=Path, required=True, help="COLMAP 输出目录")
    parser.add_argument("--model", type=Path, required=True, help="3DGS 模型目录")
    parser.add_argument("--dense", action="store_true", help="启用稠密重建（耗时更长）")
    parser.add_argument("--max-steps", type=int, default=30000, help="3DGS 训练步数")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    py = sys.executable

    # 1. COLMAP 重建
    colmap_cmd = [py, str(script_dir / "run_colmap.py"), "--input", str(args.input), "--output", str(args.output)]
    if not args.dense:
        colmap_cmd.append("--no-dense")
    run_step(colmap_cmd, "COLMAP 三维重建")

    # 2. 3DGS 训练
    gs_cmd = [
        py, str(script_dir / "train_3dgs.py"),
        "--colmap", str(args.output),
        "--out", str(args.model),
        "--max-steps", str(args.max_steps),
    ]
    run_step(gs_cmd, "3D Gaussian Splatting 训练")

    print(f"\n{'='*60}\n✅ 全流程完成！\n  点云: {args.output / 'sparse.ply'}\n  3DGS: {args.model}\n{'='*60}")


if __name__ == "__main__":
    main()
