"""将 gsplat 导出的标准 PLY 转为 Brush 兼容格式

背景：Brush 加载 PLY 时把 scale_* 当作 log(scale)、opacity 当作 logit（内部参数空间），
而 gsplat 导出的是真实 scale (exp后) 和 sigmoid 后的 opacity。
直接在 Brush 里打开 gsplat 的 PLY 会导致高斯膨胀成"光球"。

用法:
    python convert_to_brush.py --input model.ply --output model_brush.ply
"""
import argparse
from pathlib import Path

import numpy as np
from loguru import logger


def load_ply(path: Path) -> tuple[np.ndarray, bytes]:
    """读取 PLY，返回 (数据, 头部字节)"""
    with path.open("rb") as f:
        header = b""
        while b"end_header" not in header:
            header += f.readline()
        lines = header.decode("ascii").split("\n")
        n = int([l for l in lines if "element vertex" in l][0].split()[-1])
        props = [l.split()[-1] for l in lines if l.startswith("property")]
        dt = np.dtype([(p, "<f4") for p in props])
        data = np.fromfile(f, dtype=dt, count=n)
    return data, header


def to_logit(x: np.ndarray) -> np.ndarray:
    """sigmoid 值 -> logit 值"""
    x = np.clip(x, 1e-6, 1 - 1e-6)
    return np.log(x) - np.log(1 - x)


def convert(input_path: Path, output_path: Path) -> None:
    data, header = load_ply(input_path)
    logger.info(f"读取: {len(data)} 个高斯")

    # scale: 真实值 -> log
    for k in ("scale_0", "scale_1", "scale_2"):
        data[k] = np.log(np.clip(data[k], 1e-6, None))
    # opacity: sigmoid -> logit
    data["opacity"] = to_logit(data["opacity"])

    with output_path.open("wb") as f:
        f.write(header)
        f.write(data.tobytes())
    logger.info(f"Brush 兼容版已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    out = args.output or args.input.parent / f"{args.input.stem}_brush.ply"
    convert(args.input, out)


if __name__ == "__main__":
    main()
