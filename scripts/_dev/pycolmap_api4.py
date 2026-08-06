import pycolmap
recon = pycolmap.Reconstruction(r"C:/Users/luyicheng/Desktop/3dscanner/output/sparse/0")
img = list(recon.images.values())[0]
rot = img.cam_from_world().rotation
print("quat:", rot.quat, "type:", type(rot.quat))
print("quat len:", len(rot.quat))
