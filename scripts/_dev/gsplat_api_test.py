import inspect
import gsplat
print("gsplat exports:", [x for x in dir(gsplat) if not x.startswith('_')][:30])
from gsplat import rasterization
sig = inspect.signature(rasterization)
print("\nrasterization params:")
for name, p in sig.parameters.items():
    print(f"  {name}: {p.default if p.default is not inspect.Parameter.empty else '<required>'}")
