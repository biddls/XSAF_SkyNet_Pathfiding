import json
import time
import cv2
import luadata
import matplotlib
from tqdm import tqdm
from matplotlib import image as mpimg, pyplot as plt
import core
import numpy as np
from slpp import slpp as lua


class finder:
    def __init__(self, _mapImg, _file=None):
        self.mask = None
        self.optMask = None
        self.mapImg = mpimg.imread(_mapImg)
        self.scale = 10
        if _file is not None:
            self.newData(_file)

    def newData(self, _threats, _logging=False):
        if len(_threats.keys()) == 0:
            return
        _shape = self.mapImg.shape
        _mask = np.zeros(_shape[:2], dtype=np.float32)
        Y, X = np.ogrid[:_shape[0], :_shape[1]]

        _start = time.time()
        for _objKey in _threats.values():
            _obj = list(_objKey.values())
            _obj[0] = np.interp([-_obj[0]], (-244922, 339322), (0, 866)).astype(int)[0]
            _obj[1] = np.interp([_obj[1]], (-745556, 744878), (0, 2200)).astype(int)[0]
            _obj[2] = int(_obj[2] * 0.0014972)
            # print(_obj, [_threats[_objKey]['y'], -_threats[_objKey]['x'], _threats[_objKey]['size']])
            _mask += core.create_circular_mask(Y, X, *_obj)

        if _logging:
            print("It took {:.3f} seconds to complete create_circular_mask".format(time.time() - _start))
        self.mask = _mask
        self.optMask = cv2.resize(_mask, dsize=(round(_mask.shape[1] / self.scale), round(_mask.shape[0] / self.scale)),
                                  interpolation=cv2.INTER_NEAREST)

    def findPathCord(self, _arr, _show=False, _logging=False, maxDangerLevel=0):
        _logging = time.time() if _logging else _logging

        _arr = core.cord_to_pix(_arr, self.scale)

        _start = tuple(list(_arr[0].astype(int)))
        _end = tuple(list(_arr[1].astype(int)))

        route, found = core.pathFind(self.optMask, _start[::-1], _end, logging=_logging)

        _start = _arr[0] * self.scale
        _end = _arr[1] * self.scale

        if found:
            # extract x and y coordinates from route list
            route = np.array(route)

            # optimise path
            points1 = np.array(list(core.compressPath(route)))
            points = np.array(list(core.CompressPath2(points1, maxSkip=2)))
            points = np.array(list(core.CompressPath3(points, self.optMask)))

            # scale up path
            x_coords = points[:, 0] * self.scale
            y_coords = points[:, 1] * self.scale
            # scale up path
            x_coords1 = points1[:, 0] * self.scale
            y_coords1 = points1[:, 1] * self.scale

            if _logging:
                coords_len = len(route)
                print("It took {:.3f} seconds to complete the path finding".format(time.time() - _logging))
                print("Number of nodes reduced\n{} -> {}\nThats a compression ratio of {}%"
                      .format(coords_len, len(points), int(100 * (coords_len - len(points)) / coords_len)))

            if not _show:
                return x_coords, y_coords

        fig, ax = plt.subplots(1)

        ax.imshow(self.mapImg)

        alphas = np.clip(np.abs(self.mask), 0, 1)

        cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["blue", "red"])

        c = ax.pcolormesh(self.mask, cmap=cmap, vmin=-1, vmax=1, rasterized=True, alpha=alphas)
        plt.colorbar(c, ax=ax)
        ax.contour(self.mask, levels=[-.0001, .0001], colors='green', linestyles='dashed', linewidths=2)

        ax.scatter(_start[0], _start[1], marker="*", color="blue", s=200)
        ax.scatter(_end[0], _end[1], marker="*", color="red", s=200)

        if found:
            ax.plot(y_coords1, x_coords1, color="white")
            ax.plot(y_coords, x_coords, color="black")

        # plt.savefig('map.png', dpi=1000)

        plt.show()

        return [_start, _end]


if __name__ == "__main__":
    # make new finder class
    _finder = finder("pocmap.png")
    # load new map data
    with open("test_data.lua") as f:
        _data = f.read()
    _data = lua.decode(_data[6:])

    if "from" and "to" in _data.keys():
        _from, _to = _data["from"], _data["to"]
        del _data["from"]
        del _data["to"]
        raise ValueError("Still need to implement this", _from, _to)
        arr = np.array([[0, 0], [0, 0]])
    else:
        # set the from and too for a given path
        # format: [x1, y1], [x2, y2]
        # arr = np.array([[-343000, 0], [0, 0]])
        arr = np.array([[-743000, -100000], [743000, -100000]])
        arr = np.array([[-300000, 240000], [743000, -100000]])
        arr = np.array([[-260000, -55000], [743000, -100000]])
    _finder.newData(_data)

    # call this when ever you want to find a path
    _finder.findPathCord(arr, _show=True, _logging=True)
    exit(0)
    arr = np.array([_data['from'][::-1], _data['to'][::-1]])
    # call this when ever you want to find a path
    _finder.findPathCord(arr, _show=True, _logging=False)

    # ignore path
    # for x in tqdm(range(30), desc="Path finding"):
    #     arr = np.array([[-743000, -100000], [743000, -100000]])
    #     test.append([_finder.findPathCord(arr, _show=False, _logging=False)])

    # for x in tqdm(range(30), desc="Path finding pix"):
    #     # _finder.findPathPix((1265, 217), (1160, 746))
    #     # worst case max dist
    #     _finder.findPathPix((347, 0), (2194, 347))

    # for x in tqdm(range(30), desc="Path finding cord"):
    #     # worst case max dist
    #     arr = np.array([[-743000, -100000], [743000, -100000]])
    #     _finder.findPathCord(arr, _show=False, _logging=False)
