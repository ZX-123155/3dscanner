import pycolmap
recon = pycolmap.Reconstruction(r"C:/Users/luyicheng/Desktop/3dscanner/output/sparse/0")
img = list(recon.images.values())[0]
pose = img.cam_from_world()
print("pose type:", type(pose))
print("pose attrs:", [x for x in dir(pose) if not x.startswith('_')])
print("rot:", pose.rotation)
print("trans:", pose.translation)
print("qvec:", pose.qvec if hasattr(pose, 'qvec') else 'n/a')
print("rvec:", pose.rvec if hasattr(pose, 'rvec') else 'n/a')
