"""用训练相机位姿直接渲染，定位黑屏问题（v2）"""
import sys
sys.path.insert(0, r"C:\Users\luyicheng\Desktop\3dscanner\scripts")
import torch
from pathlib import Path
from train_3dgs import load_colmap_data
from gsplat import rasterization

device = "cuda"
data = load_colmap_data(Path(r"C:\Users\luyicheng\Desktop\3dscanner\output\sparse\0"),
                        Path(r"C:\Users\luyicheng\Desktop\3dscanner\output\images"), max_size=1024)
params = torch.load(r"C:\Users\luyicheng\Desktop\3dscanner\models\3dgs_v2\model.pt", map_location=device)
print("params means range:", params["means"].min(0).values, params["means"].max(0).values)
print("opacities sigmoid mean:", torch.sigmoid(params["opacities"]).mean().item())
print("scales exp mean:", torch.exp(params["scales"]).mean(0))

# 用训练视角 0 渲染
i = 0
img = torch.tensor(data["images"][i], dtype=torch.float32, device=device)
K = torch.tensor(data["Ks"][i], dtype=torch.float32, device=device).unsqueeze(0)
c2w = torch.tensor(data["c2ws"][i], dtype=torch.float32, device=device)
viewmat = torch.linalg.inv(c2w).unsqueeze(0)
h, w = img.shape[0], img.shape[1]
print("K[0,0]:", K[0,0,0].item(), "w:", w, "h:", h)

with torch.no_grad():
    colors, alphas, info = rasterization(
        params["means"], params["quats"], params["scales"], params["opacities"], params["sh0"],
        viewmats=viewmat, Ks=K, width=w, height=h, sh_degree=0,
        backgrounds=torch.zeros(3, device=device))
print("render mean:", colors.mean().item(), "max:", colors.max().item())
print("num rendered:", info["n_rendered"])
from PIL import Image
import numpy as np
out = (colors[0].clamp(0,1).cpu().numpy()*255).astype(np.uint8)
Image.fromarray(out).save(r"C:\Users\luyicheng\Desktop\3dscanner\output\debug_render2.png")
print("saved debug_render2.png")
