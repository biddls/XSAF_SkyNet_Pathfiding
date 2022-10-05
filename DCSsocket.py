import socket
import socketserver
import time
import json
import numpy as np
import lua_message_class
import main


def main_code(start_list: list, end_list: list, threats: dict = None) -> list:
    # make new finder class
    _finder = main.finder("pocmap.png")
    # load new map data
    if threats is not None:
        _finder.newData(threats)
    elif _finder.mask is None:
        # error
        return [[0, 0], [0, 0]]
    arr = np.array([start_list, end_list])
    cordX, cordY, path = _finder.findPathCord(arr)
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
