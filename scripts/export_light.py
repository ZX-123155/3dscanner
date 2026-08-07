"""导出轻量版 3DGS 模型（降采样高斯数，供浏览器在线查看）

用法:
    python scripts/export_light.py --input models/3dgs/model.ply --target 100000

原理:
    - 按透明度加权采样（透明噪点优先剔除，保留实体部分）
    - 输出 model_light.ply（默认 10 万高斯，浏览器可流畅查看）
"""
import argparse
from pathlib import Path

import numpy as np
from loguru import logger


def load_ply(path: Path) -> dict:
    """读取 gsplat/3DGS 格式的 PLY，返回各属性数组"""
    with path.open("rb") as f:
        header_lines = []
        while True:
            line = f.readline().decode("ascii", errors="ignore").strip()
            header_lines.append(line)
            if line == "end_header":
                break
        # 解析属性
        props = []
        for line in header_lines:
            if line.startswith("property "):
                parts = line.split()
                props.append(parts[-1])
        # 从 vertex count 读取
        n_vertex = 0
        for line in header_lines:
            if line.startswith("element vertex"):
                n_vertex = int(line.split()[-1])
        dtype_list = []
        for name in props:
            if name in ("x", "y", "z", "f_dc_0", "f_dc_1", "f_dc_2",
                        "opacity", "scale_0", "scale_1", "scale_2"):
                dtype_list.append((name, "<f4"))
            elif name.startswith("rot_"):
                dtype_list.append((name, "<f4"))
            elif name == "n":
                dtype_list.append((name, "<u1"))
            else:
                dtype_list.append((name, "<f4"))
        data = np.fromfile(f, dtype=np.dtype(dtype_list), count=n_vertex)
    return data


def save_ply(data: np.ndarray, out_path: Path) -> None:
    """保存 PLY（保持 gsplat 导出格式）"""
    names = data.dtype.names
    with out_path.open("wb") as f:
        f.write(b"ply\nformat binary_little_endian 1.0\n")
        f.write(f"element vertex {len(data)}\n".encode())
        for name in names:
            if name == "n":
                f.write(f"property uchar {name}\n".encode())
            else:
                f.write(f"property float {name}\n".encode())
        f.write(b"end_header\n")
        f.write(data.tobytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="输入的 model.ply")
    parser.add_argument("--out", type=Path, default=None, help="输出路径（默认同目录 model_light.ply）")
    parser.add_argument("--target", type=int, default=100_000, help="目标高斯数（默认 10 万）")
    args = parser.parse_args()

    data = load_ply(args.input)
    total = len(data)
    logger.info(f"原始模型: {total} 个高斯")

    if total <= args.target:
        logger.warning("高斯数未超过目标，直接复制")
        out = args.out or args.input.parent / "model_light.ply"
        save_ply(data, out)
        logger.info(f"已保存: {out}")
        return

    # 按透明度加权采样（保留不透明实体）
    opacity = data["opacity"]
    # 采样概率与透明度成正比，但避免全为 0
    weights = np.clip(opacity, 1e-3, 1.0)
    weights = weights / weights.sum()
    idx = np.random.choice(total, size=args.target, replace=False, p=weights)
    idx.sort()
    sampled = data[idx]

    out = args.out or args.input.parent / "model_light.ply"
    save_ply(sampled, out)
    logger.info(f"已保存轻量版: {out} ({len(sampled)} 个高斯, {out.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
