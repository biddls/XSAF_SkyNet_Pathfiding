from matplotlib import image as mpimg

import core
import json
import numpy as np
import luadata

class finder:

    def __init__(self, _mapImg):
        self.colourMask = None
        self.mask = None
        self.mapImg = mpimg.imread(_mapImg)
        self.scaler = core.calcScale(self.mapImg)

    def newData(self, _file):
        _data = json.loads(json.dumps(luadata.read(_file, encoding="utf-8"), indent=4))
        _mask = np.zeros(self.mapImg.shape[:2], dtype=np.float64)
        for _objKey in _data.keys():
            _obj = [*_data[_objKey].values()]
            _obj = core.cordToPix(self.mapImg, *_obj, self.scaler)
            if _mask is None:
                _mask = core.create_circular_mask(*self.mapImg.shape[:2], center=_obj[:2], radius=_obj[2], strength=1)
            else:
                _mask += core.create_circular_mask(*self.mapImg.shape[:2], center=_obj[:2], radius=_obj[2], strength=1)

        _mask[_mask > 1] = 1
        _colourMask = core.genColourMask(_mask)

        self.mask = _mask
        self.colourMask = _colourMask

    def findPathPix(self, _start, _end, _show=True):
        if self.colourMask is None or self.mask is None:
            raise ValueError("colourMask or mask cannot be none")
        _path, _runs = core.pathFind(self.mapImg, self.colourMask, self.mask, _start, _end, show=_show)

    def findPathCord(self, _start, _end, _show=True):
        _path, _runs = core.pathFind(self.mapImg, self.colourMask, self.mask, _start, _end, show=_show)


if __name__ == "__main__":
    finder = finder("pocmap.png")
    finder.newData("test.lua")
    # finder.findPathPix((1055, 374), (1423, 435))#, _show=False)
    finder.findPathPix((1265, 217), (1160, 746))  # , _show=False)
