import time
from tqdm import tqdm
from matplotlib import image as mpimg, pyplot as plt
import core
import json
import numpy as np
import luadata


class finder:
    def __init__(self, _mapImg, _file=None):
        self.mask = None
        self.mapImg = mpimg.imread(_mapImg)
        self.scaler = core.calcScale(self.mapImg)
        if _file is not None:
            self.newData(_file)

    def newData(self, _file='', _logging=False):
        if _file != '':
            _shape = self.mapImg.shape
            _mask = np.zeros(_shape[:2], dtype=np.float64)
            Y, X = np.ogrid[:_shape[0], :_shape[1]]
            _data = json.loads(json.dumps(luadata.read(_file, encoding="utf-8"), indent=4))

            _start = time.time()
            for _objKey in _data.keys():
                _obj = [*_data[_objKey].values()]
                _obj = core.cordToPix(*_obj)
                _mask += core.create_circular_mask(Y, X, _obj[:2], _obj[2], 1)

            if _logging:
                print("It took {:.3f} seconds to complete create_circular_mask".format(time.time() - _start))
            self.mask = _mask

    def findPathPix(self, _start, _end, _show=False, _logging=False):
        if self.mask is None:
            raise ValueError("colourMask or mask cannot be none")
        _path, _runs = core.pathFind(self.mapImg, self.mask, _start, _end, show=_show,
                                     logging=_logging)

    def findPathCord(self, _start, _end, _show=False, _logging=False):
        # todo add mapping from cord to pix
        _path, _runs = core.pathFind(self.mapImg, self.mask, _start, _end, show=_show,
                                     logging=_logging)


if __name__ == "__main__":
    _finder = finder("pocmap.png")

    for x in tqdm(range(10), desc="Loading new data"):
        _finder.newData("test.lua")

    for x in tqdm(range(100), desc="Path finding"):
        _finder.findPathPix((1265, 217), (1160, 746))
