import platform
import threading as th
from queue import Queue
from enum import Enum
from deadpad.parts.input import keys

opsys = platform.system()

# TODO: Make get method return an actual class rather than just str so it is easier/cleaner  to check
# input type and things.

# keys are bytes, not str because it includes bytes you cant encode
class InputType(Enum):
    MOUSE = 0
    KEYBOARD = 1

KEY_FILTER = {
            b'\r':b'\n'
        }

class MouseData:
    def __init__(self, inp:bytes | tuple[int,int,int,int]) -> None:
        if opsys == 'Linux':
            str_key = inp.decode()
            tail = str_key[-1]
            in_type, x, y = (int(pos) for pos in str_key.lstrip(keys.MOUSE_PREFIX.decode())[:-1].split(';'))

            self.event_type = in_type
            self.col = x
            self.row = y
            self.event_state = tail
        else:

            self.event_type, self.col, self.row, self.event_state = inp

class InputEvent:
    def __init__(self, inp:str | tuple[int,int,int,int]) -> None:
        if isinstance(inp, str):
            inp = inp.encode()
        self.inp = KEY_FILTER[inp] if inp in KEY_FILTER.keys() else inp
        
        if opsys == 'Linux':
            if self.inp.startswith(keys.MOUSE_PREFIX):
                self.type = InputType.MOUSE
                # parse mouse into metadata here
                self.mouse_data:MouseData | None = MouseData(self.inp)
            else:
                self.type = InputType.KEYBOARD
        else:
            if isinstance(self.inp, bytes):
                self.type = InputType.KEYBOARD
            else:
                self.type = InputType.MOUSE
                # parse mouse into metadata here
                self.mouse_data:MouseData | None = MouseData(self.inp)

class BaseInputHandler:

    def __init__(self) -> None:
        self._processing_thread = th.Thread(target=self._detect_keys, daemon=True)
        self.checking_for_input = True
        self.input_queue:Queue[InputEvent] = Queue(1)

    def _detect_keys(self):
        "While true and queue keys."


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