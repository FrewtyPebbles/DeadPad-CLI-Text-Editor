import msvcrt as ms
import sys
import threading as th
from queue import Queue
import time
try:
    from parts.input_handler import BaseInputHandler
except ModuleNotFoundError:
    from input_handler import BaseInputHandler

def getch():
    ch = ms.getch()
    if ch == b"\xe0":# if it is an arrow key read the rest of the bytes
        ch += ms.getch()
    return ch

class InputHandler(BaseInputHandler):
    def _detect_keys(self):
        while self.checking_for_input:
            if ms.kbhit():
                if self.input_queue.full():
                    self.input_queue.get(False)
                    self.input_queue.get(False)
                self.input_queue.put(self.filter_key(getch()), False)
            #time.sleep(0.03)

if __name__ == "__main__":
    ih = InputHandler()
    ih.start()
    while True:
        if (char := ih.get()) != None:
            print(repr(char))
            if char == b'~':
                break
        time.sleep(0.1)
    ih.stop()
        