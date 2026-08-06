import gsplat, inspect
print("has ssim:", hasattr(gsplat, 'ssim'))
print("has DefaultStrategy:", hasattr(gsplat, 'DefaultStrategy'))
try:
    from gsplat.exporter import export_splats
    print("export_splats sig:", inspect.signature(export_splats))
except Exception as e:
    print("export_splats fail:", e)
try:
    s = gsplat.DefaultStrategy()
    print("DefaultStrategy OK, steps:", s.refine_start_iter, s.refine_stop_iter)
except Exception as e:
    print("DefaultStrategy fail:", e)
