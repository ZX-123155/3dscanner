import torch
from gsplat import rasterization

device = "cuda"
N = 100
means = (torch.randn(N, 3, device=device) * 0.3).requires_grad_(True)
quats = torch.tensor([1.,0.,0.,0.], device=device).repeat(N,1).requires_grad_(True)
scales = torch.log(torch.full((N,3), 0.2, device=device)).requires_grad_(True)
opacities = torch.full((N,), 10.0, device=device).requires_grad_(True)
colors = torch.rand(N, 1, 3, device=device).requires_grad_(True)

viewmat = torch.eye(4, device=device)
viewmat[2, 3] = -3.0
viewmat = viewmat.unsqueeze(0)  # (1,4,4)
K = torch.tensor([[[500.,0.,256.],[0.,500.,256.],[0.,0.,1.]]], device=device)  # (1,3,3)
print("means shape:", means.shape)
print("viewmat shape:", viewmat.shape)
print("K shape:", K.shape)

# 尝试直接调用查看 batch_dims 推导
import inspect
src = inspect.getsource(rasterization)
lines = src.split('\n')
for l in lines[225:245]:
    print(l)
