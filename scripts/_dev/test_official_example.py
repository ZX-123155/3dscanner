"""gsplat 官方 README 最小示例"""
import torch
from gsplat import rasterization

device = "cuda"
B = 1
C = 1
N = 1000
means = torch.randn(N, 3, device=device) * 0.3
quats = torch.tensor([1.0, 0.0, 0.0, 0.0], device=device).repeat(N, 1)
scales = torch.randn(N, 3, device=device) * 0.01
opacities = torch.rand(N, device=device)
colors = torch.rand(N, 3, device=device)  # 官方示例用 (N,3)！

viewmats = torch.eye(4, device=device)[None, :, :]  # (1,4,4)
Ks = torch.tensor([[500.0, 0, 256], [0, 500, 256], [0, 0, 1]], device=device)[None, :, :]  # (1,3,3)
width, height = 512, 512

renders, alphas, meta = rasterization(
    means=means, quats=quats, scales=scales, opacities=opacities, colors=colors,
    viewmats=viewmats, Ks=Ks, width=width, height=height, sh_degree=None,
)
print("render mean:", renders.mean().item(), "max:", renders.max().item())
print("alpha mean:", alphas.mean().item())
print("render shape:", renders.shape)

# 梯度测试
means2 = means.clone().requires_grad_(True)
opacities2 = opacities.clone().requires_grad_(True)
renders2, _, _ = rasterization(
    means=means2, quats=quats, scales=scales, opacities=opacities2, colors=colors,
    viewmats=viewmats, Ks=Ks, width=width, height=height, sh_degree=None)
loss = renders2.sum()
loss.backward()
print("means2.grad nonzero:", means2.grad.abs().sum().item())
print("opacities2.grad nonzero:", opacities2.grad.abs().sum().item())
