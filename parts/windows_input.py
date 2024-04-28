import msvcrt as ms
import sys
import threading as th
from queue import Queue
import time
from parts.input_handler import BaseInputHandler

class InputHandler(BaseInputHandler):
    def _detect_keys(self):
        while self.checking_for_input:
            if ms.kbhit():
                if self.input_queue.full():
                    self.input_queue.get(False)
                    self.input_queue.get(False)
                self.input_queue.put(self.filter_key(ms.getch()), False)
            #time.sleep(0.03)