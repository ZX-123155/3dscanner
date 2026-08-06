"""重新渲染 orbit 视频（加载已训练模型，修正旋转中心）"""
import sys
sys.path.insert(0, r"C:/Users/luyicheng/Desktop/3dscanner/scripts")
import torch
from pathlib import Path
from train_3dgs import load_colmap_data, render_360

device = "cuda"
data = load_colmap_data(Path(r"C:/Users/luyicheng/Desktop/3dscanner/output/sparse/0"),
                        Path(r"C:/Users/luyicheng/Desktop/3dscanner/output/images"), max_size=1024)
params = torch.load(r"C:/Users/luyicheng/Desktop/3dscanner/models/3dgs/model.pt", map_location=device)
frames = render_360(data, params, num_frames=90, out_path=Path(r"C:/Users/luyicheng/Desktop/3dscanner/models/3dgs/orbit.mp4"), device=device)
print("rendered", len(frames), "frames")

# 验证视频内容
import imageio
vid = imageio.get_reader(r"C:/Users/luyicheng/Desktop/3dscanner/models/3dgs/orbit.mp4")
import numpy as np
for i in [0, 30, 60]:
    f = vid.get_data(i)
    print(f"frame {i}: mean={f.mean():.3f} std={f.std():.3f}")
