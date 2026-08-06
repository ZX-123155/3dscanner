"""调试 orbit 渲染为什么黑"""
import sys
sys.path.insert(0, r"C:\Users\luyicheng\Desktop\3dscanner\scripts")
import numpy as np
import torch
from pathlib import Path
from train_3dgs import load_colmap_data
from gsplat import rasterization

device = "cuda"
data = load_colmap_data(Path(r"C:\Users\luyicheng\Desktop\3dscanner\output\sparse\0"),
                        Path(r"C:\Users\luyicheng\Desktop\3dscanner\output\images"), max_size=1024)
params = torch.load(r"C:\Users\luyicheng\Desktop\3dscanner\models\3dgs_v5\model.pt", map_location=device)

# 训练视角渲染（应该能看到内容）
i = 0
K = torch.tensor(data["Ks"][i], dtype=torch.float32, device=device).unsqueeze(0)
w2c = torch.linalg.inv(torch.tensor(data["c2ws"][i], dtype=torch.float32, device=device)).unsqueeze(0)
h, w = 768, 1024
with torch.no_grad():
    c1, _, _ = rasterization(
        params["means"], params["quats"], torch.exp(params["scales"]), torch.sigmoid(params["opacities"]), params["colors"],
        viewmats=w2c, Ks=K, width=w, height=h, sh_degree=None,
        backgrounds=torch.zeros(3, device=device))
print(f"训练视角渲染: mean={c1.mean().item():.4f}")

# orbit 视角（复刻 render_360 逻辑）
pts = params["means"].detach().cpu().numpy()
center = torch.tensor(np.median(pts, axis=0), dtype=torch.float32)
all_c2w = torch.tensor(data["c2ws"], dtype=torch.float32)
dists = torch.norm(all_c2w[:, :3, 3] - center, dim=1)
radius = torch.median(dists).item()
print(f"center={center} radius={radius}")

up = torch.tensor([0.0, 1.0, 0.0], dtype=torch.float32)
# 尝试多个角度
for i in [0, 15]:
    theta = 2 * np.pi * i / 60
    cam_pos = center + torch.tensor([radius * np.cos(theta), 0.0, radius * np.sin(theta)], dtype=torch.float32)
    forward = (center - cam_pos) / torch.norm(center - cam_pos)
    right = torch.cross(forward, up)
    right = right / torch.norm(right)
    new_up = torch.cross(right, forward)
    rot = torch.stack([right, new_up, forward], dim=1)
    c2w = torch.eye(4)
    c2w[:3, :3] = rot
    c2w[:3, 3] = cam_pos
    viewmat = torch.linalg.inv(c2w).to(device).unsqueeze(0)
    with torch.no_grad():
        c2_, _, _ = rasterization(
            params["means"], params["quats"], torch.exp(params["scales"]), torch.sigmoid(params["opacities"]), params["colors"],
            viewmats=viewmat, Ks=K, width=w, height=h, sh_degree=None,
            backgrounds=torch.zeros(3, device=device))
    print(f"orbit 角度 {i}: mean={c2_.mean().item():.4f}")

# 检查 orbit 相机空间里点是否在前方
w2c_orbit = torch.linalg.inv(c2w)
pts_np = params["means"].detach().cpu().numpy()
pts_cam = (w2c_orbit[:3,:3].cpu().numpy() @ pts_np.T + w2c_orbit[:3,3:4].cpu().numpy()).T
print(f"orbit cam z range: {pts_cam[:,2].min():.3f} {pts_cam[:,2].max():.3f}")
print(f"orbit cam z>0: {(pts_cam[:,2]>0.1).sum()} / {len(pts_np)}")
