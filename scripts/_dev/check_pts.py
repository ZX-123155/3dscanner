import numpy as np
import pycolmap
recon = pycolmap.Reconstruction(r"C:/Users/luyicheng/Desktop/3dscanner/output/sparse/0")
pts = np.array([p.xyz for p in recon.points3D.values()])
print('total points:', len(pts))
# 用百分位数看分布
for q in [1, 5, 50, 95, 99]:
    print(f'p{q}:', np.percentile(pts, q, axis=0))
# 过滤离群点（±2σ 或 98% 分位）
center = np.median(pts, axis=0)
dist = np.linalg.norm(pts - center, axis=1)
mask = dist < np.percentile(dist, 95)
print('inlier points (95%):', mask.sum())
print('inlier center:', pts[mask].mean(axis=0))
print('inlier range:')
print('  min:', pts[mask].min(axis=0))
print('  max:', pts[mask].max(axis=0))
