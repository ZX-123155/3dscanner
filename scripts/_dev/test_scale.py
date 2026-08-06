"""放大高斯参数测试渲染是否可见"""
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
K = torch.tensor(data["Ks"][i], dtype=torch.float32, device=device).unsqueeze(0)
c2w = torch.tensor(data["c2ws"][i], dtype=torch.float32, device=device)
w2c = torch.linalg.inv(c2w).unsqueeze(0)
h, w = 768, 1024

# 测试 1: 原始参数
with torch.no_grad():
    c1, _, _ = rasterization(params["means"], params["quats"], params["scales"], params["opacities"], params["sh0"],
        viewmats=w2c, Ks=K, width=w, height=h, sh_degree=0, backgrounds=torch.zeros(3, device=device))
print(f"原始: mean={c1.mean().item():.4f}")

# 测试 2: scales 放大 10 倍
scales_big = params["scales"] + np.log(10)
with torch.no_grad():
    c2, _, _ = rasterization(params["means"], params["quats"], scales_big, params["opacities"], params["sh0"],
        viewmats=w2c, Ks=K, width=w, height=h, sh_degree=0, backgrounds=torch.zeros(3, device=device))
print(f"scales x10: mean={c2.mean().item():.4f}")

# 测试 3: opacities 拉满
opa_max = torch.full_like(params["opacities"], 10.0)
with torch.no_grad():
    c3, _, _ = rasterization(params["means"], params["quats"], scales_big, opa_max, params["sh0"],
        viewmats=w2c, Ks=K, width=w, height=h, sh_degree=0, backgrounds=torch.zeros(3, device=device))
print(f"scales x10 + opa=max: mean={c3.mean().item():.4f} max={c3.max().item():.4f}")

# 测试 4: 用 sh0 颜色而非默认
print("sh0 mean:", params["sh0"].mean().item())
