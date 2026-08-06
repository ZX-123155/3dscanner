import inspect
from gsplat.strategy import DefaultStrategy, Strategy
print("Strategy.check_sanity source:")
print(inspect.getsource(Strategy.check_sanity))
