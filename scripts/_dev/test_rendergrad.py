"""最小渲染 backward 测试"""
import torch
import torch.nn.functional as F
from gsplat import rasterization

device = "cuda"
N = 100
means = (torch.randn(N, 3, device=device) * 0.3).requires_grad_(True)
quats = torch.tensor([1.,0.,0.,0.], device=device).repeat(N,1).requires_grad_(True)
scales = torch.log(torch.full((N,3), 0.2, device=device)).requires_grad_(True)
opacities = torch.full((N,), 10.0, device=device).requires_grad_(True)
colors = torch.rand(N, 1, 3, device=device).requires_grad_(True)

viewmat = torch.eye(4, device=device)
viewmat[2, 3] = -3.0  # 相机 z=3
viewmat = viewmat.unsqueeze(0)
K = torch.tensor([[[500.,0.,256.],[0.,500.,256.],[0.,0.,1.]]], device=device)
gt = torch.full((1,512,512,3), 0.5, device=device)

out, alpha, info = rasterization(means, quats, scales, opacities, colors,
    viewmats=viewmat, Ks=K, width=512, height=512, sh_degree=0,
    backgrounds=torch.zeros(3, device=device))
loss = F.l1_loss(out, gt)
print("render mean:", out.mean().item(), "loss:", loss.item())
loss.backward()
print("means grad:", means.grad.abs().sum().item())
print("quats grad:", quats.grad.abs().sum().item())
print("scales grad:", scales.grad.abs().sum().item())
print("opacities grad:", opacities.grad.abs().sum().item())
print("colors grad:", colors.grad.abs().sum().item())
