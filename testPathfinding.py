import time

from tqdm import tqdm

from main import finder
import numpy as np
from itertools import combinations


_finder = finder("pocmap.png")
_finder.newData("test.lua")

L = np.ogrid[:10]
X2D, Y2D = np.meshgrid(L, L)
Z = np.column_stack((Y2D.ravel(), X2D.ravel()))
_arr = list(combinations(Z, 2))
_arr = np.array(_arr)

_arr[:, 0] = tuple(np.interp(_arr[:, 0], (0, 20), (-744900, 744800)).astype(int))
_arr[:, 1] = tuple(np.interp(_arr[:, 1], (0, 20), (-339400, 245550)).astype(int))

for index, x in enumerate(pbar := tqdm(_arr)):
    # print(str(x).replace('\n', ''))
    # exit(0)
    try:
        _finder.findPathCord(x)
    except:
        pass
    if index % 100 == 0:
        pbar.set_description(str(x).replace('\n', ''))

    # 4950 paths tool 9m 17s
    # 8.8 paths per second on average
    # map split up into 10X10 then all combinations of points are calculated and pathed between them
