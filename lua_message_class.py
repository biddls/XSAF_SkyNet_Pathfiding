import json
import time
# import lua_state_class
import os
import luadata
import DCSsocket
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
        ret_list: list = []
        idx = 0
        pict: dict = {}
        if len(self.cache) > 0:
            msg = self.cache.pop()
            if isinstance(msg, dict):
                ret_list.append([int(msg['msg']['from'][0]), int(msg['msg']['from'][1])])
                ret_list.append([int(msg['msg']['to'][0]), int(msg['msg']['to'][1])])
                if msg['msg']['threats']:
                    pict = msg['msg']['threats']
                if msg['idx']:
                    idx = msg['idx']
            else:
                return None, None, None

            return ret_list, pict, idx


class LuaExe:
    data_buffer: bytes = b''
    request_stack: list = []
    soc_to = 0.015
    sock = socket.create_server(("localhost", 3006), family=socket.AF_INET, backlog=5000)
    sock.settimeout(soc_to)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    def __init__(self):
        return

    @staticmethod
    def request_data(data, idx=1):
        return {
            'idx': f"{idx}",
            'msg': f"{data}",
        }

    def reset_connection(self):
        if self.sock.fileno() > 0:
            # empty of data, can be reset
            pass
        # self.sock.close()
        # self.sock = socket.create_server(("localhost", 3006), family=socket.AF_INET, backlog=5000)
        # self.sock.settimeout(self.soc_to)
        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, 1)
        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    def handle(self):
        if len(self.request_stack) < 1:
            # self.request_stack: list = None
            return

        self.sock.listen(0)
        # Connect to server and send data
        client, addr = self.sock.accept()

        print(client, addr)

        if client is not None:
            print(f"client {client}")
            msg_data = self.request_stack.pop()
            # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, 1)
            # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            client.sendall(bytes(json.dumps(msg_data), "utf-8"))
