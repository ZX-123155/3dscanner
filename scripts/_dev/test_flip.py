"""测试坐标系翻转组合，找正确的 viewmat 约定"""
import sys
sys.path.insert(0, r"C:/Users/luyicheng/Desktop/3dscanner/scripts")
import numpy as np
import torch
from pathlib import Path
from train_3dgs import load_colmap_data
from gsplat import rasterization

device = "cuda"
data = load_colmap_data(Path(r"C:/Users/luyicheng/Desktop/3dscanner/output/sparse/0"),
                        Path(r"C:/Users/luyicheng/Desktop/3dscanner/output/images"), max_size=1024)
params = torch.load(r"C:/Users/luyicheng/Desktop/3dscanner/models/3dgs_v3/model.pt", map_location=device)

i = 0
img = torch.tensor(data["images"][i], dtype=torch.float32, device=device)
K = torch.tensor(data["Ks"][i], dtype=torch.float32, device=device).unsqueeze(0)
c2w = torch.tensor(data["c2ws"][i], dtype=torch.float32, device=device)
w2c = torch.linalg.inv(c2w).unsqueeze(0)
h, w = img.shape[0], img.shape[1]

# 尝试不同翻转组合（OpenGL vs COLMAP 约定）
flips = {
    "none": torch.eye(4, device=device),
    "flip_yz": torch.diag(torch.tensor([1., -1., -1., 1.], device=device)),
    "flip_y": torch.diag(torch.tensor([1., -1., 1., 1.], device=device)),
    "flip_z": torch.diag(torch.tensor([1., 1., -1., 1.], device=device)),
}
for name, F in flips.items():
    vm = F.unsqueeze(0) @ w2c
    with torch.no_grad():
        colors, alphas, info = rasterization(
            params["means"], params["quats"], params["scales"], params["opacities"], params["sh0"],
            viewmats=vm, Ks=K, width=w, height=h, sh_degree=0,
            backgrounds=torch.zeros(3, device=device))
    print(f"{name}: mean={colors.mean().item():.4f} max={colors.max().item():.4f}")
