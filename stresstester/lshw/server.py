import os
import ctypes

from msl.loadlib import Server32


class Server(Server32):
    # the init takes mandatory host and port as arguments
    def __init__(self, host='127.0.0.1', port=None):
        self._dll_path = os.path.join(os.path.dirname(__file__), '硬件检测引擎.dll')
        if not os.path.exists(self._dll_path):
            raise FileNotFoundError(f"File not found: {self._dll_path}")
        super(Server, self).__init__(self._dll_path, 'windll', host, port)

    def hwinfo(self):
        # return type is a char*
        self.lib.Hwinfo_C.restype = ctypes.c_char_p
        return self.lib.Hwinfo_C()
