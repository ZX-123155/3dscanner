import pycolmap
recon = pycolmap.Reconstruction(r"C:/Users/luyicheng/Desktop/3dscanner/output/sparse/0")
p3 = list(recon.points3D.values())[0]
els = p3.track.elements
print("elements type:", type(els))
print("elements:", els[:3] if isinstance(els, list) else els)
t = els[0]
print("elem attrs:", [x for x in dir(t) if not x.startswith('_')])
print("elem:", t)
img = list(recon.images.values())[0]
pts = img.points2D
print("points2D len:", len(pts))
p = pts[0]
print("point2D attrs:", [x for x in dir(p) if not x.startswith('_')])
print("point2D:", p)
