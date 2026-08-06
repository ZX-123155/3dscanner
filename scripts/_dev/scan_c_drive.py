"""C 盘大文件扫描工具（只读，不删除任何文件）

用法: python scan_c_drive.py [--min-mb 200] [--out report.md]
输出: Markdown 报告（大文件列表 + 目录占用统计）
"""
import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 跳过这些系统/敏感目录（无法访问或不该建议删除的）
SKIP_DIRS = {
    "C:/Windows/WinSxS",
    "C:/Windows/System32",
    "C:/Windows/SysWOW64",
    "C:/Windows/assembly",
    "C:/Windows/Installer",
    "C:/Windows/SoftwareDistribution",
    "C:/$Recycle.Bin",
    "C:/System Volume Information",
    "C:/Recovery",
    "C:/Program Files/WindowsApps",
    "C:/ProgramData/Microsoft/Windows/WER",
}
SKIP_NAMES = {"pagefile.sys", "hiberfil.sys", "swapfile.sys"}


def fmt_size(n: int) -> str:
    """字节 -> 可读大小"""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def classify(path: Path) -> str:
    """按路径猜测文件类别"""
    p = str(path).lower()
    if "temp" in p or "tmp" in p or "cache" in p:
        return "临时/缓存"
    if p.endswith((".zip", ".rar", ".7z", ".tar", ".gz", ".iso", ".msi", ".exe")):
        return "安装包/压缩包"
    if "miniconda" in p or "conda" in p:
        return "conda/Python 环境"
    if "node_modules" in p or "npm" in p:
        return "npm 依赖"
    if "pip" in p or ".cache" in p or "torch" in p or "huggingface" in p:
        return "pip/模型缓存"
    if "workbuddy" in p or "codebuddy" in p:
        return "WorkBuddy 数据"
    if "downloads" in p or "下载" in p:
        return "下载文件"
    if "desktop" in p or "桌面" in p:
        return "桌面文件"
    if "video" in p or "movies" in p or p.endswith((".mp4", ".mkv", ".avi", ".mov")):
        return "视频"
    if p.endswith((".pth", ".pt", ".onnx", ".safetensors", ".ckpt")):
        return "AI 模型权重"
    if "docker" in p or "wsl" in p:
        return "容器/WSL"
    if ".vscode" in p or "code" in p:
        return "编辑器数据"
    return "其他"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-mb", type=int, default=200, help="最小文件大小(MB)")
    parser.add_argument("--out", default="C:/Users/luyicheng/Desktop/3dscanner/output/c_drive_report.md")
    args = parser.parse_args()

    min_bytes = args.min_mb * 1024 * 1024
    root = Path("C:/")
    big_files = []
    dir_sizes = {}
    t0 = time.time()
    scanned = 0
    errors = 0

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dp = Path(dirpath)
        # 跳过系统/敏感目录
        dirnames[:] = [d for d in dirnames if str(dp / d) not in SKIP_DIRS]
        # 只统计常见大目录，避免全盘统计太慢
        try:
            for f in filenames:
                if f in SKIP_NAMES:
                    continue
                fp = dp / f
                try:
                    size = fp.stat(follow_symlinks=False).st_size
                    scanned += 1
                    if size >= min_bytes:
                        big_files.append((size, fp))
                    # 目录大小统计（按一级子目录聚合）
                    parts = fp.parts
                    if len(parts) >= 3:
                        key = parts[1] if len(parts) > 2 else dp
                        dir_sizes[key] = dir_sizes.get(key, 0) + size
                except OSError:
                    errors += 1
        except OSError:
            errors += 1
        if scanned % 50000 == 0 and scanned > 0:
            print(f"[{time.time()-t0:.0f}s] 已扫描 {scanned} 个文件, 发现大文件 {len(big_files)} 个",
                  flush=True)

    big_files.sort(reverse=True)

    lines = [f"# C 盘大文件扫描报告", ""]
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"扫描范围: C:\\ (跳过系统目录)")
    lines.append(f"最小阈值: {args.min_mb} MB")
    lines.append(f"扫描文件数: {scanned:,} | 大文件数: {len(big_files):,} | 耗时: {time.time()-t0:.0f}s")
    lines.append("")

    lines.append("## 一、单个大文件 TOP 60")
    lines.append("")
    lines.append("| 大小 | 路径 | 类别 |")
    lines.append("|---|---|---|")
    for size, fp in big_files[:60]:
        lines.append(f"| {fmt_size(size)} | `{fp}` | {classify(fp)} |")
    lines.append("")

    lines.append("## 二、顶层目录占用统计 TOP 30")
    lines.append("")
    lines.append("| 目录 | 大小 |")
    lines.append("|---|---|")
    for d, s in sorted(dir_sizes.items(), key=lambda x: -x[1])[:30]:
        lines.append(f"| `C:/{d}/` | {fmt_size(s)} |")
    lines.append("")

    report = "\n".join(lines)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"\n扫描完成: {len(big_files)} 个大文件, 报告已保存: {out}")
    print(f"总计可看大小: {fmt_size(sum(s for s, _ in big_files))}")


if __name__ == "__main__":
    main()
