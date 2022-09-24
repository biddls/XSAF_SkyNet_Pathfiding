import socketserver
import threading
import socket
from main import finder
import numpy as np
# import lua_message_class


# if __name__ == "__main__":
# def main_code(start_list: list, end_list: list, threats: dict = {}):
#     # test = []
#     # make new finder class
#     _finder = finder("pocmap.png")
#     # load new map data
#     _finder.newData(threats)
#     # set the from and too for a given path
#     # format: [x1, y1], [x2, y2]
#     # arr = np.array([[-743000, -100000], [743000, -100000]])
#     arr = np.array([start_list, end_list])
#     # call this when ever you want to find a path
#     cordX, cordY, path = _finder.findPathCord(arr, _show=False, _logging=False)
#
#     if cordY is None:
#         return [[0, 0], [0, 0]]
#
#     return [cordX, cordY]
#
#
# def main_loop():
#
#     lua_message = lua_message_class.LuaMessage()
#     lua_exe = lua_message_class.LuaExe()
#     soc = socketserver.TCPServer(("localhost", 3015), lua_message.handle)
#     soc.allow_reuse_address = True
#     soc.request_queue_size = 10
#     soc.timeout = 0.15
#
#     while True:
#         # check socket for incoming data stream
#         soc.handle_request()
#
#         # check for cached proc requests
#         # already json decoded and ready to proc_func
#         if lua_message.is_empty() is not True:
#             path_req, picture, idx = lua_message.proc()
#             if path_req is not None:
#                 path = main_code(path_req[0], path_req[1], picture)
#                 print(f"msg proc: {path_req}")
#                 if path:
#                     lua_exe.request_stack.append(lua_exe.request_data(path, idx))
#                     print(f"msg ready: {path}")
#
#         elif len(lua_exe.request_stack) > 0:
#             try:
#                 lua_exe.handle()
#             except Exception as e:
#                 print(e)
#
#         else:
#             lua_exe.reset_connection()


class Client:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

    def write(self, message):
        message = message.encode('utf-8')
        self.sock.send(message)

    def stop(self):
        self.sock.close()

    def receive(self):
        while True:
            try:
                message = self.sock.recv(1024).decode('utf-8')
                print(message)
            except ConnectionAbortedError:
                break
            except Exception as e:
                print("Error:", e)
                self.socket.close()

if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 9090
    client = Client(HOST, PORT)
    # main_loop()
