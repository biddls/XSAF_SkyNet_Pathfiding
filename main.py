import socket
import socketserver
import time
import cv2
import matplotlib
from matplotlib import image as mpimg, pyplot as plt
import core
import json
import numpy as np
import lua_message_class


# unused
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
                _obj = core.cordToPix(_obj[1], _obj[0], _obj[2])
                _obj = (_obj[0]*0.965, 866-_obj[1]*0.92, _obj[2])
                _mask += core.create_circular_mask(Y, X, _obj[:2], _obj[2], 1)

            if _logging:
                print("It took {:.3f} seconds to complete create_circular_mask".format(time.time() - _start))
            self.mask = _mask
            self.optMask = cv2.resize(_mask, dsize=(round(_mask.shape[1] / self.scale), round(_mask.shape[0] / self.scale)),
                      interpolation=cv2.INTER_NEAREST)
            np.save("optMask", self.optMask)

    def findPathCord(self, _arr, _show=False, _logging=False, maxDangerLevel=1):
        _logging = time.time() if _logging else _logging

        # y1, y2, x1, x2 = -745556, 744878, -339322, 244922

        _start = core.cordToPix(_arr[0][1], _arr[0][0], 10)
        _end = core.cordToPix(_arr[1][1], _arr[1][0], 10)

        _start = (_start[0], 866-_start[1])
        _end = (_end[0], 866-_end[1])

        x_coords, y_coords, _steps = core.pathFind(self.optMask, _start, _end, logging=_logging)

        # points = []
        if y_coords is None:
            print("NO PATH")
            return False, None, None
        else:
            print(f"number of points is {len(y_coords)}")

        cx = []
        cy = []
        for point in range(len(y_coords)-1):
            if point % 14 == 0:
                # 10th the number equally
                cx.append(x_coords[point])
                cy.append(y_coords[point])
        print(f"number of points is {len(cy)}")

        if not _show:
            return cx, cy, _steps

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
            ax[0].plot(cx, cy, color="black")
            ax[1].plot(cx, cy, color="black")

        # plt.savefig('map.png', dpi=1000)

        plt.show()

        return cx, cy, _steps


# unused
def findPathAlone(start, end, _scale=10, maxDangerLevel=1):
    _arr = np.zeros((2, 2))
    _arr[0] = np.array(start)
    _arr[1] = np.array(end)
    print(_arr)
    optMask = np.load("optMask.npy")
    _start = tuple(np.floor_divide(np.interp(_arr[:, 0], (-744878, 744878), (0, 2200)), _scale).astype(int))
    _end = tuple(np.floor_divide(np.interp(_arr[:, 1], (-339322, 245600), (0, 866)), _scale).astype(int))

    return core.pathFind(optMask, _start, _end)


def main_code(start_list: list, end_list: list, threats: dict = None):
    # make new finder class
    _finder = finder("pocmap.png")
    # load new map data
    if threats is not None:
        _finder.newData(threats)
    elif _finder.mask is None:
        # error
        return [[0, 0], [0, 0]]
    arr = np.array([start_list, end_list])
    cordX, cordY, path = _finder.findPathCord(arr, _show=False, _logging=False)
    if cordY is None:
        return [[0, 0], [0, 0]]
    return [cordX, cordY]


def main_loop():
    lua_message = lua_message_class.LuaMessage()
    soc = socketserver.TCPServer(("localhost", 3015), lua_message.handle)
    soc.allow_reuse_address = True
    soc.request_queue_size = 10
    soc.timeout = 0.45
    ret_data = 0

    while True:
        # check for data to be returned
        if len(lua_message.request_stack) > 0:
            host = "localhost"
            port = 3025
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.003)
                if s.connect_ex((host, port)) < 1:
                    s.sendall(bytes(json.dumps(lua_message.request_stack.pop()), "utf-8"))
                    ret_data += 1
                    print(f"Data return no {ret_data} sent to Lua and popped from the stack.")
                    continue
                else:
                    continue
        # check for cached proc requests
        if lua_message.is_empty() is not True:
            path_req, picture, idx = lua_message.proc()
            if path_req is not None:
                path = main_code(path_req[0], path_req[1], picture)
                if path:
                    lua_message.request_stack.append(lua_message.request_data(path, idx))
                    print(f"Total calculation and return time {time.time() - lua_message.perf_counter} for Skynet{idx}")
        else:
            soc.handle_request()


if __name__ == '__main__':
    try:
        main_loop()
    except BaseException as e:
        print(e)
        input()
