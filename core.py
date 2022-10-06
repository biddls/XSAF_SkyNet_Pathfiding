import json

import numpy as np
from numba import jit
import _pathFinding
from matplotlib import pyplot as plt
import matplotlib.patches as patches
import ast


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
    yield points[0]
    for a, b, c in zip(points, points[1:], points[2:]):
        if slope(*a, *b) != slope(*b, *c):
            yield b
    yield points[-1]


def CompressPath2(points, maxSkip=3):
    yield points[0]
    sub = lambda x1, y1, x2, y2: maxSkip >= x1-x2 >= -maxSkip and maxSkip >= y1-y2 >= -maxSkip
    for a, b, c, d in zip(points, points[1:], points[2:], points[3:]):
        if not sub(*a, *b):
            yield b
            continue
        if slope(*a, *b) != slope(*c, *d):
            yield b
    yield points[-2]
    yield points[-1]

def CompressPath3(points, mask):
    points = list(points)
    points.append(points[-1])
    points.append(points[-1])
    clear = {}
    step = 0
    for p1, p2, p3 in zip(points, points[1:], points[2:]):
        if _slice(p1, p2, mask) + _slice(p2, p3, mask) > _slice(p1, p3, mask):
            clear[step] = p1
            clear[step + 1] = p3
        elif _slice(p1, p2, mask) + _slice(p2, p3, mask) == 0:
            clear[step] = p1
            clear[step + 1] = p3
        else:
            if step not in list(clear.keys()):
                clear[step] = p1
        step += 1

    if list(clear.keys()):
        clear = np.array(list(clear.values()))
    last = clear[0]
    for x in clear:
        if str(x) != str(last):
            yield last
            last = x
    yield points[-1]


def _slice(p1, p2, arr):
    y1, y2, x1, x2 = min(p2[0], p1[0]), max(p2[0], p1[0]), min(p2[1], p1[1]), max(p2[1], p1[1])
    # temp = np.random.randint(0, 10, arr.shape)
    # temp = np.triu(temp)
    # fig, ax = plt.subplots(2)
    # ax[0].imshow(temp)
    # ax[1].imshow(arr)
    # plt.show()
    return arr[y1:1 + y2, x1:1 + x2].sum()

def pathFind(_mask, _start, _end, maxDangerLevel=0, logging=False):
    return _pathFinding.pathFind(_start, _end[::-1], _mask > maxDangerLevel, _pathFinding.astar, trackSteps=logging)