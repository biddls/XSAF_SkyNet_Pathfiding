import numpy as np
from numba import jit
import _pathFinding
import cv2


@jit(nopython=True, nogil=True)
def create_circular_mask(_Y, _X, x, y, radius, strength):
    dist_from_center = np.clip((radius - np.sqrt(((x - _X) ** 2) + ((y - _Y) ** 2))) / radius, 0, radius)
    # dist_from_center[dist_from_center < 0] = 0
    return strength * dist_from_center


def slope(x1, y1, x2, y2):
    if x2 - x1 != 0:
        return (y2 - y1) / (x2 - x1)
    else:
        return float("inf")


def compressPath(points):
    yield [points[0]]
    grad = None
    prev0 = None
    prev1 = None
    for points in points:
        if grad is not None:
            prev2 = points
            _temp = slope(*prev1, *prev2)
            grad = slope(*prev0, *prev1)

            prev0 = prev1
            prev1 = prev2
            if _temp == grad:
                continue
            else:
                yield prev0
        if prev0 is None:
            prev0 = points
            continue
        if prev0 is not None:
            grad = slope(*prev0, *points)
            prev1 = points
    yield [points[-1]]


def pathFind(_mask, _start, _end, maxDangerLevel=0, logging=False):
    # _mask > maxDangerLevel
    return _pathFinding.pathFind(_start, _end[::-1], _mask > maxDangerLevel, _pathFinding.astar, trackSteps=logging)