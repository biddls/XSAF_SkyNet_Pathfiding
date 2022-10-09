import matplotlib.pyplot as plt
import numpy as np
import heapq


def pathFind(_start, _goal, _grid, _pathFinder, show=False):
    route, found = _pathFinder(_grid, _start, _goal, show=show)
    if found is False:
        route = ([_start] + [_goal])
    else:
        route = (route + [_start])[::-1]

    return route, found


def heuristic(_a, _b):
    return np.sqrt((_b[0] - _a[0]) ** 2 + (_b[1] - _a[1]) ** 2)


def astar(array, _start, _goal, show=False):
    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    max0, max1 = array.shape[0] - 1, array.shape[1] - 1
    close_set = set()
    came_from = {}
    gscore = {_start: 0}
    fscore = {_start: heuristic(_start, _goal)}
    oheap = []
    heapq.heappush(oheap, (fscore[_start], _start))
    if show:
        plt.imshow(array)
        plt.scatter(_start[1], _start[0], marker="*", color="blue", s=200)
        plt.scatter(_goal[1], _goal[0], marker="*", color="red", s=200)
    while oheap:
        current = heapq.heappop(oheap)[1]
        if current == _goal:
            data = []

            while current in came_from:
                data.append(current)
                current = came_from[current]

            plt.show() if show else None
            return data, True

        close_set.add(current)
        for i, j in neighbors:
            neighbor = current[0] + i, current[1] + j
            if np.clip(neighbor[0], 0, max0) != neighbor[0] or np.clip(neighbor[1], 0, max1) != neighbor[1]:
                continue
            if array[neighbor[0]][neighbor[1]] == 1:
                continue

            tentative_g_score = gscore[current] + 1 if -1 >= i + j >= 1 else 0.414

            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                continue
            if neighbor not in [i[1] for i in oheap]:
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score
                fscore[neighbor] = tentative_g_score + heuristic(neighbor, _goal)
                heapq.heappush(oheap, (fscore[neighbor], neighbor))
                plt.scatter(neighbor[1], neighbor[0], marker=".", color="black", s=20) if show else None

    return [], False


def biddlsPhonk(array, _start, _goal):
    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    Y, X = np.ogrid[:array.shape[0], :array.shape[1]]
    # max0, max1 = array.shape[0] - 1, array.shape[1] - 1

    # gen oval
    # nill = heuristic((X, Y), _start[::-1]) + heuristic((X, Y), goal[::-1]) - heuristic(_start[::-1], goal[::-1])
    # gen dist to point

    nill = heuristic((X, Y), _goal[::-1])
    array += nill
    path = {_start: array[_start[0], _start[1]]}
    current = start
    while _goal not in path.keys():
        _min = float("inf")
        _next = current
        for i, j in neighbors:
            neighbor = current[0] + i, current[1] + j
            try:
                _next = neighbor if array[neighbor[0]][neighbor[1]] < _min else _next
            except Exception as e:
                print(e)
                continue
            if _next == current:
                raise ValueError("Path blocked, no new path found")
            else:
                current = _next
        plt.imshow(array)
        plt.scatter(_start[1], _start[0], marker="*", color="blue", s=200)
        plt.scatter(_goal[1], _goal[0], marker="*", color="red", s=200)
        plt.grid()
        plt.show()

        exit(0)

    return [], False


if __name__ == "__main__":
    from timeit import default_timer as timer

    itters = 10000
    a = 1
    b = 2
    start = timer()

    for x in range(itters):
        if a <= 1.5 < b:
            continue

    print((timer() - start) / itters)

    start = timer()

    for x in range(itters):
        min(0, a, b)
        max(a, b, 10)

    print((timer() - start) / itters)
