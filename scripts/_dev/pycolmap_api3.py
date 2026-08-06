import pycolmap
recon = pycolmap.Reconstruction(r"C:/Users/luyicheng/Desktop/3dscanner/output/sparse/0")
img = list(recon.images.values())[0]
rot = img.cam_from_world().rotation
print("Rotation3d attrs:", [x for x in dir(rot) if not x.startswith('_')])
print("str:", rot)
print("matrix:", rot.matrix())
