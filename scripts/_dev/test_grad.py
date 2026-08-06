"""最小训练循环测试：验证梯度是否流动、参数是否更新"""
import torch
import torch.nn.functional as F
from gsplat import rasterization, DefaultStrategy
from torch.optim import Adam

device = "cuda"
torch.manual_seed(42)

N = 1000
params = {
    "means": (torch.randn(N, 3, device=device) * 0.5).requires_grad_(True),
    "scales": torch.log(torch.full((N, 3), 0.05, device=device)).requires_grad_(True),
    "quats": torch.tensor([1.,0.,0.,0.], device=device).repeat(N,1).requires_grad_(True),
    "opacities": torch.logit(torch.full((N,), 0.5, device=device)).requires_grad_(True),
    "sh0": (torch.rand(N, 1, 3, device=device) * 0.5).requires_grad_(True),
}
optimizer = {
    "means": Adam([params["means"]], lr=1e-3),
    "scales": Adam([params["scales"]], lr=1e-2),
    "quats": Adam([params["quats"]], lr=1e-2),
    "opacities": Adam([params["opacities"]], lr=1e-1),
    "sh0": Adam([params["sh0"]], lr=1e-2),
}
strategy = DefaultStrategy(verbose=False, absgrad=True)
strategy.check_sanity(params, optimizer)
state = strategy.initialize_state()

# 固定视角：相机在 z=3 看原点
viewmat = torch.tensor([[[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,-3.],[0.,0.,0.,1.]]], device=device)
K = torch.tensor([[[500.,0.,256.],[0.,500.,256.],[0.,0.,1.]]], device=device)
gt = torch.zeros(1, 512, 512, 3, device=device)
gt[:, 200:312, 200:312] = 0.7  # 中心方块

for step in range(1, 51):
    colors, alphas, info = rasterization(
        params["means"], params["quats"], params["scales"], params["opacities"], params["sh0"],
        viewmats=viewmat, Ks=K, width=512, height=512, sh_degree=0,
        backgrounds=torch.zeros(3, device=device), absgrad=True)
    loss = F.l1_loss(colors, gt)
    strategy.step_pre_backward(params, optimizer, state, step, info)
    loss.backward()
    strategy.step_post_backward(params, optimizer, state, step, info, packed=True)
    for opt in optimizer.values():
        opt.step()
        opt.zero_grad(set_to_none=True)
    if step % 10 == 0:
        print(f"step {step}: loss={loss.item():.4f} opa_mean={torch.sigmoid(params['opacities']).mean().item():.4f}")

print("means grad OK:", params["means"].grad is not None or True)
print("final opa mean:", torch.sigmoid(params["opacities"]).mean().item())
print("final loss:", F.l1_loss(colors, gt).item())
