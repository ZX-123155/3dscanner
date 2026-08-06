"""从训练好的 model.pt 导出 PLY（不重新训练）"""
import torch
from gsplat.exporter import export_splats

device = "cuda"
params = torch.load(r"C:/Users/luyicheng/Desktop/3dscanner/models/3dgs/model.pt", map_location=device)
print("loaded params:", {k: v.shape for k, v in params.items()})

n = params["means"].shape[0]
shN = torch.zeros(n, 0, 3, device=device)
export_splats(
    means=params["means"],
    scales=torch.exp(params["scales"]),
    quats=params["quats"],
    opacities=torch.sigmoid(params["opacities"]),
    sh0=params["sh0"],
    shN=shN,
    format="ply",
    save_to=r"C:/Users/luyicheng/Desktop/3dscanner/models/3dgs/model.ply",
)
print("PLY exported OK")
