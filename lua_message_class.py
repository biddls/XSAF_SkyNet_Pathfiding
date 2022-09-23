import json
import time
# import lua_state_class
import os
import luadata
import socket
import datetime
import lua.parse
import lua.serialize
from zipfile import ZipFile
import zipfile
import random
from lua.cloud_presets import Clouds
from socketserver import BaseRequestHandler


class LuaMessage:

    data: bytes = b''
    data_buffer: bytes = b''
    cache = []

    def __init__(self):
        return

    def handle(self, request, client_address, inbound):
        # get data from socket
        self.data_buffer = request.recv(8192)
        while len(self.data_buffer) > 0:
            self.data = b''.join([self.data, self.data_buffer])
            self.data_buffer = request.recv(8192)

        self.data_buffer = b''

        if len(self.data) > 0:
            print(time.asctime() + ": Proc a Lua MSG recv, buffer size:", len(self.data))
            self.data = json.loads(self.data)
            self.add_data()

    # only add to cache when a data package is complete and ready to fit into a pro func
    def is_empty(self):
        return len(self.cache) == 0

    def add_data(self):
        self.cache.append(self.data)
        self.data = b''

    def proc(self):
        ret_list = []
        if len(self.cache) > 0:
            msg = self.cache.pop()
            if isinstance(msg, dict):
                # ret_list.append([int(msg['msg']['from'][0]), int(msg['msg']['from'][1])])
                # ret_list.append([int(msg['msg']['to'][0]), int(msg['msg']['to'][1])])
                ret_list.append(msg['msg']['from'])
                ret_list.append(msg['msg']['to'])
                return ret_list


class LuaExe:
    data_buffer: bytes = b''
    request_stack = []
    return_stack = []
    soc_to = 5.55
    sock = socket.create_server(("localhost", 3006), family=socket.AF_INET, backlog=5000)
    sock.settimeout(soc_to)

    def __init__(self):
        return

    @staticmethod
    def request_data(data, idx=1):
        return {
            'idx': f"{idx}",
            'msg': f"{data}",
        }

    def reset_connection(self):
        self.sock.close()
        self.sock = socket.create_server(("localhost", 3006), family=socket.AF_INET, backlog=5000)
        self.sock.settimeout(self.soc_to)

    def handle(self):
        if len(self.request_stack) < 1:
            return

        self.sock.listen(1)
        # Connect to server and send data
        client, addr = self.sock.accept()

        if client is not None:
            print(f"client {client}")
            msg_data = self.request_stack.pop()
            client.sendall(bytes(json.dumps(msg_data), "utf-8"))
