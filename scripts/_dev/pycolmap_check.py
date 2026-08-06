import pycolmap, inspect
print("write signature:", inspect.signature(pycolmap.Reconstruction.write))
# 看看有没有 Read/Write 工具函数
print("pycolmap exports:", [x for x in dir(pycolmap) if 'read' in x.lower() or 'write' in x.lower()])
