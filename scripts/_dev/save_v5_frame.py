"""保存 v5 orbit 视频的一帧用于查看"""
import imageio
import numpy as np
from PIL import Image

vid = imageio.get_reader(r"C:/Users/luyicheng/Desktop/3dscanner/models/3dgs_v5/orbit.mp4")
frames = [vid.get_data(i) for i in [0, 10, 20]]
# 拼接 3 帧
h, w = frames[0].shape[:2]
canvas = np.zeros((h, w * 3, 3), dtype=np.uint8)
for i, f in enumerate(frames):
    canvas[:, i*w:(i+1)*w] = f
Image.fromarray(canvas).save(r"C:/Users/luyicheng/Desktop/3dscanner/output/orbit_v5_preview.png")
print("saved", canvas.shape)
