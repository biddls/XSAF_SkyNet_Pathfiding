import time
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder import a_star
import luadata
import json
import _pathFinding


def NormalizeData(data, scale=255):
    if scale > 1:
        return np.round(scale * ((data - np.min(data)) / (np.max(data) - np.min(data))))
    elif scale <= 1:
        return scale * ((data - np.min(data)) / (np.max(data) - np.min(data)))
    else:
        raise ValueError("Scale has to be greater than 0")


def create_circular_mask(h, w, center=None, radius=None, strength=1):
    if strength > 1 or strength <= 0:
        raise ValueError("Strength needs to be 0 <= strength < 1: {}".format(strength))
    if center is None:  # use the middle of the image
        center = (int(w / 2), int(h / 2))
    if radius is None:  # use the smallest distance between the center and image walls
        radius = min(center[0], center[1], w - center[0], h - center[1])

    Y, X = np.ogrid[:h, :w]
    dist_from_center = strength * ((radius - np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)) / radius)
    dist_from_center[dist_from_center < 0] = 0
    dist_from_center = dist_from_center

    return dist_from_center


def pathFind(img, colourMask, mask, _start, _end, maxDangerLevel=0, show=True):
    startTime = time.time()
    # if mask[_start[1]][_start[0]] != 0:
    #     raise ValueError("Start point not valid: {}".format(_start))
    # if mask[_end[1]][_end[0]] != 0:
    #     raise ValueError("End point not valid: {}".format(_end))

    grid = Grid(matrix=mask <= maxDangerLevel)
    start = grid.node(_start[0], _start[1])
    end = grid.node(_end[0], _end[1])

    finder = a_star.AStarFinder(diagonal_movement=DiagonalMovement.always)
    path, runs = finder.find_path(start, end, grid)

    print("It took {:.2f} seconds to complete the path finding".format(time.time() - startTime))
    if not show:
        return path, runs

    fig, ax = plt.subplots(2)

    ax[0].imshow(img)
    ax[0].imshow(colourMask, alpha=0.7)
    ax[1].imshow(mask <= maxDangerLevel)

    ax[0].scatter(_start[0], _start[1], marker="*", color="yellow", s=200)
    ax[1].scatter(_start[0], _start[1], marker="*", color="yellow", s=200)

    ax[0].scatter(_end[0], _end[1], marker="*", color="red", s=200)
    ax[1].scatter(_end[0], _end[1], marker="*", color="red", s=200)

    # extract x and y coordinates from route list
    x_coords = []
    y_coords = []

    for step in path:
        x_coords.append(step[0])
        y_coords.append(step[1])

    ax[0].plot(x_coords, y_coords, color="black")
    ax[1].plot(x_coords, y_coords, color="black")

    plt.show()

    return path, runs


def genColourMask(mask):
    colourMask = np.zeros((*mask.shape, 4), dtype=np.uint8)

    # mask = dist_from_center <= radius
    # mask = mask * dist_from_center
    for indexx, x in enumerate(mask):
        for indexy, y in enumerate(x):
            colourMask[indexx][indexy] = [255, 0, 0, int(y * 255)]

    return colourMask


def cordToPix(canvas, x, y, scaler, _range=0, xRng=(-744878, 744878), yRng=(-339322, 245600)):
    x = scale(x, xRng, scaler=canvas.shape[:2][1])
    y = scale(y, yRng, scaler=canvas.shape[:2][0])
    return x, y, scaleRange(_range, _scaler=scaler)


def scale(value, rng, scaler=1):
    return int(scaler * (value - min(rng)) / (max(rng) - min(rng)))


def scaleRange(_range, _scaler=1):
    return int(_range * _scaler)


def calcScale(canvas, xRng=(-744878, 744878), yRng=(-339322, 245600)):
    length = lambda x, y: min(x, y) - max(x, y)
    dist = lambda x, y: np.sqrt(x ** 2 + y ** 2)
    mapDist = dist(length(*xRng), length(*yRng))
    canvasDist = dist(*canvas.shape[:2])
    return canvasDist / mapDist


if __name__ == "__main__":

    img = mpimg.imread('pocmap.png')
    data = json.loads(json.dumps(luadata.read("test.lua", encoding="utf-8"), indent=4))
    scaler = calcScale(img)
    mask = None
    for objKey in data.keys():
        obj = [*data[objKey].values()]
        obj = cordToPix(img, *obj, scaler)
        if mask is None:
            mask = create_circular_mask(*img.shape[:2], center=obj[:2], radius=obj[2], strength=1)
        else:
            mask += create_circular_mask(*img.shape[:2], center=obj[:2], radius=obj[2], strength=1)
    #
    # h, w = img.shape[:2]
    # mask = create_circular_mask(h, w, radius=100, strength=1)

    mask[mask > 1] = 1

    colourMask = genColourMask(mask)

    # fig, ax = plt.subplots(2)
    # ax[0].imshow(img, extent=[-744878, 744878, -339322, 245600])
    # ax[0].imshow(colourMask, extent=[-744878, 744878, -339322, 245600], alpha=0.5)
    # ax[0].title.set_text("0")
    # ax[1].imshow(mask)
    # ax[1].title.set_text("1")
    # plt.show()

    # plt.imshow(img)
    # plt.imshow(colourMask, alpha=0.5)
    # plt.show()

    # _start = (1015, 606)
    # _end = (1156, 318)
    _start = (1265, 217)
    _end = (1160, 746)

    start = time.time()
    path, runs = pathFind(img, colourMask, mask, _start, _end, show=False)
    print("that took: {} seconds".format(round(time.time() - start, 1)))

    start = time.time()
    _pathFinding.pathFind(list(_start), list(_end), mask >= 0, show=False)
    print("that took: {} seconds".format(round(time.time() - start, 1)))
