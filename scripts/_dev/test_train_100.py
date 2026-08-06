"""100 步训练测试：验证 loss 是否下降（参数是否更新）"""
import sys
sys.path.insert(0, r"C:\Users\luyicheng\Desktop\3dscanner\scripts")
import torch
import numpy as np
import torch.nn.functional as F
from pathlib import Path
from train_3dgs import load_colmap_data, ssim_loss, get_camera_rays
from gsplat import rasterization, DefaultStrategy
from torch.optim import Adam

device = "cuda"
data = load_colmap_data(Path(r"C:\Users\luyicheng\Desktop\3dscanner\output\sparse\0"),
                        Path(r"C:\Users\luyicheng\Desktop\3dscanner\output\images"), max_size=1024)
N_imgs = len(data["images"])

pts = data["init_points"]
med = np.median(pts, axis=0)
dists = np.linalg.norm(pts - med, axis=1)
inlier = dists < 5.0 * np.median(dists)
pts_clean = pts[inlier]
cols_clean = data["init_colors"][inlier]
n_init = min(len(pts_clean), 100_000)
idx = np.random.choice(len(pts_clean), n_init, replace=False)
means = torch.tensor(pts_clean[idx], dtype=torch.float32, device=device)
init_colors = torch.tensor(cols_clean[idx], dtype=torch.float32, device=device)
params = {
    "means": means.clone().requires_grad_(True),
    "scales": torch.log(torch.full((n_init, 3), 0.05, device=device)).requires_grad_(True),
    "quats": torch.tensor([1.0, 0.0, 0.0, 0.0], device=device).repeat(n_init, 1).requires_grad_(True),
    "opacities": torch.logit(torch.full((n_init,), 0.5, device=device)).requires_grad_(True),
    "sh0": init_colors.unsqueeze(1).clone().requires_grad_(True),
}
optimizer = {
    "means": Adam([params["means"]], lr=1.6e-4),
    "scales": Adam([params["scales"]], lr=5e-3),
    "quats": Adam([params["quats"]], lr=1e-3),
    "opacities": Adam([params["opacities"]], lr=5e-2),
    "sh0": Adam([params["sh0"]], lr=2.5e-3),
}
strategy = DefaultStrategy(verbose=False, absgrad=True)
state = strategy.initialize_state()

viewmats, Ks = [], []
for i in range(N_imgs):
    v, k = get_camera_rays(data["c2ws"][i], data["Ks"][i], data["images"][i].shape[1], data["images"][i].shape[0])
    viewmats.append(v.to(device))
    Ks.append(k.to(device))

losses = []
for step in range(1, 101):
    i = np.random.randint(N_imgs)
    gt = torch.tensor(data["images"][i], dtype=torch.float32, device=device).unsqueeze(0)
    K = Ks[i].unsqueeze(0)
    vm = viewmats[i].unsqueeze(0)
    h, w = gt.shape[1], gt.shape[2]
    colors, alphas, info = rasterization(
        params["means"], params["quats"], params["scales"], params["opacities"], params["sh0"],
        viewmats=vm, Ks=K, width=w, height=h, sh_degree=0,
        backgrounds=torch.zeros(3, device=device), absgrad=True)
    loss = 0.8 * F.l1_loss(colors, gt) + 0.2 * ssim_loss(colors, gt)
    strategy.step_pre_backward(params, optimizer, state, step, info)
    loss.backward()
    strategy.step_post_backward(params, optimizer, state, step, info, packed=True)
    for opt in optimizer.values():
        opt.step()
        opt.zero_grad(set_to_none=True)
    losses.append(loss.item())
    if step % 20 == 0:
        print(f"step {step}: loss={loss.item():.4f} opa={torch.sigmoid(params['opacities']).mean().item():.4f}")

print(f"loss[0]={losses[0]:.4f} loss[-1]={losses[-1]:.4f}")
print(f"opa end={torch.sigmoid(params['opacities']).mean().item():.4f}")
