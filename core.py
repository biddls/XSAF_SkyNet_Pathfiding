import time
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import luadata
import json
import _pathFinding
import cv2


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


def doubleCompress(x_cords, y_cords):
    pass


def pathFind(img, colourMask, _mask, _start, _end, scaler=10, maxDangerLevel=0, show=True, logging=False):
    logging = time.time() if logging else logging

    scaleTuple = lambda tup, sc: tuple(int(_x/sc) for _x in tup)
    scaleArr = lambda _arr, sc: [_x*sc for _x in _arr]

    mask = cv2.resize(_mask, dsize=(round(_mask.shape[1]/scaler), round(_mask.shape[0]/scaler)), interpolation=cv2.INTER_NEAREST)
    mask = mask > maxDangerLevel

    y_coords, x_coords = _pathFinding.pathFind(scaleTuple(_start[::-1], scaler), scaleTuple(_end[::-1], scaler), mask, show=False)

    # path compression
    x_coords = scaleArr(x_coords, scaler)
    y_coords = scaleArr(y_coords, scaler)
    coords_len = len(x_coords)
    # optimise path
    points = list(compressPath(x_coords, y_coords))
    if logging:
        print("It took {:.3f} seconds to complete the path finding".format(time.time() - logging))
        print("Number of nodes reduced\n{} -> {}\nThats a compression ratio of {}%".format(coords_len, len(points), int(100 * (coords_len - len(points))/coords_len)))

    x_coords = []
    y_coords = []
    for point in points:
        x_coords.append(point[0])
        y_coords.append(point[1])

    if not show:
        return x_coords, y_coords

    fig, ax = plt.subplots(2)

    ax[0].imshow(img)
    ax[0].imshow(colourMask, alpha=0.7)
    ax[1].imshow(_mask > maxDangerLevel)

    ax[0].scatter(_start[0], _start[1], marker="*", color="yellow", s=200)
    ax[1].scatter(_start[0], _start[1], marker="*", color="yellow", s=200)

    ax[0].scatter(_end[0], _end[1], marker="*", color="red", s=200)
    ax[1].scatter(_end[0], _end[1], marker="*", color="red", s=200)

    ax[0].plot(x_coords, y_coords, color="black")
    ax[1].plot(x_coords, y_coords, color="black")

    plt.show()

    return x_coords, y_coords


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

    mask[mask > 1] = 1
    colourMask = genColourMask(mask)

    # fig, ax = plt.subplots(2)
    # ax[0].imshow(img, extent=[-744878, 744878, -339322, 245600])
    # ax[0].imshow(colourMask, extent=[-744878, 744878, -339322, 245600], alpha=0.5)
    # ax[0].title.set_text("0")
    # ax[1].imshow(mask)
    # ax[1].title.set_text("1")
    # plt.show()
    #
    # plt.imshow(img, extent=[-744878, 744878, -339322, 245600])
    # plt.imshow(colourMask, extent=[-744878, 744878, -339322, 245600], alpha=0.5)
    # plt.show()

    # exit(0)

    # for visualisation #
    # from astar import main
    # B = np.argwhere(mask)
    # (ystart, xstart), (ystop, xstop) = B.min(0), B.max(0) + 1
    # Atrim = mask[ystart:ystop, xstart:xstop]
    # _max = max(ystop - ystart, xstop - xstart)
    # _zeros = np.zeros((_max, _max))
    # _zeros[0:Atrim.shape[0], 0:Atrim.shape[1]] = Atrim
    # main(list(_zeros), _max)
    # exit(0)

    _start = (1265, 217)
    _end = (1160, 746)

    test = False
    if test:
        times = 0
        runs = 100
        for x in range(runs):
            start = time.time()
            pathFind(img, colourMask, mask, _start, _end, maxDangerLevel=0.1)
            times += time.time() - start
        print("100 runs took on average: {:.4f} seconds".format(times/runs))
    else:
        pathFind(img, colourMask, mask, _start, _end, show=True)
