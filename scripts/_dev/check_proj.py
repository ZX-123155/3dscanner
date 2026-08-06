"""检查 COLMAP 坐标下 3D 点投影到图像的位置（验证 K/位姿是否正确）"""
import sys
sys.path.insert(0, r"C:/Users/luyicheng/Desktop/3dscanner/scripts")
import numpy as np
import pycolmap
from pathlib import Path
from train_3dgs import load_colmap_data

data = load_colmap_data(Path(r"C:/Users/luyicheng/Desktop/3dscanner/output/sparse/0"),
                        Path(r"C:/Users/luyicheng/Desktop/3dscanner/output/images"), max_size=1024)
i = 0
K = data["Ks"][i]
c2w = data["c2ws"][i]
w2c = np.linalg.inv(c2w)
pts = data["init_points"]
med = np.median(pts, axis=0)
d = np.linalg.norm(pts - med, axis=1)
inlier = pts[d < 5*np.median(d)]
print("K:", K[0,0], K[0,2], K[1,2], "img:", data["images"][i].shape)
# 投影到相机坐标系
pts_cam = (w2c[:3,:3] @ inlier.T + w2c[:3,3:4]).T
print("cam space z range:", pts_cam[:,2].min(), pts_cam[:,2].max())
front = pts_cam[pts_cam[:,2] > 0.1]
print("front points:", len(front))
if len(front) > 0:
    x = K[0,0]*front[:,0]/front[:,2] + K[0,2]
    y = K[1,1]*front[:,1]/front[:,2] + K[1,2]
    inside = (x>0)&(x<1024)&(y>0)&(y<768)
    print("projected inside image:", inside.sum(), "/", len(front))
    if inside.sum():
        print("x range:", x[inside].min(), x[inside].max())
        print("y range:", y[inside].min(), y[inside].max())
