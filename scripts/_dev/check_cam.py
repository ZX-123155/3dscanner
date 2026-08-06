"""检查 COLMAP 相机位姿范围，定位 orbit 渲染问题"""
import numpy as np
import pycolmap
import torch

recon = pycolmap.Reconstruction(r"C:/Users/luyicheng/Desktop/3dscanner/output/sparse/0")
c2ws = []
for img in sorted(recon.images.values(), key=lambda im: im.name):
    pose = img.cam_from_world()
    R = np.array(pose.rotation.matrix())
    t = np.array(pose.translation)
    w2c = np.eye(4); w2c[:3,:3] = R; w2c[:3,3] = t
    c2ws.append(np.linalg.inv(w2c))
c2ws = np.array(c2ws)
print('camera positions:')
print('  min:', c2ws[:, :3, 3].min(axis=0))
print('  max:', c2ws[:, :3, 3].max(axis=0))
print('  mean:', c2ws[:, :3, 3].mean(axis=0))
# 点云范围
pts = np.array([p.xyz for p in recon.points3D.values()])
print('point cloud:')
print('  min:', pts.min(axis=0))
print('  max:', pts.max(axis=0))
print('  mean:', pts.mean(axis=0))
center = c2ws[:, :3, 3].mean(axis=0)
dist = np.linalg.norm(c2ws[:, :3, 3] - center, axis=1)
print('camera-center distances: min', dist.min(), 'max', dist.max(), 'mean', dist.mean())
# 相机朝向检查（z 轴指向）
fwd = -c2ws[:, :3, 2]  # 光轴方向（c2w 第三列）
print('view dir mean:', fwd.mean(axis=0))
print('view dir sample:', fwd[0], fwd[50])
