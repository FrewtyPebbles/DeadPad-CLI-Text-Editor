import platform
import threading as th
from queue import Queue

opsys = platform.system()

LEFT = b'\x1b[D' if opsys == 'Linux' else b'\xe0K'
RIGHT = b'\x1b[C' if opsys == 'Linux' else b'\xe0M'
UP = b'\x1b[A' if opsys == 'Linux' else b'\xe0H'
DOWN = b'\x1b[B' if opsys == 'Linux' else b'\xe0P'
HOME = b'\x1b[H' if opsys == 'Linux' else b'\xe0G'
END = b'\x1b[F' if opsys == 'Linux' else b'\xe0O'
ESC = b'\x1b\x1b\x1b' if opsys == 'Linux' else b'\x1b'
BACKSPACE = b'\x7f' if opsys == 'Linux' else b'\x08'
CTRL_O = b'\x0f' if opsys == 'Linux' else b'\x0f'
CTRL_W = b'\x17' if opsys == 'Linux' else b'\x17'

class BaseInputHandler:

    def __init__(self) -> None:
        self._processing_thread = th.Thread(target=self._detect_keys, daemon=True)
        self.checking_for_input = True
        self.input_queue:Queue[bytes] = Queue(2)

    def _detect_keys(self):
        "While true and queue keys."

    def filter_key(self, key:bytes):
        k_filter = {
            b'\r':b'\n'
        }
        return (k_filter)[key] if key in k_filter.keys() else key

    def start(self):
        "Start recording inputs."
        self.checking_for_input = True
        self._processing_thread.start()

    def stop(self):
        "Stop recording inputs."
        self.checking_for_input = False

    def get(self):
        "Get the next input in the input queue"
        if not self.input_queue.empty():
            return self.input_queue.get(False)