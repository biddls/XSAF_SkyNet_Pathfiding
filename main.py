import heapq
import socketserver
import time

import cv2
import matplotlib
from tqdm import tqdm
from matplotlib import image as mpimg, pyplot as plt
import core
import json
import numpy as np
import luadata
from animation import start
import lua_message_class


def rotate_vec(x, y, theta=1):
    return int(x * np.cos(theta) - y * np.sin(theta)), int(x * np.sin(theta) + y * np.cos(theta))


class finder:
    def __init__(self, _mapImg, _file=None):
        self.mask = None
        self.mapImg = mpimg.imread(_mapImg)
        self.scaler = core.calcScale(self.mapImg)
        self.scale = 10
        if _file is not None:
            self.newData(_file)

    def newData(self, _file='', _logging=False):
        if _file is not None and isinstance(_file, dict):
            _shape = self.mapImg.shape
            _mask = np.zeros(_shape[:2], dtype=np.float64)
            Y, X = np.ogrid[:_shape[0], :_shape[1]]
            _data = _file

            _start = time.time()
            for _objKey in _data.keys():
                _obj = [_data[_objKey]['x'], _data[_objKey]['y'], _data[_objKey]['size']]
                _obj = core.cordToPix(_obj[0], _obj[1], _obj[2])
                _obj = (_obj[0]*1.095, 866-_obj[1]*0.835, _obj[2])
                _mask += core.create_circular_mask(Y, X, _obj[:2], _obj[2], 1)

            if _logging:
                print("It took {:.3f} seconds to complete create_circular_mask".format(time.time() - _start))
            self.mask = _mask
            self.optMask = cv2.resize(_mask, dsize=(round(_mask.shape[1] / self.scale), round(_mask.shape[0] / self.scale)),
                      interpolation=cv2.INTER_NEAREST)
            np.save("optMask", self.optMask)

    # def findPathPix(self, _start, _end, _show=False, _logging=False):
    #     if self.mask is None:
    #         raise ValueError("Mask not loaded")
    #     _path, _runs, _steps = core.pathFind(self.optMask, _start, _end, show=_show, logging=_logging)
    #     # start(X=_steps, _shape=self.mask.shape)
    #     return _path, _runs, _steps

    def findPathCord(self, _arr, _show=False, _logging=False, maxDangerLevel=1):
        _logging = time.time() if _logging else _logging

        # y1, y2, x1, x2 = -745556, 744878, -339322, 244922

        # _start = tuple(np.floor_divide(np.interp(_arr[:, 0], (-745556, 744878), (0, 2200)), self.scale).astype(int))
        # _end = tuple(np.floor_divide(np.interp(_arr[:, 1], (-339322, 244922), (0, 866)), self.scale).astype(int))

        # _start = tuple(np.floor_divide(np.interp(_arr[:, 0], (-744878, 744878), (0, 2200)), self.scale).astype(int))
        # _end = tuple(np.floor_divide(np.interp(_arr[:, 1], (-339322, 245600), (0, 866)), self.scale).astype(int))

        _start = core.cordToPix(_arr[0][1], _arr[0][0], 10)
        _end = core.cordToPix(_arr[1][1], _arr[1][0], 10)

        _start = (_start[0], 866-_start[1])
        _end = (_end[0], 866-_end[1])

        x_coords, y_coords, _steps = core.pathFind(self.optMask, _start, _end, logging=_logging)
        #
        if y_coords is None:
            print("NO PATH")
            return False, None, None
        else:
            print(f"number of points is {len(y_coords)}")
        #
        # # de-compress path
        # # x_coords = np.array(x_coords) * self.scale
        # # y_coords = np.array(y_coords) * self.scale
        x_coords = np.array(x_coords)
        y_coords = np.array(y_coords)
        #
        # # optimise path
        points = list(core.compressPath(x_coords, y_coords))

        # coords_len = len(x_coords)
        # if _logging:
        #     print("It took {:.3f} seconds to complete the path finding".format(time.time() - _logging))
        #     print("Number of nodes reduced\n{} -> {}\nThats a compression ratio of {}%".format(coords_len, len(points),
        #                                                                                        int(100 * (coords_len - len(
        #                                                                                            points)) / coords_len)))
        #
        x_coords = []
        y_coords = []
        for point in points:
            x_coords.append(point[0])
            y_coords.append(point[1])
        print(f"number of points is {len(y_coords)}")
        # if not _show:
        #     return x_coords, y_coords, _steps

        fig, ax = plt.subplots(2)

        ax[0].imshow(self.mapImg)

        alphas = np.clip(np.abs(self.mask), 0, 1)

        cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["blue", "red"])

        c = ax[0].pcolormesh(self.mask, cmap=cmap, vmin=-1, vmax=1, rasterized=True, alpha=alphas)
        plt.colorbar(c, ax=ax[0])

        # ax[0].contour(self.mask[::1], levels=[-.0001, .0001], colors='green', linestyles='dashed', linewidths=1)

        ax[1].imshow(self.mask > maxDangerLevel)

        ax[0].scatter(_start[0], _start[1], marker="*", color="blue", s=200)
        ax[1].scatter(_start[0], _start[1], marker="*", color="blue", s=200)

        ax[0].scatter(_end[0], _end[1], marker="*", color="red", s=200)
        ax[1].scatter(_end[0], _end[1], marker="*", color="red", s=200)
        #
        if y_coords is not None:
            ax[0].plot(x_coords, y_coords, color="black")
            ax[1].plot(x_coords, y_coords, color="black")

        # plt.savefig('map.png', dpi=1000)

        plt.show()

        return x_coords, y_coords, _steps


def findPathAlone(start, end, _scale=10, maxDangerLevel=1):
    _arr = np.zeros((2, 2))
    _arr[0] = np.array(start)
    _arr[1] = np.array(end)
    print(_arr)
    optMask = np.load("optMask.npy")
    _start = tuple(np.floor_divide(np.interp(_arr[:, 0], (-744878, 744878), (0, 2200)), _scale).astype(int))
    _end = tuple(np.floor_divide(np.interp(_arr[:, 1], (-339322, 245600), (0, 866)), _scale).astype(int))

    return core.pathFind(optMask, _start, _end)


# if __name__ == "__main__":
def main_code(start_list: list, end_list: list, threats: dict = {}):
    test = []
    # make new finder class
    _finder = finder("pocmap.png")
    # load new map data
    _finder.newData(threats)
    # set the from and too for a given path
    # format: [x1, y1], [x2, y2]
    # arr = np.array([[-743000, -100000], [743000, -100000]])
    arr = np.array([start_list, end_list])
    # call this when ever you want to find a path
    cordX, cordY, path = _finder.findPathCord(arr, _show=False, _logging=False)

    if cordY is None:
        return [[0, 0], [0, 0]]

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
    return [cordX, cordY]


def main_loop():

    lua_message = lua_message_class.LuaMessage()
    lua_exe = lua_message_class.LuaExe()
    soc = socketserver.TCPServer(("localhost", 3015), lua_message.handle)
    soc.allow_reuse_address = True
    soc.request_queue_size = 10
    soc.timeout = 1.55

    while True:
        # check socket for incoming data stream
        soc.handle_request()

        # check for cached proc requests
        # already json decoded and ready to proc_func
        if lua_message.is_empty() is not True:
            path_req, picture, idx = lua_message.proc()
            if path_req is not None:
                path = main_code(path_req[0], path_req[1], picture)
                print(f"msg proc: {path_req}")
                if path:
                    lua_exe.request_stack.append(lua_exe.request_data(path, idx))
                    print(f"msg ready: {path}")

        elif len(lua_exe.request_stack) > 0:
            try:
                lua_exe.handle()
            except TimeoutError:
                pass
            except ConnectionResetError:
                print(ConnectionResetError)
            except ConnectionAbortedError:
                print(ConnectionAbortedError)

        # else:
        #     lua_exe.reset_connection()


main_loop()
