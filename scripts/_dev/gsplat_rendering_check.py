import inspect
from gsplat import rasterization
src = inspect.getsource(rasterization)
# 打印关键的 shape 断言部分
lines = src.split('\n')
for i, l in enumerate(lines):
    if 'assert' in l or 'shape' in l.lower() and 'viewmat' in l.lower() or 'batch_dims' in l:
        print(i, l)
