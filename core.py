import time

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import luadata
import json

from numba import jit

import _pathFinding
import cv2


def NormalizeData(data, scale=255):
    if scale > 1:
        return np.round(scale * ((data - np.min(data)) / (np.max(data) - np.min(data))))
    elif scale <= 1:
        return scale * ((data - np.min(data)) / (np.max(data) - np.min(data)))
    else:
        raise ValueError("Scale has to be greater than 0")


def create_circular_mask(Y, X, center, radius, strength):
    dist_from_center = (radius - np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)) / radius
    dist_from_center[dist_from_center < 0] = 0
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


def pathFind(img, _mask, _start, _end, scaler=10, maxDangerLevel=0, show=False, logging=False):
    logging = time.time() if logging else logging

    scaleTuple = lambda tup, sc: tuple(int(_x / sc) for _x in tup)
    scaleArr = lambda _arr, sc: [_x * sc for _x in _arr]

    mask = cv2.resize(_mask, dsize=(round(_mask.shape[1] / scaler), round(_mask.shape[0] / scaler)),
                      interpolation=cv2.INTER_NEAREST)
    mask = mask > maxDangerLevel

    y_coords, x_coords = _pathFinding.pathFind(scaleTuple(_start[::-1], scaler), scaleTuple(_end[::-1], scaler), mask)

    # path compression
    x_coords = scaleArr(x_coords, scaler)
    y_coords = scaleArr(y_coords, scaler)

    # optimise path
    coords_len = len(x_coords)
    points = list(compressPath(x_coords, y_coords))
    if logging:
        print("It took {:.3f} seconds to complete the path finding".format(time.time() - logging))
        print("Number of nodes reduced\n{} -> {}\nThats a compression ratio of {}%".format(coords_len, len(points),
                                                                                           int(100 * (coords_len - len(
                                                                                               points)) / coords_len)))

    x_coords = []
    y_coords = []
    for point in points:
        x_coords.append(point[0])
        y_coords.append(point[1])

    if not show:
        return x_coords, y_coords

    fig, ax = plt.subplots(2)

    ax[0].imshow(img)
    alphas = np.clip(np.abs(_mask), 0, 1)
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["blue", "red"])
    c = ax[0].pcolormesh(_mask, cmap=cmap, vmin=-1, vmax=1, rasterized=True, alpha=alphas)
    plt.colorbar(c, ax=ax[0])
    ax[0].contour(_mask[::1], levels=[-.0001, .0001], colors='green', linestyles='dashed', linewidths=1)

    ax[1].imshow(_mask > maxDangerLevel)

    ax[0].scatter(_start[0], _start[1], marker="*", color="blue", s=200)
    ax[1].scatter(_start[0], _start[1], marker="*", color="blue", s=200)

    ax[0].scatter(_end[0], _end[1], marker="*", color="red", s=200)
    ax[1].scatter(_end[0], _end[1], marker="*", color="red", s=200)

    ax[0].plot(x_coords, y_coords, color="black")
    ax[1].plot(x_coords, y_coords, color="black")

    # plt.savefig('map.png', dpi=1000)

    plt.show()

    return x_coords, y_coords


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


@jit(nopython=True)
def scaleRange(_range, _scaler=1):
    return int(_range * _scaler)


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
