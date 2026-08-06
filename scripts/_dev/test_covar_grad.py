"""测试 gsplat 核心函数梯度是否流动"""
import torch
from gsplat import quat_scale_to_covar_preci

device = "cuda"
quats = torch.tensor([1.,0.,0.,0.], device=device).repeat(5,1).requires_grad_(True)
scales = torch.log(torch.full((5,3), 0.1, device=device)).requires_grad_(True)

covars, precisions = quat_scale_to_covar_preci(quats, scales, True, True)
loss = covars.sum() + (precisions.sum() if precisions is not None else 0)
loss.backward()
print("quats.grad:", quats.grad.abs().sum().item())
print("scales.grad:", scales.grad.abs().sum().item())
print("covar grad OK" if quats.grad.abs().sum() > 0 else "covar grad ZERO")
