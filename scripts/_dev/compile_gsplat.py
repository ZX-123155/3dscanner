import os
os.environ["CUDA_HOME"] = r"C:/Users/luyicheng/miniconda3/envs/3dscanner"
os.environ["TORCH_CUDA_ARCH_LIST"] = "8.6"
os.environ["FAST_COMPILE"] = "1"
from gsplat.cuda._backend import _C
print("gsplat CUDA extension compiled OK:", _C)
import gsplat
print("has ssim:", hasattr(gsplat, 'ssim'))
