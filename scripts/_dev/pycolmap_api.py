import pycolmap
import numpy as np
recon = pycolmap.Reconstruction(r"C:/Users/luyicheng/Desktop/3dscanner/output/sparse/0")
img = list(recon.images.values())[0]
print("Image attrs:", [x for x in dir(img) if not x.startswith('_')])
print()
cam = list(recon.cameras.values())[0]
print("Camera attrs:", [x for x in dir(cam) if not x.startswith('_')])
print()
p3 = list(recon.points3D.values())[0]
print("Point3D attrs:", [x for x in dir(p3) if not x.startswith('_')])
print()
# 测试读取位姿
print("cam_from_world type:", type(img.cam_from_world))
