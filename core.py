import time

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import luadata
import json

from numba import jit, prange

import _pathFinding
import cv2


def NormalizeData(data, scale=255):
    if scale > 1:
        return np.round(scale * ((data - np.min(data)) / (np.max(data) - np.min(data))))
    elif scale <= 1:
        return scale * ((data - np.min(data)) / (np.max(data) - np.min(data)))
    else:
        raise ValueError("Scale has to be greater than 0")


@jit(nopython=True, nogil=True)
def create_circular_mask(_Y, _X, center, radius, strength):
    dist_from_center = np.clip((radius - np.sqrt((_X - center[0]) ** 2 + (_Y - center[1]) ** 2)) / radius, 0, radius)
    return strength * dist_from_center


def slope(x1, y1, x2, y2):
    if x2 - x1 != 0:
        return (y2 - y1) / (x2 - x1)
    else:
        return float("inf")


def compressPath(x_cords, y_cords):
    yield [x_cords[0], y_cords[0]]
    grad = None
    prev0 = None
    prev1 = None
    for points in zip(x_cords, y_cords):
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
    yield [x_cords[-1], y_cords[-1]]


# todo: this (mby)
def doubleCompress(x_cords, y_cords):
    pass


def pathFind(_mask, _start, _end, maxDangerLevel=0, logging=False):
    return _pathFinding.pathFind(_start, _end[::-1], _mask > maxDangerLevel, _pathFinding.astar)


@jit(nopython=True)
def genColourMask(mask):
    mask = np.clip(mask, -1, 1)
    colourMask = np.zeros((*mask.shape, 4), dtype=np.uint8)

    # mask = dist_from_center <= radius
    # mask = mask * dist_from_center
    for indexx, x in enumerate(mask):
        for indexy, y in enumerate(x):
            colourMask[indexx][indexy] = [255, 0, 0, int(y * 255)]

    return colourMask


# xRng=(-744878, 744878), yRng=(-339322, 245600)
# int(_canvasShape[d] * (d - dRng[0]) / (dRng[1] - dRng[0]))
# self.scaler=0.0014772583309862865
# self.mapImg.shape[:2]=(866, 2200)

@jit(nopython=True)
def cordToPix(_x, _y, _range):
    _x = int((_x + 744878) / 677.16)
    _y = int((_y + 339322) / 675.43)
    return _x, _y, int(_range * 0.0014772)


def calcScale(canvas, xRng=(-744878, 744878), yRng=(-339322, 245600)):
    length = lambda x, y: min(x, y) - max(x, y)
    dist = lambda x, y: np.sqrt(x ** 2 + y ** 2)
    mapDist = dist(length(*xRng), length(*yRng))
    canvasDist = dist(*canvas.shape[:2])
    return canvasDist / mapDist


def plots(_img, _colourMask, _mask, _maskMap=True):
    if _maskMap:
        fig, ax = plt.subplots(2)
        ax[0].imshow(_img, extent=[-744878, 744878, -339322, 245600])
        ax[0].imshow(_colourMask, extent=[-744878, 744878, -339322, 245600], alpha=0.5)
        ax[0].title.set_text("0")
        ax[1].imshow(_mask)
        ax[1].title.set_text("1")
    else:
        plt.imshow(_img, extent=[-744878, 744878, -339322, 245600])
        plt.imshow(_colourMask, extent=[-744878, 744878, -339322, 245600], alpha=0.5)

    plt.show()


if __name__ == "__main__":
    img = mpimg.imread('pocmap.png')
    data = json.loads(json.dumps(luadata.read("test.lua", encoding="utf-8"), indent=4))
    scaler = calcScale(img)
    _shape = img.shape
    mask = np.zeros(_shape[:2], dtype=np.float64)
    Y, X = np.ogrid[:_shape[0], :_shape[1]]
    for objKey in data.keys():
        obj = [*data[objKey].values()]
        obj = cordToPix(*obj)
        mask += create_circular_mask(Y, X, obj[:2], obj[2], 1)

    _start = (1265, 217)
    _end = (1160, 746)
    pathFind(img, mask, _start, _end, show=True)
