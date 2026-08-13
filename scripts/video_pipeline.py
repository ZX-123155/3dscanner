"""视频 → 3D 场景重建一键流程

用法:
  python scripts/video_pipeline.py --video <视频.mp4> [--work <工作目录>]

示例:
  python scripts/video_pipeline.py --video scan.mp4
  python scripts/video_pipeline.py --video scan.mp4 --fps 2 --max-steps 30000
  python scripts/video_pipeline.py --video scan.mp4 --engine brush   # 用 Brush 训练

流程: 视频 → ffmpeg 抽帧 → COLMAP(sequential) → 3DGS/Brush 训练 → 导出
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from loguru import logger


def find_ffmpeg() -> Path:
    """定位 ffmpeg：优先 PATH，其次 conda 3dscanner 环境"""
    exe = shutil.which("ffmpeg")
    if exe:
        return Path(exe)
    # conda 环境常见位置
    candidates = [
        Path.home() / "miniconda3" / "envs" / "3dscanner" / "Library" / "bin" / "ffmpeg.exe",
        Path.home() / "anaconda3" / "envs" / "3dscanner" / "Library" / "bin" / "ffmpeg.exe",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "找不到 ffmpeg，请先安装：conda install -n 3dscanner ffmpeg，"
        "或确保 ffmpeg 在 PATH 中"
    )


def extract_frames(ffmpeg: Path, video: Path, frames_dir: Path, fps: float) -> int:
    """用 ffmpeg 按固定帧率抽帧，返回抽出的帧数"""
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("frame_*.jpg"):
        old.unlink()
    cmd = [
        str(ffmpeg), "-i", str(video),
        "-vf", f"fps={fps}",
        "-qscale:v", "2",
        str(frames_dir / "frame_%04d.jpg"),
        "-y",
    ]
    logger.info(f"抽帧: {video.name} @ {fps}fps")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 抽帧失败:\n{result.stderr[-800:]}")
    n = len(list(frames_dir.glob("frame_*.jpg")))
    logger.info(f"抽帧完成: {n} 帧 → {frames_dir}")
    if n < 8:
        raise RuntimeError(f"只抽出 {n} 帧（视频太短或 fps 太大），至少需要 8 帧才能重建")
    return n


def run_colmap(script_dir: Path, frames_dir: Path, colmap_dir: Path) -> None:
    """COLMAP 稀疏重建（视频序列用 sequential_matcher）"""
    py = sys.executable
    cmd = [
        py, str(script_dir / "run_colmap.py"),
        "--input", str(frames_dir),
        "--output", str(colmap_dir),
        "--matcher", "sequential",
        "--no-dense",
    ]
    logger.info("COLMAP 稀疏重建（sequential_matcher）")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError("COLMAP 重建失败")


def prepare_brush_dataset(colmap_dir: Path, brush_dir: Path) -> Path:
    """把 COLMAP 输出整理成 Brush 需要的数据集（sparse/ + images/）"""
    src_sparse = colmap_dir / "sparse" / "0"
    if not src_sparse.exists():
        raise FileNotFoundError(f"COLMAP 稀疏模型不存在: {src_sparse}")

    dst_sparse = brush_dir / "sparse"
    dst_images = brush_dir / "images"
    if dst_sparse.exists():
        shutil.rmtree(dst_sparse)
    if dst_images.exists():
        shutil.rmtree(dst_images)
    shutil.copytree(src_sparse, dst_sparse)
    shutil.copytree(colmap_dir / "images", dst_images)
    n_img = len(list(dst_images.glob("*.jpg")))
    logger.info(f"Brush 数据集就绪: {brush_dir}（{n_img} 图）")
    return brush_dir


def train_gsplat(script_dir: Path, colmap_dir: Path, model_dir: Path, max_steps: int, max_size: int) -> None:
    """用 gsplat 训练（需要 MSVC + CUDA 环境，建议经 run_env_light.bat 运行本脚本）"""
    py = sys.executable
    cmd = [
        py, str(script_dir / "train_3dgs.py"),
        "--colmap", str(colmap_dir),
        "--out", str(model_dir),
        "--max-steps", str(max_steps),
        "--max-size", str(max_size),
    ]
    logger.info(f"gsplat 训练 {max_steps} 步")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError("gsplat 训练失败")


def train_brush(brush_cli: Path, brush_dir: Path, work_dir: Path, max_steps: int) -> None:
    """用 Brush（headless CLI）训练，输出在 work_dir/brush_dataset_exports/"""
    cmd = [str(brush_cli), str(brush_dir), "--total-train-iters", str(max_steps)]
    logger.info(f"Brush 训练 {max_steps} 步")
    result = subprocess.run(cmd, cwd=str(work_dir))
    if result.returncode != 0:
        raise RuntimeError("Brush 训练失败")


def export_light(script_dir: Path, model_dir: Path, target: int) -> None:
    """降采样导出浏览器可看的轻量版"""
    src = model_dir / "model.ply"
    if not src.exists():
        logger.warning(f"未找到 {src}，跳过轻量版导出")
        return
    py = sys.executable
    cmd = [
        py, str(script_dir / "export_light.py"),
        "--input", str(src),
        "--target", str(target),
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        logger.warning("轻量版导出失败（不影响主结果）")


def main() -> None:
    parser = argparse.ArgumentParser(description="视频 → 3D 场景重建一键流程")
    parser.add_argument("--video", type=Path, required=True, help="输入视频文件")
    parser.add_argument("--work", type=Path, default=None, help="工作目录（默认视频同级 <视频名>_recon）")
    parser.add_argument("--fps", type=float, default=2.0, help="抽帧帧率（默认 2，即每 0.5 秒一帧）")
    parser.add_argument("--max-steps", type=int, default=30000, help="训练步数")
    parser.add_argument("--max-size", type=int, default=1024, help="训练图片最大边")
    parser.add_argument("--engine", choices=["gsplat", "brush"], default="gsplat", help="训练引擎")
    parser.add_argument("--brush-cli", type=Path, default=None, help="brush-cli.exe 路径（engine=brush 时需要）")
    parser.add_argument("--light", type=int, default=100_000, help="轻量版目标高斯数（0=跳过）")
    parser.add_argument("--skip-colmap", action="store_true", help="跳过 COLMAP（复用已有 colmap/）")
    parser.add_argument("--skip-train", action="store_true", help="跳过训练（只抽帧+COLMAP）")
    args = parser.parse_args()

    if not args.video.exists():
        raise FileNotFoundError(f"视频不存在: {args.video}")

    script_dir = Path(__file__).parent
    work = args.work or args.video.with_name(args.video.stem + "_recon")
    frames_dir = work / "frames"
    colmap_dir = work / "colmap"
    model_dir = work / "models"
    work.mkdir(parents=True, exist_ok=True)
    logger.info(f"工作目录: {work}")

    # 1. 抽帧
    ffmpeg = find_ffmpeg()
    extract_frames(ffmpeg, args.video, frames_dir, args.fps)

    # 2. COLMAP
    if not args.skip_colmap:
        run_colmap(script_dir, frames_dir, colmap_dir)

    if args.skip_train:
        logger.success(f"完成（跳过训练）。产物: {colmap_dir}")
        return

    # 3. 训练
    if args.engine == "gsplat":
        train_gsplat(script_dir, colmap_dir, model_dir, args.max_steps, args.max_size)
    else:
        brush_cli = args.brush_cli or Path.home() / "Desktop" / "brush" / "target" / "release" / "brush-cli.exe"
        if not brush_cli.exists():
            raise FileNotFoundError(f"brush-cli 不存在: {brush_cli}")
        brush_dir = work / "brush_dataset"
        prepare_brush_dataset(colmap_dir, brush_dir)
        train_brush(brush_cli, brush_dir, work, args.max_steps)

    # 4. 导出轻量版（gsplat 引擎自动双导出 model.ply + model_brush.ply）
    if args.engine == "gsplat" and args.light > 0:
        export_light(script_dir, model_dir, args.light)

    logger.success(
        f"🎉 视频重建完成！\n"
        f"  帧: {frames_dir}\n"
        f"  COLMAP: {colmap_dir}\n"
        f"  模型: {model_dir}"
    )


if __name__ == "__main__":
    main()
