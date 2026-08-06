from PIL import Image
from pathlib import Path
import os
d = Path(r"C:/Users/luyicheng/Desktop/3dscanner/input")
imgs = sorted(d.iterdir())[:5]
for i in imgs:
    with Image.open(i) as im:
        print(i.name, im.size, im.mode)
