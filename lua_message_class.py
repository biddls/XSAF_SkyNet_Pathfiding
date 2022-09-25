import json
import time


class LuaMessage:

    data: bytes = b''
    data_buffer: bytes = b''
    cache = []
    request_stack: list = []
    perf_counter: float = 0.0

    @staticmethod
    def request_data(data, idx=1):
        return {
            'idx': f"{idx}",
            'msg': f"{data}",
        }

    def __init__(self):
        return

    def handle(self, request, client_address, inbound):
        # if client_address and inbound and client_address[1] != 3015 and request:
        self.data_buffer = request.recv(125)
        while 0 < len(self.data_buffer) > 25:
            self.data = b''.join([self.data, self.data_buffer])
            self.data_buffer = request.recv(8192)
        self.data_buffer = b''
        if len(self.data) > 0:
            print(time.asctime() + ": Proc a Lua MSG recv, buffer size:", len(self.data))
            self.data = json.loads(self.data)
            self.add_data()
        request.close()

    def is_empty(self):
        return len(self.cache) == 0

    def add_data(self):
        self.cache.append(self.data)
        self.data = b''

    def proc(self):
        ret_list: list = []
        idx = 0
        pict: dict = {}
        self.perf_counter = time.time()
        if len(self.cache) > 0:
            msg = self.cache.pop()
            if isinstance(msg, dict):
                ret_list.append([int(msg['msg']['from'][0]), int(msg['msg']['from'][1])])
                ret_list.append([int(msg['msg']['to'][0]), int(msg['msg']['to'][1])])
                if msg['msg'].get('threats'):
                    pict = msg['msg']['threats']
                if msg.get('idx'):
                    idx = msg['idx']
            else:
                return None, None, None
            return ret_list, pict, idx
        return None, None, None
