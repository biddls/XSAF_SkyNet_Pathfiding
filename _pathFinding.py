import math

import numpy as np
import heapq
import matplotlib.pyplot as plt
from numba import jit

def pathFind(start, goal, grid, pathFinder, trackSteps=False):
    route, steps = astar(grid, start, goal, trackSteps)
    if isinstance(route, bool):
        return False, None, None

    route = (route + [start])[::-1]

    # extract x and y coordinates from route list
    x_coords = []
    y_coords = []
    for i in (range(0, len(route))):
        x_coords.append(route[i][0])
        y_coords.append(route[i][1])

    return x_coords, y_coords, steps


def heuristic(a, b):
    return np.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)


def astar(array, start, goal, trackSteps):
    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    close_set = set()
    came_from = {}
    gscore = {start: 0}
    fscore = {start: heuristic(start, goal)}
    oheap = []
    heapq.heappush(oheap, (fscore[start], start))
    steps = []
    while oheap:
        current = heapq.heappop(oheap)[1]

        if current == (goal[1], goal[0]):
            data = []

            while current in came_from:
                data.append(current)
                current = came_from[current]
            return data, steps

        close_set.add(current)
        for i, j in neighbors:
            neighbor = (current[0] + i), (current[1] + j)
            tentative_g_score = gscore[current] + heuristic(current, neighbor)
            if 0 <= neighbor[1]/10 < array.shape[0]:
                if 0 <= neighbor[0]/10 < array.shape[1]:
                    if array[math.floor(neighbor[1]/10)][math.floor(neighbor[0]/10)] == 1:
                        continue
                else:
                    continue
            else:
                continue

            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                continue
            if tentative_g_score < gscore.get(neighbor, 0) or neighbor not in [i[1] for i in oheap]:
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score
                fscore[neighbor] = tentative_g_score + heuristic(neighbor, (goal[1], goal[0]))
                heapq.heappush(oheap, (fscore[neighbor], neighbor))
            if trackSteps:
                steps.append(neighbor)

    return False, None
