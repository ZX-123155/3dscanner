import torch
from gsplat import rasterization
# 快速渲染测试
N = 1000
means = torch.randn(N, 3, device='cuda')
quats = torch.tensor([1.,0.,0.,0.], device='cuda').repeat(N,1)
scales = torch.full((N,3), -3.0, device='cuda')
opacities = torch.full((N,), 0.5, device='cuda')
colors = torch.rand(N, 1, 3, device='cuda')
viewmats = torch.eye(4, device='cuda').unsqueeze(0)
Ks = torch.tensor([[500.,0.,256.],[0.,500.,256.],[0.,0.,1.]], device='cuda').unsqueeze(0)
out, alpha, _ = rasterization(means, quats, scales, opacities, colors,
    viewmats=viewmats, Ks=Ks, width=512, height=512, sh_degree=0)
print('render OK:', out.shape, 'mean color:', out.mean().item())
