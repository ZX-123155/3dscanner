import gsplat, torch
print('gsplat version:', gsplat.__version__)
from gsplat import rasterization
print('rasterization OK')
print('CUDA:', torch.cuda.is_available())
