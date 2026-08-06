import gsplat
from gsplat import cuda
print("cuda module:", cuda)
print("_C:", cuda._C if hasattr(cuda, '_C') else 'no _C attr')
import os
print("CUDA_HOME:", os.environ.get('CUDA_HOME'))
print("CUDA_PATH:", os.environ.get('CUDA_PATH'))
print("PATH has nvcc:", any('nvcc' in p.lower() for p in os.environ.get('PATH','').split(';')))
# 检查 wheel 文件
import gsplat.cuda._wrapper as w
print("wrapper file:", w.__file__)
