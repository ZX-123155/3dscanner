"""检查 backward 后梯度是否存在"""
import sys
sys.path.insert(0, r"C:\Users\luyicheng\Desktop\3dscanner\scripts")
import torch
import numpy as np
import torch.nn.functional as F
from pathlib import Path
from train_3dgs import load_colmap_data, ssim_loss, get_camera_rays
from gsplat import rasterization

device = "cuda"
data = load_colmap_data(Path(r"C:\Users\luyicheng\Desktop\3dscanner\output\sparse\0"),
                        Path(r"C:\Users\luyicheng\Desktop\3dscanner\output\images"), max_size=1024)

# 用少量高斯（1000 个）加速
pts = data["init_points"]
med = np.median(pts, axis=0)
d = np.linalg.norm(pts - med, axis=1)
inlier = pts[d < 5*np.median(d)]
idx = np.random.choice(len(inlier), 2000, replace=False)
means = torch.tensor(inlier[idx], dtype=torch.float32, device=device, requires_grad=True)
scales = torch.log(torch.full((2000, 3), 0.1, device=device)).requires_grad_(True)
quats = torch.tensor([1.,0.,0.,0.], device=device).repeat(2000,1).requires_grad_(True)
opacities = torch.full((2000,), 10.0, device=device).requires_grad_(True)
colors = torch.rand(2000, 1, 3, device=device).requires_grad_(True)

i = 0
gt = torch.tensor(data["images"][i], dtype=torch.float32, device=device).unsqueeze(0)
K = torch.tensor(data["Ks"][i], dtype=torch.float32, device=device).unsqueeze(0)
vm = torch.linalg.inv(torch.tensor(data["c2ws"][i], dtype=torch.float32, device=device)).unsqueeze(0)
h, w = gt.shape[1], gt.shape[2]

out, alpha, info = rasterization(means, quats, scales, opacities, colors,
    viewmats=vm, Ks=K, width=w, height=h, sh_degree=0,
    backgrounds=torch.zeros(3, device=device))
print("render mean:", out.mean().item(), "max:", out.max().item())
print("info keys:", list(info.keys()))

loss = F.l1_loss(out, gt)
print("loss:", loss.item())
# 检查相机空间坐标
w2c = vm[0].cpu().numpy()
pts_np = means.detach().cpu().numpy()
pts_cam = (w2c[:3, :3] @ pts_np.T + w2c[:3, 3:4]).T
print("cam z range:", pts_cam[:, 2].min(), pts_cam[:, 2].max())
print("cam z > 0 count:", (pts_cam[:, 2] > 0.1).sum(), "/", len(pts_np))
loss.backward()
print("means.grad:", means.grad)
if means.grad is not None:
    print("means.grad nonzero:", means.grad.abs().sum().item())
    print("opacities.grad nonzero:", opacities.grad.abs().sum().item())
    print("scales.grad nonzero:", scales.grad.abs().sum().item())
