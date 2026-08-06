"""测试 gsplat 各 kernel 是否可用"""
import torch
from gsplat import quat_scale_to_covar_preci, fully_fused_projection, rasterize_to_pixels
import inspect

device = "cuda"
print("quat_scale_to_covar_preci:", inspect.signature(quat_scale_to_covar_preci))

try:
    quats = torch.tensor([1.,0.,0.,0.], device=device).repeat(5,1)
    scales = torch.log(torch.full((5,3), 0.1, device=device))
    out = quat_scale_to_covar_preci(quats, scales, 0, True)
    print("covar result type:", type(out), [None if o is None else o.shape for o in out])
except Exception as e:
    print("covar FAIL:", e)

# 测试 fully_fused_projection
try:
    means = torch.randn(5, 3, device=device)
    covars = torch.randn(5, 3, 3, device=device)
    viewmats = torch.eye(4, device=device).unsqueeze(0)
    Ks = torch.tensor([[[500.,0.,256.],[0.,500.,256.],[0.,0.,1.]]], device=device)
    res = fully_fused_projection(means, covars, viewmats, Ks, 512, 512)
    print("projection result:", type(res), len(res))
except Exception as e:
    print("projection FAIL:", e)
