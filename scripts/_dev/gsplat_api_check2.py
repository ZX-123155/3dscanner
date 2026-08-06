import gsplat
import pkgutil
# 找 ssim
for m in dir(gsplat):
    if 'ssim' in m.lower() or 'psnr' in m.lower():
        print("gsplat:", m)
# 检查子模块
try:
    from gsplat import metrics
    print("metrics:", [x for x in dir(metrics) if not x.startswith('_')])
except Exception as e:
    print("metrics fail:", e)
import inspect
from gsplat.exporter import export_splats
print(inspect.signature(export_splats))
from gsplat.strategy import DefaultStrategy
print("DefaultStrategy init:", inspect.signature(DefaultStrategy.__init__))
