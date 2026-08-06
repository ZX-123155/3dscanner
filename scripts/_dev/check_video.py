import imageio
import numpy as np
vid = imageio.get_reader(r'C:/Users/luyicheng/Desktop/3dscanner/models/3dgs/orbit.mp4')
meta = vid.get_meta_data()
print('frames:', meta.get('nframes'), 'fps:', meta.get('fps'), 'size:', meta.get('size'))
frame = vid.get_data(0)
print('frame shape:', frame.shape, 'mean:', frame.mean(), 'std:', frame.std())
# 提取中间帧看看
for i in [0, 30]:
    f = vid.get_data(i)
    print(f'frame {i} mean:', f.mean(), 'std:', f.std())
