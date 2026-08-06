import inspect
from gsplat import rasterization
src = inspect.getsource(rasterization)
lines = src.split('\n')
for i, l in enumerate(lines[260:330], start=260):
    print(i, l)
