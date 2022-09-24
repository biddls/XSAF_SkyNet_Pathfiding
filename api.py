import main
import numpy as np
from fastapi import FastAPI

app = FastAPI()


@app.get('/pathfind/{x1}/{y1}/{x2}/{y2}')
def pathFind(x1, x2, y1, y2):
    x1 = -int(x1[1:]) if x1[0] == 'n' else int(x1)
    x2 = -int(x2[1:]) if x2[0] == 'n' else int(x2)
    y1 = -int(y1[1:]) if y1[0] == 'n' else int(y1)
    y2 = -int(y2[1:]) if y2[0] == 'n' else int(y2)
    path_x, path_y, steps = _finder.findPathCord(np.array([[x1, y1], [x2, y2]]))

    return {
                "pathX": str(path_x),
                "pathY": str(path_y)
            }


_finder = main.finder("pocmap.png")
_finder.newData("test.lua")

# uvicorn api:app --reload
